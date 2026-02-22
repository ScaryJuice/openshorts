# OpenShorts

A professional video clipper for creating short-form content with automated transcription, intelligent clipping, and advanced caption systems.

## Features

- Automatic clip generation with virality scoring
- AI-powered clip selection using Ollama
- Advanced caption system with multiple styles (TikTok, YouTube, Professional, Minimal)
- Vertical (9:16) and horizontal (16:9) output modes
- Face detection for intelligent cropping
- Background music integration
- Word-level caption timing

## Requirements

- Python 3.14+
- FFmpeg
- Homebrew (macOS)

## Installation

1. Install system dependencies:
   ```bash
   brew install ffmpeg
   ```

2. Install Python dependencies:
   ```bash
   pip install --break-system-packages gradio faster-whisper opencv-python pillow
   ```

3. Optional: Install Ollama for AI-powered clipping:
   ```bash
   pip install --break-system-packages ollama
   ```

## Usage

1. Run the application:
   ```bash
   python openshorts.py
   ```

2. Open browser to `http://127.0.0.1:7875`

3. Upload video file

4. Configure settings:
   - Output mode (vertical/horizontal)
   - Caption style
   - Clip preferences

5. Generate clips using either:
   - Quick Shorts (automatic)
   - AI Smart Clips (requires Ollama)

## Output

Generated clips are saved to the `openshorts_clips/` directory with sequential naming: `clip_01.mp4`, `clip_02.mp4`, etc.

## Configuration

Settings are automatically saved to `openshorts_config.json` and persist between sessions.