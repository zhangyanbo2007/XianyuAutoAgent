#!/usr/bin/env python3
"""Persistent reverse proxy for COS HTML files.
Strips force-download headers so browsers render HTML inline."""

import os, sys, signal, yaml, urllib3
from http.server import HTTPServer, BaseHTTPRequestHandler

CONFIG_PATH = os.path.expanduser('~/.cos.yaml')
PORT_FILE = '/tmp/cos_html_proxy_port'

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)['base']

BUCKET = cfg.get('webpages_bucket', f"webpages-{cfg['bucket'].split('-')[-1]}")
REGION = cfg['region']
COS_BASE = f"https://{BUCKET}.cos.{REGION}.myqcloud.com"

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8',
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf', '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript', '.json': 'application/json',
    '.mp4': 'video/mp4', '.mp3': 'audio/mpeg',
    '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
}

http_pool = urllib3.PoolManager()

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == '/' or path == '/favicon.ico':
            self.send_error(404)
            return

        url = f"{COS_BASE}{path}"
        try:
            resp = http_pool.request('GET', url, timeout=30)
            if resp.status != 200:
                self.send_error(resp.status)
                return

            ext = os.path.splitext(path.split('/')[-1].split('?')[0])[1].lower()
            content_type = CONTENT_TYPES.get(ext, 'application/octet-stream')

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', 'inline')
            self.send_header('Content-Length', str(len(resp.data)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(resp.data)
        except Exception as e:
            self.send_error(502, str(e))

    def log_message(self, format, *args):
        pass

def shutdown(signum, frame):
    server.shutdown()

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
server = HTTPServer(('0.0.0.0', port), ProxyHandler)

# Write port to file so upload script can find it
with open(PORT_FILE, 'w') as f:
    f.write(str(port))

print(f"COS HTML proxy running on port {port}")
print(f"Origin: {COS_BASE}")
server.serve_forever()
