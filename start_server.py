import subprocess
import sys
import os

def check_python():
    """Check if Python is available"""
    try:
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True)
        print(f"✅ Python found: {result.stdout.strip()}")
        return True
    except:
        print("❌ Python not found")
        return False

def install_flask():
    """Install required packages"""
    packages = ['flask', 'flask-cors', 'requests']
    for package in packages:
        try:
            print(f"📦 Installing {package}...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")

def start_server():
    """Start the Flask server"""
    try:
        print("🚀 Starting Am I Wrong? server...")
        print("📍 Server will run on: http://127.0.0.1:5000")
        print("📱 Open this URL in your browser")
        print("⚠️  Press Ctrl+C to stop the server")
        print()
        
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the server
        subprocess.run([sys.executable, 'app.py'])
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🔧 Am I Wrong? Server Setup")
    print("=" * 40)
    
    # Check Python
    if not check_python():
        print("Please install Python first")
        return
    
    # Install packages
    print("\n📦 Installing required packages...")
    install_flask()
    
    # Start server
    print("\n🚀 Starting server...")
    start_server()

if __name__ == '__main__':
    main()
