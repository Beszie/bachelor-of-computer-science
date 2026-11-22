import socket
import threading

# Configuration
HOST = '0.0.0.0'
PORT = 12345
BUFFER_SIZE = 1024
HEADER = "TNE20003:"

# --- MODIFICATION 1: Message Framing Delimiter ---
# UDP delivers messages as distinct, self-contained chunks, so no framing is needed.
# TCP is stream-based: multiple messages can arrive merged together, or a single
# message can be split across multiple reads. To solve this, we add a newline '\n'
# as a message terminator. The receiver buffers incoming bytes and only processes
# a message once it sees the '\n', ensuring we always parse exactly one complete message.
DELIMITER = "\n"


def parse_client_message(data):
    """
    Check if the received data matches the protocol format: TNE20003:<message>
    Returns the <message> part if valid, or None if invalid.
    (Logic unchanged from the UDP version)
    """
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        return None  # Not valid ASCII - reject

    if not text.startswith(HEADER):
        return None  # Header mismatch - reject

    message = text[len(HEADER):]

    if len(message) < 1:
        return None  # Empty message - reject

    return message


def build_ack(message):
    """Build a valid acknowledgement response: TNE20003:A:<message>"""
    # MODIFICATION 2: Append the delimiter '\n' so the client can detect the end
    # of this response in the TCP stream (mirrors the framing added on the send side).
    return f"TNE20003:A:{message}{DELIMITER}"


def build_error(error_message):
    """Build an error response: TNE20003:E:<error_message>"""
    # MODIFICATION 2 (same as above): Append delimiter to every outgoing response.
    return f"TNE20003:E:{error_message}{DELIMITER}"


def handle_client(conn, addr):
    """
    Handle a single connected client in its own thread.

    MODIFICATION 3: Per-client threaded handler.
    The UDP server used a single blocking recvfrom() loop because UDP is connectionless
    — each packet already carries the sender's address. TCP is connection-oriented:
    once a client connects, we get a dedicated socket (conn) for that client.
    We spin up a thread per client so the server can serve multiple clients
    simultaneously without one client blocking another.
    """
    print(f"\n[SERVER] New connection from {addr}")

    # MODIFICATION 4: Persistent receive buffer per client connection.
    # UDP: each recvfrom() returns exactly one full datagram — no buffering needed.
    # TCP: recv() can return any number of bytes. We accumulate bytes in `buffer`
    # and only extract + process a message once we find the '\n' delimiter.
    buffer = ""

    try:
        while True:
            # Receive a chunk of bytes from the TCP stream
            chunk = conn.recv(BUFFER_SIZE)

            if not chunk:
                # An empty recv() means the client has closed the connection
                print(f"[SERVER] Client {addr} disconnected.")
                break

            # Decode and append to our persistent buffer
            # MODIFICATION 5: Decode here (not inside parse) so we can scan for '\n'
            try:
                buffer += chunk.decode('ascii')
            except UnicodeDecodeError:
                # If we receive non-ASCII data we cannot decode, send an error and
                # clear the buffer to avoid corrupting subsequent messages
                response = build_error("Non-ASCII data received.")
                conn.sendall(response.encode('ascii'))
                buffer = ""
                continue

            # MODIFICATION 6: Message extraction loop.
            # A single recv() might deliver more than one complete message (e.g.
            # "TNE20003:Hello\nTNE20003:World\n"). We loop, pulling out one message
            # per iteration, until no more complete messages remain in the buffer.
            while DELIMITER in buffer:
                # Split off exactly one complete message at the first '\n'
                message_raw, buffer = buffer.split(DELIMITER, 1)

                print(f"[SERVER] Received message: '{message_raw}'")

                # Strip the trailing '\n' that was part of the delimiter before
                # passing to parse (parse_client_message is unchanged from UDP version)
                parsed = parse_client_message(message_raw.encode('ascii'))

                if parsed is not None:
                    response = build_ack(parsed)
                    print(f"[SERVER] Valid message. Sending ACK: {response.strip()}")
                else:
                    response = build_error("Invalid protocol format. Expected TNE20003:<message>")
                    print(f"[SERVER] Invalid message. Sending ERROR: {response.strip()}")

                # MODIFICATION 7: Use sendall() instead of sendto().
                # UDP uses sendto() because it is connectionless (must specify destination).
                # TCP uses sendall() on the connected socket (conn); the destination is
                # already established by the connection. sendall() guarantees all bytes
                # are sent even if the OS only sends part of them in one call.
                conn.sendall(response.encode('ascii'))

    finally:
        conn.close()
        print(f"[SERVER] Connection with {addr} closed.")


def run_server():
    # MODIFICATION 8: Switch from SOCK_DGRAM (UDP) to SOCK_STREAM (TCP).
    # SOCK_DGRAM = UDP (datagram-based, connectionless)
    # SOCK_STREAM = TCP (stream-based, connection-oriented)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # MODIFICATION 9: SO_REUSEADDR allows the server to reuse the port immediately
    # after restart, avoiding "Address already in use" errors during development.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    # MODIFICATION 10: listen() is required for TCP (not needed for UDP).
    # It puts the socket into passive listening mode and sets the backlog queue
    # (max number of pending connections before new ones are refused).
    server_socket.listen(5)
    print(f"[SERVER] TCP server listening on {HOST}:{PORT} ...")

    try:
        while True:
            # MODIFICATION 11: accept() blocks until a client connects, then returns
            # a NEW dedicated socket (conn) for that client plus their address.
            # UDP has no concept of "accepting" — datagrams just arrive.
            conn, addr = server_socket.accept()

            # Spawn a thread to handle this client so the main loop can immediately
            # accept the next connection (MODIFICATION 3 continued).
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")

    finally:
        server_socket.close()


if __name__ == "__main__":
    run_server()