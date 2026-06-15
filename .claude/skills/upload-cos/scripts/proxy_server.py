#!/usr/bin/env python3
"""Lightweight reverse proxy that serves COS files with inline Content-Disposition."""

import os, sys, yaml, urllib3, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

with open(os.path.expanduser('~/.cos.yaml')) as f:
    cfg = yaml.safe_load(f)['base']

BUCKET = cfg.get('webpages_bucket', f"webpages-{cfg['bucket'].split('-')[-1]}")
REGION = cfg['region']
COS_BASE = f"https://{BUCKET}.cos.{REGION}.myqcloud.com"
CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.mp4': 'video/mp4',
    '.mp3': 'audio/mpeg',
}

http_pool = urllib3.PoolManager()

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == '/' or path == '/favicon.ico':
            self.send_error(404)
            return
        
        # Fetch from COS
        url = f"{COS_BASE}{path}"
        try:
            resp = http_pool.request('GET', url)
            if resp.status != 200:
                self.send_error(resp.status)
                return
            
            # Determine content type
            ext = os.path.splitext(path.split('/')[-1])[1].lower()
            content_type = CONTENT_TYPES.get(ext, 'application/octet-stream')
            
            # Serve with Content-Disposition: inline (override force-download)
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', 'inline')
            self.send_header('Content-Length', len(resp.data))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(resp.data)
        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"Proxy serving on port {port}")
    print(f"Origin: {COS_BASE}")
    server.serve_forever()
