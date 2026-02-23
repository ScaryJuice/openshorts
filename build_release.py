#!/usr/bin/env python3
"""
OpenShorts Packaging Script
Creates distributable executables using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def create_spec_file():
    """Create a custom .spec file for advanced packaging"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all Gradio data files
gradio_datas = collect_data_files('gradio')
safehttpx_datas = collect_data_files('safehttpx')
faster_whisper_datas = collect_data_files('faster_whisper')

# Collect all submodules
gradio_hiddenimports = collect_submodules('gradio')
torch_hiddenimports = collect_submodules('torch')

block_cipher = None

a = Analysis(
    ['openshorts.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ] + gradio_datas + safehttpx_datas + faster_whisper_datas,
    hiddenimports=[
        'gradio',
        'gradio.components',
        'gradio.themes',
        'gradio.blocks',
        'gradio.interface',
        'gradio.processing_utils',
        'gradio._simple_templates',
        'faster_whisper',
        'cv2', 
        'ollama',
        'PIL',
        'PIL._tkinter_finder',
        'numpy',
        'torch',
        'transformers',
        'ctranslate2',
        'onnxruntime',
        'safehttpx',
        'httpx',
        'uvicorn',
        'websockets',
        'jinja2',
        'markupsafe',
        'typing_extensions',
        'pathlib',
    ] + gradio_hiddenimports + torch_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OpenShorts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('openshorts.spec', 'w') as f:
        f.write(spec_content.strip())
    print("✅ Created openshorts.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building OpenShorts executable...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Build using spec file
    cmd = ['pyinstaller', '--clean', 'openshorts.spec']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        print(f"📁 Executable created: {os.path.abspath('dist/OpenShorts')}")
        return True
    else:
        print("❌ Build failed:")
        print(result.stderr)
        return False

def create_installer_script():
    """Create a simple installer script for end users"""
    installer_content = '''#!/bin/bash
# OpenShorts Installer Script

echo "🎬 OpenShorts Installer"
echo "======================"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "📥 FFmpeg not found. Please install FFmpeg first:"
    echo ""
    echo "macOS: brew install ffmpeg"
    echo "Ubuntu: sudo apt install ffmpeg"  
    echo "Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue anyway? (y/N): " continue_install
    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create application directory
APP_DIR="$HOME/Applications/OpenShorts"
mkdir -p "$APP_DIR"

# Copy executable
cp OpenShorts "$APP_DIR/"
chmod +x "$APP_DIR/OpenShorts"

# Create desktop shortcut (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    cat > "$HOME/.local/share/applications/openshorts.desktop" << EOF
[Desktop Entry]
Name=OpenShorts
Comment=AI Video Clipper
Exec=$APP_DIR/OpenShorts
Icon=video-editor
Type=Application
Categories=AudioVideo;
EOF
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - create alias
    ln -sf "$APP_DIR/OpenShorts" "/usr/local/bin/openshorts"
fi

echo "✅ OpenShorts installed successfully!"
echo "🚀 Run 'openshorts' from terminal or find it in your applications"
'''

    with open('install.sh', 'w') as f:
        f.write(installer_content.strip())
    os.chmod('install.sh', 0o755)
    print("✅ Created install.sh")

def main():
    print("🎬 OpenShorts Packaging Tool")
    print("============================")
    
    # Check if we're in the right directory
    if not os.path.exists('openshorts.py'):
        print("❌ Error: openshorts.py not found. Run this script from the project directory.")
        sys.exit(1)
    
    try:
        # Step 1: Install PyInstaller
        install_pyinstaller()
        
        # Step 2: Create spec file
        create_spec_file()
        
        # Step 3: Build executable
        if build_executable():
            # Step 4: Create installer
            create_installer_script()
            
            print("\\n🎉 Packaging complete!")
            print("📁 Files created:")
            print("   - dist/OpenShorts (executable)")
            print("   - install.sh (installer script)")
            print("\\n📋 Next steps:")
            print("   1. Test the executable: ./dist/OpenShorts")
            print("   2. Distribute the dist/ folder with install.sh")
            print("   3. Users run: ./install.sh")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()