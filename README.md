# OpenShorts

A professional, fully local, open-source video clipper designed to turn long-form videos into engaging short-form content — your personal, offline alternative to Opus Clip and CapCut.

100% private: no cloud uploads, no subscriptions, no data leaves your machine.

## Features

- **Video URL Support** - Paste YouTube, TikTok, Twitter/X, Instagram, Vimeo links and process them directly
- **Automatic intelligent clip generation** with natural language-based scene detection and virality scoring
- **AI-powered clip selection** using local Ollama models (optional but powerful)
- **Advanced animated caption system** with multiple styles: TikTok-style word-highlight, YouTube professional, Minimal clean, etc. - NOT working well at the moment.
- **SRT subtitle export** - Export standard SRT subtitle files alongside videos for universal compatibility
- **Vertical (9:16) Shorts** and **Horizontal (16:9)** output modes — always ≥1080p resolution
- **Background music integration** (add your own royalty-free loops)
- **Batch processing** support for multiple videos
- **Persistent settings** saved to JSON file
- **Clean output folder** with clips, thumbnails, and optional SRT files

## Installation

### Option 1: Python Package (Recommended)

**Download the wheel file from [Releases](../../releases) and install:**

```bash
# Download the .whl file, then:
pip install openshorts-2.0.0-py3-none-any.whl

# Or use the installer script (included in download):
./install.sh        # macOS/Linux
# or install.bat     # Windows
```

**Then run:**
```bash
openshorts
```

### Option 2: Docker (Cross-platform)

```bash
# Clone and run with Docker
git clone https://github.com/yourusername/openshorts.git
cd openshorts
docker-compose up -d
```

**Services included:**
- OpenShorts web interface: `http://localhost:7875`
- Ollama AI service: `http://localhost:11434`

To stop: `docker-compose down`

### Option 3: From Source (Developers)

- Python 3.10+ (recommended: 3.12 or 3.13)
- FFmpeg (required for video encoding/decoding)
- macOS, Linux, or Windows

## Installation

### 1. Install FFmpeg

**macOS** (using Homebrew):
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows**:
- Download the full build from https://www.gyan.dev/ffmpeg/builds/
- Extract and add the `bin` folder to your system PATH

### 2. (Strongly recommended) Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
# or on Windows: venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt

# For URL download support (recommended):
pip install yt-dlp
```

### 4. Optional: Ollama for smarter AI clip selection

1. Download and install Ollama: https://ollama.com/download
2. Install the Python package:
   ```bash
   pip install ollama
   ```
3. Start the server in a terminal:
   ```bash
   ollama serve
   ```
4. Pull a lightweight model (recommended):
   ```bash
   ollama pull llama3.2   # or gemma2:9b, phi3:medium, etc.
   ```

## Usage

1. Launch the app:
   ```bash
   python openshorts.py
   ```

2. Open your browser to:  
   http://localhost:7875 (or the port shown in the terminal)

3. Drag & drop (or browse) your long-form video **OR** paste a video URL

4. Choose your input method:
   - **File Upload**: Drop local video files
   - **Video URL**: Paste links from YouTube, TikTok, Twitter/X, Instagram, Vimeo, etc.

5. Configure options in the sidebar or settings tab:
   - Output mode: Vertical Shorts (1080×1920) or Horizontal (1920×1080+)
   - Caption style & animation
   - Desired number of clips
   - Clip length range
   - Background music folder (optional)
   - Face-detection sensitivity

5. Choose generation mode:
   - **Quick Shorts** → fast automatic clipping
   - **AI Smart Clips** → uses Ollama to select the most engaging moments

6. Watch progress in real-time (transcription + rendering)

## Output

All generated content is saved to:

```
./openshorts_clips/
├── clip_01.mp4
├── clip_01.srt              # If SRT export enabled
├── clip_01.ass              # If ASS export enabled  
├── clip_01_thumbnail.jpg
├── clip_02.mp4
├── full_transcript.srt      # Full video transcript (when exported)
└── ...
```

- Clips are named sequentially
- Thumbnails are auto-generated (middle frame)
- SRT files for universal subtitle compatibility 
- ASS files for advanced animated captions
- Optional full transcript export in SRT format

## Configuration

- All UI settings (caption style, default mode, clip count, etc.) are automatically saved to  
  `./openshorts_config.json`  
  and loaded on next launch.

## Troubleshooting

- **"FFmpeg not found"** → verify FFmpeg is installed and in your PATH (`ffmpeg -version` should work in terminal)
- **Slow performance** → transcription is CPU/GPU heavy; use a smaller Whisper model or enable GPU (CUDA/Metal)
- **Ollama not responding** → make sure `ollama serve` is running in another terminal
- **No face detection** → ensure OpenCV is installed correctly; fallback to center crop works automatically

## Why OpenShorts?

Because you should own your tools.  
No watermarks, no usage limits, no monthly fees, full control over every frame and subtitle.

Built for creators who value privacy, quality, and customization.

Enjoy clipping — completely offline and yours forever.
