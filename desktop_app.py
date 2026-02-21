#!/usr/bin/env python3
"""
Theophile POS Desktop Application Entry Point
"""

import os
import sys
import webbrowser
import threading
import time
import socket
from app import app

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    """Main entry point"""
    print("=" * 50)
    print("  Theophile POS Desktop Application")
    print("=" * 50)
    print("\nStarting server...")
    
    # Check if port is available
    if not is_port_available(5000):
        print("Port 5000 is already in use!")
        print("Please close other applications using this port.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        # Run the Flask app
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()