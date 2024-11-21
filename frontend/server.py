from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import getpass

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        self.wfile.write(b"<h1>Hello From Rosie</h1>") # TODO: put Rosé here

host = socket.gethostname()
port = 8001

if __name__ == "__main__":
    server = HTTPServer((host, port), SimpleHTTPRequestHandler)
    print(f"Serving on http://{host}:{port}")
    print(f"Run this on your local machine:")
    print(f"ssh -L 8001:{host}:8001 {getpass.getuser()}@dh-mgmt2.hpc.msoe.edu")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
