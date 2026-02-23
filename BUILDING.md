# OpenShorts Development Guide

## Building Releases

### Automated Releases (Recommended)

OpenShorts uses GitHub Actions for automated cross-platform builds:

1. **Tag a release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions automatically**:
   - Builds executables for Windows, macOS, and Linux
   - Creates release packages with installers
   - Publishes to GitHub Releases

### Manual Building

#### All Platforms
```bash
python build_release.py
```

#### Windows Only
```bash
build_windows.bat
```

#### Docker Image
```bash
docker build -t openshorts .
docker run -p 7875:7875 openshorts
```

## Packaging Challenges Solved

### FFmpeg Dependency
- **Problem**: FFmpeg is a large external dependency
- **Solution**: User installs FFmpeg separately (documented in README)
- **Alternative**: Include FFmpeg binary (increases size to ~200MB)

### ML Models
- **Problem**: faster-whisper models are 100MB+ each
- **Solution**: Models download automatically on first use
- **Alternative**: Pre-bundle common models (increases size significantly)

### Large Executable Size
- **Current size**: ~150MB (includes Python runtime + all dependencies)
- **Optimization**: Use `--exclude-module` for unused packages
- **Alternative**: Create installer that downloads components

## Distribution Strategy

### Target Platforms
1. **Windows 10/11** (largest user base)
2. **macOS 10.14+** (content creators)
3. **Ubuntu/Debian** (developer community)

### Release Channels
1. **GitHub Releases** - Main distribution
2. **Docker Hub** - Containerized version
3. **Homebrew** - macOS package manager (future)
4. **Chocolatey** - Windows package manager (future)
5. **Snap Store** - Linux universal packages (future)

## Testing Releases

### Pre-release Checklist
- [ ] Test FFmpeg detection
- [ ] Test video upload/processing
- [ ] Test caption generation
- [ ] Test Ollama integration (optional)
- [ ] Test on clean system (no dev dependencies)
- [ ] Verify file permissions
- [ ] Test installer scripts

### Platform-Specific Tests
- **Windows**: Test on Windows 10/11, with/without admin rights
- **macOS**: Test on Intel and Apple Silicon, handle code signing
- **Linux**: Test on Ubuntu 20.04+, verify FFmpeg installation

## Future Improvements

### Code Signing
- **Windows**: Sign .exe files to avoid security warnings
- **macOS**: Sign and notarize for Gatekeeper compatibility

### Auto-updater
- Implement in-app update mechanism
- Use GitHub API to check for new versions

### Smaller Executables
- Split into core app + downloadable components
- Use virtual environments more efficiently

### Professional Installer
- Create MSI for Windows
- Create .pkg for macOS  
- Create .deb/.rpm for Linux