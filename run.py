#!/usr/bin/env python
"""
Theophile POS - Desktop Launcher
This file starts the Flask server and opens the browser
"""

import os
import sys
import threading
import time
import socket
import webbrowser
import subprocess
from app import app

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except socket.error:
            return False

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:5000')

def create_database():
    """Create database if it doesn't exist"""
    try:
        import pymysql
        from config import Config
        
        # Connect to MySQL
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Database check complete")
    except Exception as e:
        print(f"! Database warning: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("  THEOPHILE POS - Desktop Application")
    print("=" * 60)
    print()
    
    # Check if port is available
    if not is_port_available(5000):
        print("❌ Port 5000 is already in use!")
        print("   Please close other applications using this port.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Check database
    print("✓ Checking database...")
    create_database()
    
    # Start browser in background
    print("✓ Starting browser...")
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app
    print("✓ Starting server...")
    print("\n" + "=" * 60)
    print("  Server running at: http://127.0.0.1:5000")
    print("  Close this window to stop the application")
    print("=" * 60 + "\n")
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()