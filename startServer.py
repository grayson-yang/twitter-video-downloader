#!/usr/bin/env python

# Python 3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys


class CORSRequestHandler(SimpleHTTPRequestHandler):
	def end_headers(self):
		self.send_header('Access-Control-Allow-Origin', '*')
		SimpleHTTPRequestHandler.end_headers(self)


def StartServer():
	port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
	sever = HTTPServer(("", port), CORSRequestHandler)
	sever.serve_forever()

	
if __name__ == '__main__':
	StartServer()