# URL Download Feature - Usage Examples

## Supported Platforms

OpenShorts now supports downloading videos from these platforms:

- **YouTube** - `https://youtube.com/watch?v=...` or `https://youtu.be/...`
- **TikTok** - `https://tiktok.com/@user/video/...`
- **Twitter/X** - `https://twitter.com/user/status/...` or `https://x.com/user/status/...`
- **Instagram** - `https://instagram.com/p/...` or `https://instagram.com/reel/...`
- **Vimeo** - `https://vimeo.com/...`
- **Twitch** - `https://twitch.tv/videos/...`
- **Facebook** - `https://facebook.com/watch/...`
- **Dailymotion** - `https://dailymotion.com/video/...`
- **Rumble** - `https://rumble.com/...`
- **And many more...**

## How to Use

1. **Open OpenShorts**: Run `python openshorts.py` 
2. **Switch to URL Mode**: In the "Upload & Transcribe" tab, select "Video URL" radio button
3. **Paste URL**: Enter any supported video URL in the text box
4. **Download & Process**: Click "Download & Transcribe" button
5. **Wait for Processing**: The app will:
   - Download the video (with progress bar)
   - Extract audio and transcribe it
   - Make it available for all clip generation features

## Example URLs to Try

```
# YouTube short tutorial
https://youtube.com/watch?v=dQw4w9WgXcQ

# TikTok video  
https://tiktok.com/@username/video/1234567890

# Twitter/X video
https://twitter.com/username/status/1234567890
```

## Features Available After URL Download

Once downloaded, the video works exactly like a local upload:

- ✅ **Auto Clip Generation** - AI-powered scene detection
- ✅ **AI Smart Clips** - Ollama-powered viral moment selection  
- ✅ **Manual Clips** - Custom time ranges
- ✅ **SRT Export** - Standard subtitle files
- ✅ **Animated Captions** - Professional ASS subtitles
- ✅ **Vertical/Horizontal** - Perfect for shorts or traditional videos
- ✅ **Background Music** - Add your own tracks
- ✅ **Batch Processing** - Multiple URLs (coming soon)

## Quality & Settings

- **Auto Quality**: Downloads best quality up to 1080p MP4
- **Format Priority**: MP4 > WebM > Other formats
- **File Storage**: Temporary files cleaned up after processing
- **Error Handling**: Clear error messages for private/unavailable videos

## Privacy & Offline

- **No Cloud Processing**: Videos downloaded locally, never sent anywhere 
- **Temporary Storage**: Downloaded files deleted after processing
- **Your Data**: Stays on your machine completely

Enjoy creating clips from any video on the internet! 🎬✨