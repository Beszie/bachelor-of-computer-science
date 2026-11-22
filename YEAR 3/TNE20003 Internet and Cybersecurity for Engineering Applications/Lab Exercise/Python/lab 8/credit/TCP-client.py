import socket

# Configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024
HEADER = "TNE20003:"

# --- MODIFICATION 1: Message Framing Delimiter ---
# UDP guarantees each send/recv is one complete message. TCP does not — it is a
# byte stream and multiple messages can be merged or split across reads.
# We use '\n' as a message terminator. Every outgoing message ends with '\n'
# so the server knows where this message ends. We also look for '\n' in the
# server's reply to know we have received a complete response.
DELIMITER = "\n"


def build_message(text):
    """
    Build a properly formatted client message: TNE20003:<message>
    MODIFICATION 2: Append the '\n' delimiter to mark the end of the message
    in the TCP stream. The server will buffer bytes until it sees '\n' and
    then process that chunk as one complete message.
    (The UDP version did NOT append '\n' — UDP framing is implicit.)
    """
    return f"TNE20003:{text}{DELIMITER}"


def parse_server_reply(text):
    """
    Parse the server's reply.
    Valid formats:
      TNE20003:A:<message>  -> Acknowledgement
      TNE20003:E:<error>    -> Error

    MODIFICATION 3: Parameter changed from raw bytes (data) to a decoded string
    (text). In the UDP version, this function received raw bytes and decoded them
    itself. In the TCP version, decoding and delimiter-splitting happen in
    receive_response() before calling here, so we accept an already-decoded string.
    """
    print(f"[CLIENT] Raw reply: {text}")

    if not text.startswith(HEADER):
        print("[CLIENT] Reply has wrong header — protocol mismatch!")
        return

    rest = text[len(HEADER):]

    if rest.startswith("A:"):
        echoed_message = rest[2:]
        print(f"[CLIENT] ACK received. Server echoed message: '{echoed_message}'")

    elif rest.startswith("E:"):
        error_message = rest[2:]
        print(f"[CLIENT] ERROR received from server: '{error_message}'")

    else:
        print(f"[CLIENT] Unknown reply type: {rest}")


def receive_response(sock):
    """
    MODIFICATION 4: New helper function for TCP stream-aware receiving.

    UDP: A single recvfrom() always returns exactly one complete server reply.
    TCP: recv() may return partial data. We must buffer bytes and keep reading
         until we find the '\n' delimiter, which signals the end of one full reply.

    This function blocks until a complete '\n'-terminated message is assembled,
    then strips the delimiter and returns the clean message string.
    """
    buffer = ""
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            # Server closed the connection unexpectedly
            raise ConnectionError("[CLIENT] Server closed the connection.")

        buffer += chunk.decode('ascii')

        # Check if we now have a complete message (delimiter found)
        if DELIMITER in buffer:
            # Extract the first complete message; discard anything after '\n'
            # (in this simple client we send one message and wait for one reply,
            # so there should be nothing after the delimiter)
            message, _ = buffer.split(DELIMITER, 1)
            return message


def send_message(sock, message_text):
    """
    Send one formatted message to the server and wait for a reply.

    MODIFICATION 5: Replace sendto()/recvfrom() with send()/receive_response().
    - UDP sendto() requires specifying the destination address each call because
      UDP is connectionless. TCP's send() uses the already-established connection.
    - UDP recvfrom() returns a full datagram in one call. TCP requires the buffered
      receive loop in receive_response() to handle stream fragmentation.
    """
    message = build_message(message_text)
    # Strip delimiter for display so the log is clean
    print(f"\n[CLIENT] Sending: {message.strip()}")

    # MODIFICATION 6: send() instead of sendto() — TCP connection already knows
    # the destination; no need to pass (SERVER_HOST, SERVER_PORT) again.
    sock.send(message.encode('ascii'))

    # Wait for a complete '\n'-terminated response from the server
    reply_text = receive_response(sock)
    parse_server_reply(reply_text)


def run_client():
    # MODIFICATION 7: Switch from SOCK_DGRAM (UDP) to SOCK_STREAM (TCP).
    # SOCK_DGRAM = UDP (connectionless, no handshake)
    # SOCK_STREAM = TCP (connection-oriented, requires connect() before sending)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5)

    try:
        # MODIFICATION 8: connect() is required for TCP — not needed in UDP.
        # This performs the TCP three-way handshake with the server.
        # Once connected, all send/recv calls on this socket talk to the server.
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"[CLIENT] Connected to {SERVER_HOST}:{SERVER_PORT}")

        # --- Message 1: A normal valid message ---
        send_message(client_socket, "Hello from the client!")

        # --- Message 2: Another valid message ---
        send_message(client_socket, "Testing TCP protocol")

        # --- Message 3 (bonus): Send a bad/invalid message to test error handling ---
        # Manually craft a message that violates the protocol header so the server
        # responds with an error. We still append '\n' so the server can frame it.
        bad_message = f"BADHEADER:this should trigger an error{DELIMITER}"
        print(f"\n[CLIENT] Sending invalid message: {bad_message.strip()}")
        client_socket.send(bad_message.encode('ascii'))
        reply_text = receive_response(client_socket)
        parse_server_reply(reply_text)

    except socket.timeout:
        print("[CLIENT] Timed out — no reply from server.")

    except ConnectionError as e:
        print(e)

    finally:
        # MODIFICATION 9: For TCP, closing the socket sends a FIN to the server,
        # gracefully signalling the end of the connection (TCP four-way teardown).
        # UDP close() simply releases the local port with no network signalling.
        client_socket.close()
        print("\n[CLIENT] Socket closed.")


if __name__ == "__main__":
    run_client()