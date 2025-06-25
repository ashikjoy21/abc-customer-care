#!/usr/bin/env python3
import os
import http.server
import socketserver
import threading
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for HTTP health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health' or self.path == '/':
            # Return 200 OK for health checks
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "ok"})
            self.wfile.write(response.encode('utf-8'))
        else:
            # Return 404 for other paths
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"error": "Not found"})
            self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.client_address[0], format % args)

def start_http_server(port=8080):
    """Start the HTTP server in a separate thread"""
    handler = HealthCheckHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    logger.info(f"Starting HTTP server on port {port}")
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return httpd

if __name__ == "__main__":
    # For testing the HTTP server directly
    port = int(os.environ.get("PORT", 8080))
    httpd = start_http_server(port)
    
    try:
        logger.info(f"Server started at port {port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.shutdown() 