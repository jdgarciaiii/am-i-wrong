#!/usr/bin/env python3
"""
Secure runner for the Am I Wrong? app
"""
import os
import sys
from secure_app import app

def main():
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    
    # Generate secure secret key if not set
    if not os.getenv('SECRET_KEY'):
        import secrets
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
    
    print("🔒 Starting secure Am I Wrong? app...")
    print("📍 Running on https://127.0.0.1:5000")
    print("🛡️  Security features enabled:")
    print("   - HTTPS/SSL encryption")
    print("   - Input validation & sanitization") 
    print("   - Rate limiting")
    print("   - Security headers")
    print("   - CORS protection")
    print("\n📱 Open https://127.0.0.1:5000 in your browser")
    print("⚠️  Accept the self-signed certificate in your browser")
    
    try:
        app.run(
            debug=False,
            host='127.0.0.1',
            port=5000,
            ssl_context='adhoc'  # Self-signed certificate for HTTPS
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
