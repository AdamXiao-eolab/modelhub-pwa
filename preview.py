"""
ModelHub local preview server
"""

import http.server
import socketserver
import os
import sys

PORT = 5000
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)
    def log_message(self, format, *args):
        print(f"[Preview] {args[0]} {args[1]} {args[2]}")

print("=" * 50)
print("ModelHub Preview Server")
print("=" * 50)
print()
print("Static pages:")
print(f"  http://localhost:{PORT}/index.html")
print(f"  http://localhost:{PORT}/pricing.html")
print(f"  http://localhost:{PORT}/docs.html")
print(f"  http://localhost:{PORT}/privacy.html")
print()
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        sys.exit(0)
