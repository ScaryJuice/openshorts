@echo off
REM OpenShorts Windows Packaging Script

echo 🎬 OpenShorts Windows Packaging
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

REM Install PyInstaller
echo 📦 Installing PyInstaller...
python -m pip install pyinstaller

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Create the spec file for Windows
echo 🔨 Creating Windows spec file...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['openshorts.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('requirements.txt', '.'^^),
echo         ^('README.md', '.'^^),
echo     ],
echo     hiddenimports=[
echo         'gradio',
echo         'faster_whisper', 
echo         'cv2',
echo         'ollama',
echo         'PIL',
echo         'numpy'
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='OpenShorts',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=True,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon=None,
echo ^^)
) > openshorts_windows.spec

REM Build executable
echo 🔨 Building Windows executable...
pyinstaller --clean openshorts_windows.spec

if %errorlevel% equ 0 (
    echo ✅ Build successful!
    echo 📁 Executable created: %cd%\dist\OpenShorts.exe
    
    REM Create simple installer batch file
    echo 🚀 Creating installer...
    (
        echo @echo off
        echo echo 🎬 OpenShorts Installer
        echo echo ======================
        echo.
        echo REM Check FFmpeg
        echo ffmpeg -version ^>nul 2^>^&1
        echo if %%errorlevel%% neq 0 ^(
        echo     echo ❌ FFmpeg not found. Please install FFmpeg first:
        echo     echo    Download from: https://ffmpeg.org/download.html#build-windows
        echo     echo    Or use: winget install ffmpeg
        echo     pause
        echo     exit /b 1
        echo ^^)
        echo.
        echo REM Copy to Program Files
        echo set "INSTALL_DIR=%%LOCALAPPDATA%%\OpenShorts"
        echo mkdir "%%INSTALL_DIR%%" 2^>nul
        echo copy "OpenShorts.exe" "%%INSTALL_DIR%%\"
        echo.
        echo echo ✅ OpenShorts installed to %%INSTALL_DIR%%
        echo echo 🚀 You can now run OpenShorts from the Start Menu
        echo pause
    ) > dist\install.bat
    
    echo ✅ Windows packaging complete!
    echo 📋 Distribute the dist\ folder to Windows users
) else (
    echo ❌ Build failed
    pause
    exit /b 1
)

pause