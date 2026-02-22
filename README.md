# OpenShorts

A professional, fully local, open-source video clipper designed to turn long-form videos into engaging short-form content — your personal, offline alternative to Opus Clip and CapCut.

100% private: no cloud uploads, no subscriptions, no data leaves your machine.

## Features

- **Automatic intelligent clip generation** with natural language-based scene detection and virality scoring
- **AI-powered clip selection** using local Ollama models (optional but powerful)
- **Advanced animated caption system** with multiple styles: TikTok-style word-highlight, YouTube professional, Minimal clean, etc.
- **Vertical (9:16) Shorts** and **Horizontal (16:9)** output modes — always ≥1080p resolution
- **Intelligent face-aware cropping** for vertical mode (using OpenCV face detection)
- **Word-level timed subtitles** with highlight animation
- **Background music integration** (add your own royalty-free loops)
- **Batch processing** support for multiple videos
- **Persistent settings** saved to JSON file
- **Clean output folder** with clips, thumbnails, and optional SRT files

## Requirements

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
```

### 4. Optional: Ollama for smarter AI clip selection

1. Download and install Ollama: https://ollama.com/download
2. Start the server in a terminal:
   ```bash
   ollama serve
   ```
3. Pull a lightweight model (recommended):
   ```bash
   ollama pull llama3.2   # or gemma2:9b, phi3:medium, etc.
   ```

## Usage

1. Launch the app:
   ```bash
   python openshorts.py
   ```

2. Open your browser to:  
   http://127.0.0.1:7875 (or the port shown in the terminal)

3. Drag & drop (or browse) your long-form video

4. Configure options in the sidebar or settings tab:
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
├── clip_01_thumbnail.jpg
├── clip_02.mp4
└── ...
```

- Clips are named sequentially
- Thumbnails are auto-generated (middle frame)
- Optional SRT subtitle files if enabled

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
