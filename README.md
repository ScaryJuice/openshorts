# OpenShorts

A professional, fully local, open-source video clipper designed to turn long-form videos into engaging short-form content — your personal, offline alternative to Opus Clip and CapCut.

100% private: no cloud uploads, no subscriptions, no data leaves your machine.

## Features

- **Video URL Support (Still in testing, suggest manual upload)** - Paste YouTube, TikTok, Twitter/X, Instagram, Vimeo links and process them directly
- **Automatic intelligent clip generation** with natural language-based scene detection and virality scoring
- **AI-powered clip selection** using local Ollama models (optional but powerful)
- **Advanced animated caption system** with multiple styles: TikTok-style word-highlight, YouTube professional, Minimal clean, etc. - NOT working well at the moment.
- **SRT subtitle export** - Export standard SRT subtitle files alongside videos for universal compatibility
- **Vertical (9:16) Shorts** and **Horizontal (16:9)** output modes — always ≥1080p resolution
- **Background music integration** (add your own royalty-free loops)
- **Batch processing** support for multiple videos
- **Persistent settings** saved to JSON file
- **Clean output folder** with clips, thumbnails, and optional SRT files

## Installation & Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- 4GB+ available disk space (for AI models)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/openshorts.git
   cd openshorts
   ```
2. **Start all services:**

   ```bash
   docker-compose up -d
   ```

   This will automatically:

   - Build the OpenShorts container
   - Download and start Ollama AI service
   - Pull the llama3.2 model (~2GB) for AI features
3. **Access the app:**Open http://localhost:7875 in your browser
4. **Stop when done:**

   ```bash
   docker-compose down
   ```

**Services included:**

- OpenShorts web interface: `http://localhost:7875`
- Ollama AI service: `http://localhost:11434` (automatic)

## Usage

1. **Ensure services are running:**

   ```bash
   docker-compose ps
   ```

   (All services should show "Up" status)
2. **Open the web interface:**http://localhost:7875
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
6. Choose generation mode:

   - **Quick Shorts** → fast automatic clipping
   - **AI Smart Clips** → uses Ollama to select the most engaging moments
7. Watch progress in real-time (transcription + rendering)

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

- **Services not starting** → Run `docker-compose logs` to check for errors
- **Ollama not available** → Wait for model download: `docker-compose logs ollama-init -f`
- **Port conflicts** → Change ports in docker-compose.yml if 7875 or 11434 are in use
- **Performance issues** → Ensure Docker has adequate resources (4GB+ RAM recommended)
- **No face detection** → Feature works automatically; fallback to center crop if needed

**Check service status:**

```bash
docker-compose ps          # View all services
docker-compose logs app    # Check app logs  
docker-compose logs ollama # Check AI service logs
```

**Restart if needed:**

```bash
docker-compose down && docker-compose up -d
```

## Why OpenShorts?

Because you should own your tools.
No watermarks, no usage limits, no monthly fees, full control over every frame and subtitle.

Built for creators who value privacy, quality, and customization.

Enjoy clipping — completely offline and yours forever.
