from compression.zstd import zstd_version
import socket

HOST = "smis.events"
PORT = 443

#pass task
def download_page(host, port):
    """Open a raw TCP socket, send an HTTP/1.0 GET request, and return the full response as a string."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    # HTTP 1.0 request
    request = f"GET /.htaccess HTTP/1.0\r\nHost: {host}\r\n\r\n"
    s.sendall(request.encode())

    chunks = []
    while True:
        data = s.recv(4096)
        if not data:
            break
        chunks.append(data)

    s.close()
    return b"".join(chunks).decode("utf-8", errors="replace")


# credit task
def parse_response(raw):
    """
    Split raw HTTP response into:
      - status line  (e.g. 'HTTP/1.0 200 OK')
      - headers dict (e.g. {'Content-Type': 'text/html', ...})
      - body         (the actual HTML)
    Returns (status_line, headers_dict, body)
    """
    if "\r\n\r\n" in raw:
        header_section, body = raw.split("\r\n\r\n", 1)
        header_lines = header_section.split("\r\n")
    else:
        header_section, body = raw.split("\n\n", 1)
        header_lines = header_section.split("\n")

    status_line = header_lines[0]          # e.g. "HTTP/1.0 301 Moved Permanently"
    raw_headers  = header_lines[1:]        # remaining lines are header fields

    headers = {}
    for line in raw_headers:
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip()] = value.strip()

    return status_line, headers, body


def display_results(status_line, headers, body):
   
    parts = status_line.split(" ", 2)          
    response_code = int(parts[1])
    response_msg  = parts[2] if len(parts) > 2 else ""

    print("=" * 60)
    print("  HTTP RESPONSE STATUS")
    print("=" * 60)
    print(f"  Version  : {parts[0]}")
    print(f"  Code     : {response_code}")
    print(f"  Message  : {response_msg}")

    
    print("\n" + "=" * 60)
    print("  RESPONSE HEADERS")
    print("=" * 60)
    for key, value in headers.items():
        print(f"  {key:<30} : {value}")

    print("\n" + "=" * 60)
    if response_code == 200:
        print("  HTML CONTENT")
        print("=" * 60)
        print(body)
    else:
        print("  ERROR")
        print("=" * 60)
        print(f"  HTTP Error {response_code}: {response_msg}")
        print("  The server did not return a 200 OK response.")
        print(f"  (Full body hidden – response code is {response_code})")
    print("=" * 60)

# main
if __name__ == "__main__":
    print(f"Connecting to {HOST}:{PORT} using HTTP/1.0 ...")
    raw_response = download_page(HOST, PORT)

    print("Download complete. Parsing response ...\n")
    status_line, headers, body = parse_response(raw_response)

    display_results(status_line, headers, body)