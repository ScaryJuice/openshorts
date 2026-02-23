#!/usr/bin/env python3
"""
Build OpenShorts Python Package
Creates a wheel that users can install with pip
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    paths_to_clean = ['build', 'dist', '*.egg-info', '__pycache__']
    for pattern in paths_to_clean:
        if '*' in pattern:
            # Handle glob patterns
            import glob
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        elif os.path.exists(pattern):
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
            else:
                os.remove(pattern)
    print("🧹 Cleaned build artifacts")

def install_build_deps():
    """Install build dependencies"""
    packages = ['build', 'wheel', 'twine']
    for package in packages:
        print(f"📦 Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      check=True, capture_output=True)

def build_wheel():
    """Build the wheel package"""
    print("🔨 Building Python wheel...")
    
    result = subprocess.run([
        sys.executable, "-m", "build", "--wheel"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Wheel build successful!")
        # List the created files
        dist_files = list(Path("dist").glob("*.whl"))
        for file in dist_files:
            print(f"📦 Created: {file}")
        return True
    else:
        print("❌ Wheel build failed:")
        print(result.stderr)
        return False

def create_install_script():
    """Create installation script for end users"""
    script_content = '''#!/bin/bash
# OpenShorts Installation Script

echo "🎬 OpenShorts Installer"
echo "======================"

# Check Python version
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.12+ first."
    exit 1
fi

# Check FFmpeg
ffmpeg -version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  FFmpeg not found. Installing FFmpeg is recommended:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    echo ""
fi

# Install OpenShorts
echo "📦 Installing OpenShorts..."
pip3 install openshorts*.whl

echo "✅ Installation complete!"
echo ""
echo "🚀 To run OpenShorts:"
echo "   openshorts"
echo ""
echo "🌐 Then open your browser to: http://127.0.0.1:7875"
'''

    with open('dist/install.sh', 'w') as f:
        f.write(script_content.strip())
    os.chmod('dist/install.sh', 0o755)
    print("✅ Created install.sh")

def create_windows_installer():
    """Create Windows installation batch file"""
    bat_content = '''@echo off
echo 🎬 OpenShorts Installer
echo ======================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.12+ first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ FFmpeg not found. Installing FFmpeg is recommended:
    echo    winget install ffmpeg
    echo    Or download from: https://ffmpeg.org/download.html#build-windows
    echo.
)

REM Install OpenShorts
echo 📦 Installing OpenShorts...
pip install openshorts*.whl

echo ✅ Installation complete!
echo.
echo 🚀 To run OpenShorts:
echo    openshorts
echo.
echo 🌐 Then open your browser to: http://127.0.0.1:7875
pause
'''

    with open('dist/install.bat', 'w') as f:
        f.write(bat_content.strip())
    print("✅ Created install.bat")

def main():
    print("🎬 OpenShorts Python Package Builder")
    print("====================================")
    
    if not os.path.exists('setup.py'):
        print("❌ Error: setup.py not found")
        sys.exit(1)
    
    try:
        # Clean previous builds
        clean_build()
        
        # Install build dependencies  
        install_build_deps()
        
        # Build wheel
        if build_wheel():
            # Create installer scripts
            create_install_script()
            create_windows_installer()
            
            print("\\n🎉 Package building complete!")
            print("📁 Distribution files:")
            for file in Path("dist").iterdir():
                print(f"   - {file.name}")
            
            print("\\n📋 Distribution options:")
            print("   1. Upload to PyPI: python -m twine upload dist/*.whl")
            print("   2. Local install: pip install dist/*.whl")
            print("   3. Share dist/ folder with install scripts")
            
            # Test installation
            print("\\n🧪 To test locally:")
            print("   pip install dist/openshorts-*.whl")
            print("   openshorts")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()