#!/usr/bin/env python3
"""Serve the Smoly prototypes with caching switched off.

Plain `python3 -m http.server` lets the browser hold on to tokens.css,
components.css and app.js, so edits appear to do nothing until a hard reload.
Everything here is sent with no-store, which is what you want while iterating.

    python3 serve.py                 # http://127.0.0.1:8787/  — this machine only
    python3 serve.py --lan           # also reachable from your phone on the same wi-fi
    python3 serve.py --lan 9000      # ...on a different port

Only this folder is served, never the parent — the project folder around it
holds client documents that have no business on the network.
"""

import functools
import http.server
import os
import socket
import socketserver
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

args = [a for a in sys.argv[1:]]
lan = "--lan" in args
ports = [a for a in args if a.isdigit()]
PORT = int(ports[0]) if ports else 8787
HOST = "0.0.0.0" if lan else "127.0.0.1"


def lan_ip():
    """Best guess at this machine's address on the local network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 1))   # TEST-NET-1; no packets are actually sent
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_header(self, keyword, value):
        if keyword == "Last-Modified":   # so conditional requests cannot 304
            return
        super().send_header(keyword, value)


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    handler = functools.partial(NoCacheHandler, directory=HERE)
    with ReusableServer((HOST, PORT), handler) as httpd:
        print(f"Serving {HERE}")
        print(f"  this machine → http://127.0.0.1:{PORT}/")
        if lan:
            print(f"  same wi-fi   → http://{lan_ip()}:{PORT}/")
            print("  (anyone on this network can reach it while it runs; ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
