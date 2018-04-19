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
import time

try:
    import coloredlogs
    import logging
    coloredlogs.install()
except ImportError:
    pass

hostName = ""
hostPort = 8080


class MyServer(BaseHTTPRequestHandler):

    # def handle_one_request(self):
    #     super().handle_one_request()
    #     logging.info(f"{self.command} {self.client_address}: {self.path}")

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET is for clients geting the predi
    def do_GET(self):
        self.send_response(204)
        self.end_headers()
        self.wfile.write(b'')

    # POST is for submitting data.
    def do_POST(self):

        if "Content-Length" in self.headers:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            if post_data:
                logging.info("Received:", post_data)

        self.send_response(204)
        self.end_headers()
        self.wfile.write(b'')

    def log_message(self, format, *args):
        logging.info(format, *args)

    def log_error(selr, format, *args):
        logging.error(format, *args)


myServer = HTTPServer((hostName, hostPort), MyServer)
logging.info(f"Server Starts {hostName}, port: {hostPort}")

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
logging.info(f"Server Stops {hostName}, port: {hostPort}")
