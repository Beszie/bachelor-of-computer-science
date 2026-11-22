import socket

# Configuration 
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 12345
BUFFER_SIZE = 1024
HEADER = "TNE20003:"

def build_message(text):
    """Build a properly formatted client message: TNE20003:<message>"""
    return f"TNE20003:{text}"


def parse_server_reply(data):
    """
    Parse the server's reply.
    Valid formats:
      TNE20003:A:<message>   -> Acknowledgement
      TNE20003:E:<error>     -> Error
    """
    # The server expexted to always reply with ASCII text per the protocol
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        print("[CLIENT] Could not decode server reply.")
        return

    print(f"[CLIENT] Raw reply: {text}")
    # Check that the reply starts with the correct protocol header
    if not text.startswith(HEADER):
        print("[CLIENT] Reply has wrong header — protocol mismatch!")
        return

    rest = text[len(HEADER):] 

    # Check message type
    if rest.startswith("A:"):
        echoed_message = rest[2:] 
        print(f"[CLIENT] ACK received. Server echoed message: '{echoed_message}'")

    elif rest.startswith("E:"):
        error_message = rest[2:]  
        print(f"[CLIENT] ERROR received from server: '{error_message}'")

    else:
        print(f"[CLIENT] Unknown reply type: {rest}")
        # The reply header was correct but the message type is unrecognised


def send_message(sock, message_text):
    """Send one formatted message to the server and wait for a reply."""
    message = build_message(message_text)
    print(f"\n[CLIENT] Sending: {message}")

    sock.sendto(message.encode('ascii'), (SERVER_HOST, SERVER_PORT)) # Send as ASCII bytes

    data, server_address = sock.recvfrom(BUFFER_SIZE) # Wait for the server's reply
    parse_server_reply(data)


def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket
    client_socket.settimeout(5) # Set a timeout so we don't wait forever if server doesn't reply

    try:
        # --- Message 1: A normal valid message ---
        send_message(client_socket, "Hello from the client!")

        # --- Message 2: Another valid message ---
        send_message(client_socket, "Testing UDP protocol")

        # --- Message 3 (bonus): Send a bad/invalid message to test error handling ---
        # because we manually send something that doesn't follow the protocol
        bad_message = "BADHEADER:this should trigger an error"
        print(f"\n[CLIENT] Sending invalid message: {bad_message}")
        client_socket.sendto(bad_message.encode('ascii'), (SERVER_HOST, SERVER_PORT))
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        parse_server_reply(data)

    except socket.timeout:
        print("[CLIENT] Timed out — no reply from server.")

    finally:
        client_socket.close()
        print("\n[CLIENT] Socket closed.")


if __name__ == "__main__":
    run_client()