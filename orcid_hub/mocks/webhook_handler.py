#!/usr/bin/env python
"""
Very simple HTTP server in python.

Usage::
    ./dummy-web-server.py [<port>]

Send a GET request::
    curl http://localhost

Send a HEAD request::
    curl -I http://localhost

Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost

"""
from http.server import BaseHTTPRequestHandler, HTTPServer

import logging
try:
    import coloredlogs
    coloredlogs.install()
except ImportError:
    pass

host_name = ""
host_port = 8080


class UpdateHandler(BaseHTTPRequestHandler):
    """Webhook update even handler."""

    def do_GET(self):  # noqa: N802
        """Handle GET request."""
        self.send_response(204)
        self.end_headers()
        self.wfile.write(b'')

    def do_POST(self):  # noqa: N802
        """Handle POST request."""
        if "Content-Length" in self.headers:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            if post_data:
                logging.info(f"Received: {post_data.decode()}")
        self.log_message("*** Headers:\n%s", self.headers)
        self.log_message("Source: %s", self.headers.get("X-Forwarded-For"))

        self.send_response(204)
        self.end_headers()
        self.wfile.write(b'')

    def log_message(self, format, *args):
        """Log a message."""
        logging.info(format, *args)

    def log_error(self, format, *args):
        """Log an error message."""
        logging.error(format, *args)


server = HTTPServer((host_name, host_port), UpdateHandler)
logging.info(f"Server Starts {host_name}, port: {host_port}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass

server.server_close()
logging.info(f"Server Stops {host_name}, port: {host_port}")
