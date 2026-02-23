#!/usr/bin/env python3
"""
Simple OpenShorts Packaging Script
Alternative approach with better Gradio handling
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    paths_to_clean = ['build', 'dist', '*.spec', '__pycache__']
    for path in paths_to_clean:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"🧹 Cleaned {path}/")
            else:
                os.remove(path)
                print(f"🧹 Cleaned {path}")

def install_dependencies():
    """Install required packaging dependencies"""
    packages = ['pyinstaller', 'auto-py-to-exe']
    for package in packages:
        print(f"📦 Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      check=True, capture_output=True)

def build_simple():
    """Simple PyInstaller build with minimal options"""
    print("🔨 Building with simple PyInstaller configuration...")
    
    cmd = [
        'pyinstaller',
        '--onedir',  # Use onedir instead of onefile for Gradio
        '--name=OpenShorts',
        '--console',
        '--noconfirm',
        '--clean',
        '--collect-data=gradio',
        '--collect-data=safehttpx', 
        '--collect-data=faster_whisper',
        '--hidden-import=gradio',
        '--hidden-import=gradio.components',
        '--hidden-import=gradio.themes',
        '--hidden-import=safehttpx',
        '--hidden-import=faster_whisper',
        '--hidden-import=cv2',
        '--hidden-import=PIL',
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        'openshorts.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Simple build successful!")
        return True
    else:
        print("❌ Simple build failed:")
        print(result.stderr)
        return False

def create_launcher_script():
    """Create a simple launcher script for the onedir build"""
    launcher_content = '''#!/bin/bash
# OpenShorts Launcher Script

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Run OpenShorts
./OpenShorts/OpenShorts

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "OpenShorts encountered an error. Press any key to exit..."
    read -n 1
fi
'''
    
    with open('dist/launch_openshorts.sh', 'w') as f:
        f.write(launcher_content.strip())
    os.chmod('dist/launch_openshorts.sh', 0o755)
    print("✅ Created launcher script")

def main():
    print("🎬 OpenShorts Simple Packaging")
    print("===============================")
    
    if not os.path.exists('openshorts.py'):
        print("❌ Error: openshorts.py not found")
        sys.exit(1)
    
    try:
        # Clean previous builds
        clean_build()
        
        # Install dependencies
        install_dependencies()
        
        # Try simple build first
        if build_simple():
            create_launcher_script()
            print("\\n🎉 Packaging complete!")
            print("📁 Files created:")
            print("   - dist/OpenShorts/ (application folder)")
            print("   - dist/launch_openshorts.sh (launcher script)")
            print("\\n📋 To distribute:")
            print("   1. Zip the entire dist/ folder")
            print("   2. Users extract and run launch_openshorts.sh")
            print("   3. Or run dist/OpenShorts/OpenShorts directly")
        else:
            print("\\n❌ Build failed. Try running from virtual environment:")
            print("  python -m venv venv")
            print("  source venv/bin/activate")  
            print("  pip install -r requirements.txt")
            print("  python simple_build.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()