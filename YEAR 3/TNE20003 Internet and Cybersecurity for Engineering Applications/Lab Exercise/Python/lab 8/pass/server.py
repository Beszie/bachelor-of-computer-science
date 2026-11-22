import socket
# Configuration
HOST = '0.0.0.0'   
PORT = 12345        
BUFFER_SIZE = 1024  
HEADER = "TNE20003:"

def parse_client_message(data):
    """
    Check if the received data matches the protocol format: TNE20003:<message>
    Returns the <message> part if valid, or None if invalid.
    """
    # If the data contains non-ASCII bytes, decoding will fail and we return None.
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        return None # Not valid ASCII - reject the packet
    
    # If the header is missing or wrong, this is not a valid protocol message.
    if not text.startswith(HEADER):
        return None # Header mismatch - reject the packet

    message = text[len(HEADER):] # extract the <message> part

    # To make sure the message is not empty
    if len(message) < 1: # The protocol requires <message> to be at least 1 character long
        return None
    return message


def build_ack(message):
    """Build a valid acknowledgement response: TNE20003:A:<message>"""
    return f"TNE20003:A:{message}"


def build_error(error_message):
    """Build an error response: TNE20003:E:<error_message>"""
    return f"TNE20003:E:{error_message}"


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket

    server_socket.bind((HOST, PORT))
    print(f"[SERVER] Listening on {HOST}:{PORT} ...")

    while True:
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)
        print(f"\n[SERVER] Received packet from {client_address}")
        print(f"[SERVER] Raw data: {data}")

        message = parse_client_message(data)

        if message is not None:
            response = build_ack(message)
            print(f"[SERVER] Valid message. Sending ACK: {response}")
        else:
            # Invalid message (send error)
            response = build_error("Invalid protocol format. Expected TNE20003:<message>")
            print(f"[SERVER] Invalid message. Sending ERROR: {response}")

        server_socket.sendto(response.encode('ascii'), client_address)


if __name__ == "__main__":
    run_server()