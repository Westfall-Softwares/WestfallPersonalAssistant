#!/usr/bin/env python3
"""
Simple test server for the new backend structure.
Can run with minimal dependencies for testing.
"""

import argparse
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class SimpleBackendHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for testing the backend structure."""
    
    def log_message(self, format, *args):
        """Log messages with timestamp."""
        print(f"[{self.log_date_time_string()}] {format % args}")
    
    def send_json_response(self, data, status=200):
        """Send a JSON response."""
        response_data = json.dumps(data, indent=2)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_data.encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            self.send_json_response({
                "name": "Westfall Personal Assistant Backend",
                "version": "1.0.0-simple",
                "status": "running",
                "message": "Simple test server - FastAPI not loaded"
            })
        
        elif path == '/api/health':
            import time
            import os
            self.send_json_response({
                "status": "ok",
                "version": "1.0.0-simple",
                "timestamp": "2024-01-01T00:00:00Z",
                "pid": os.getpid(),
                "message": "Simple health check"
            })
        
        elif path == '/shutdown':
            self.send_json_response({"message": "Shutdown request received"})
            # Note: actual shutdown would need to be handled by the server
        
        else:
            self.send_json_response({
                "error": "Not Found",
                "path": path,
                "available_endpoints": ["/", "/api/health", "/shutdown"]
            }, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/shutdown':
            self.send_json_response({"message": "Shutdown initiated"})
            print("Shutdown request received")
        else:
            self.send_json_response({
                "error": "Method not implemented",
                "path": path,
                "method": "POST"
            }, 501)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_simple_server(host='127.0.0.1', port=8756):
    """Run the simple test server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, SimpleBackendHandler)
    
    print(f"Starting simple backend server on http://{host}:{port}")
    print("Available endpoints:")
    print(f"  - http://{host}:{port}/")
    print(f"  - http://{host}:{port}/api/health")
    print(f"  - http://{host}:{port}/shutdown (POST)")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        httpd.server_close()
        print("Server stopped")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple Westfall Backend Test Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8756, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Check if FastAPI is available before trying to import
    try:
        import fastapi
        import uvicorn
        fastapi_available = True
    except ImportError:
        fastapi_available = False
    
    if fastapi_available:
        try:
            print("FastAPI available, attempting to load full backend...")
            # Add the backend directory to path
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent
            sys.path.insert(0, str(backend_path))
            
            # Import without executing (avoid sys.exit in app.py)
            import importlib.util
            app_path = backend_path / "westfall_backend" / "app.py"
            spec = importlib.util.spec_from_file_location("app", app_path)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)
            
            print("Using FastAPI backend...")
            app_module.main()
            
        except Exception as e:
            print(f"Error starting FastAPI server ({e}), falling back to simple server...")
            run_simple_server(args.host, args.port)
    else:
        print("FastAPI not available, using simple test server...")
        run_simple_server(args.host, args.port)

if __name__ == "__main__":
    main()