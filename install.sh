#!/bin/bash
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