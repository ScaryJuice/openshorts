"""
OpenShorts v2 — Built for Tyler Hudson — February 2026
===========================================================
A fully local, offline-first short-form video clipper
100% alternative to Opus Clip + CapCut

New v2 Features:
- Vertical 9:16 Shorts Mode with intelligent cropping
- Professional animated captions (word-by-word highlighting)
- Smarter clip intelligence with virality scoring
- Modern tabbed UI with progress bars and settings
- Batch processing and thumbnail generation
- Background music mixing capabilities
- Persistent user preferences

Requirements:
- ffmpeg (brew install ffmpeg)
- python packages: gradio>=4.0.0 faster-whisper ollama (optional) moviepy opencv-python (optional)
"""

import gradio as gr
from faster_whisper import WhisperModel
import subprocess
import json
import os
from datetime import timedelta
import shutil
import tempfile
from pathlib import Path
import re
import math
import time
from typing import List, Dict, Tuple, Optional

# Optional dependencies
try:
    import ollama
    # Test if Ollama service is actually running and accessible
    try:
        models = ollama.list()
        OLLAMA_AVAILABLE = len(models.get('models', [])) > 0
    except Exception:
        OLLAMA_AVAILABLE = False
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

# Configuration manager
class Config:
    def __init__(self):
        self.config_path = "openshorts_config.json"
        self.default_config = {
            "output_mode": "long-form",  # horizontal, vertical, or long-form
            "talking_head_mode": False,
            "animated_captions": False,
            "caption_style": {
                "style": "tiktok",
                "font_size": 28,
                "font_color": "white",
                "highlight_color": "yellow",
                "position": "bottom",
                "background_box": True,
                "font_family": "Arial Black",
                "auto_effects": True,
                "word_emphasis": True
            },
            "clip_preferences": {
                "min_duration": 60,
                "max_duration": 180,
                "preferred_count": 4,
                "hook_first_mode": True
            },
            "background_music": {
                "enabled": False,
                "volume": 0.15,
                "music_folder": ""
            },
            "export_settings": {
                "export_srt": False,
                "export_ass": True,
                "srt_style": "simple"
            },
            "stock_video": {
                "enabled": False,
                "folder_path": "",
                "usage_percentage": 30,
                "selection_mode": "random",
                "emphasis_threshold": 70,
                "min_segment_duration": 2.0,
                "max_segment_duration": 8.0
            }
        }
        self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new keys
                    self.config = {**self.default_config, **loaded}
            else:
                self.config = self.default_config.copy()
        except Exception as e:
            print(f"Config load error: {e}, using defaults")
            self.config = self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def get(self, key_path: str, default=None):
        """Get nested config value using dot notation like 'caption_style.font_size'"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value):
        """Set nested config value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()

# Global config instance
config = Config()

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

def get_resolution(video_path):
    """Get video resolution using ffprobe"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-select_streams", "v:0", video_path]
    try:
        output = subprocess.check_output(cmd).decode()
        data = json.loads(output)
        return int(data["streams"][0]["width"]), int(data["streams"][0]["height"])
    except Exception as e:
        print(f"Resolution detection failed: {e}")
        return 1920, 1080

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_entries", "format=duration", video_path]
    try:
        output = subprocess.check_output(cmd).decode()
        data = json.loads(output)
        return float(data["format"]["duration"])
    except Exception as e:
        print(f"Duration detection failed: {e}")
        return 0

def detect_face_center(video_path, timestamp=30):
    """
    Detect face center for smart cropping (requires opencv)
    Returns (x, y) center coordinates or None if no face detected
    """
    if not OPENCV_AVAILABLE:
        return None
    
    try:
        # Validate timestamp against video duration
        duration = get_video_duration(video_path)
        if duration and timestamp >= duration:
            timestamp = min(30, duration / 2)  # Use 30s or middle of video, whichever is smaller
        
        # Extract a frame at the given timestamp
        cmd = ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path, "-vframes", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg failed to extract frame: {result.stderr}")
            return None
        
        if not result.stdout or len(result.stdout) == 0:
            print("FFmpeg returned empty frame data")
            return None
        
        # Decode image
        import numpy as np
        nparr = np.frombuffer(result.stdout, np.uint8)
        
        if len(nparr) == 0:
            print("Empty frame buffer from FFmpeg")
            return None
            
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None or frame.size == 0:
            print("Failed to decode frame data")
            return None
        
        # Load face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            # Return center of largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            return (x + w//2, y + h//2)
        
    except Exception as e:
        print(f"Face detection failed: {e}")
        return None
        return None
    except Exception as e:
        print(f"Face detection failed: {e}")
        return None

def create_advanced_captions(segments, output_path, caption_style, video_resolution=(1080, 1920)):
    """
    Create professional-grade captions with precise word-level timing and effects
    """
    style_name = caption_style.get("style", "tiktok")  # tiktok, youtube, professional, minimal
    font_size = caption_style.get("font_size", 28)
    primary_color = caption_style.get("font_color", "white")
    highlight_color = caption_style.get("highlight_color", "yellow")
    position = caption_style.get("position", "bottom")
    background_box = caption_style.get("background_box", True)
    font_family = caption_style.get("font_family", "Arial Black")
    
    # Style configurations
    styles = {
        "tiktok": {
            "font": "Arial Black",
            "size": 32,
            "outline": 3,
            "shadow": 2,
            "bg_alpha": 160,
            "animation": "bounce"
        },
        "youtube": {
            "font": "Roboto",
            "size": 28,
            "outline": 2,
            "shadow": 1,
            "bg_alpha": 180,
            "animation": "slide"
        },
        "professional": {
            "font": "Helvetica",
            "size": 24,
            "outline": 1,
            "shadow": 1,
            "bg_alpha": 200,
            "animation": "fade"
        },
        "minimal": {
            "font": "SF Pro Display",
            "size": 26,
            "outline": 1,
            "shadow": 0,
            "bg_alpha": 140,
            "animation": "typewriter"
        }
    }
    
    current_style = styles.get(style_name, styles["tiktok"])
    
    # Calculate positioning based on video resolution
    margin_v = 50 if video_resolution[1] > 1080 else 30
    if position == "bottom":
        alignment = 2
    elif position == "top":
        alignment = 8
    else:  # center
        alignment = 5
    
    # ASS header with advanced styling
    ass_content = f"""[Script Info]
Title: OpenShorts Advanced Captions
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{current_style['font']},{current_style['size']},&H00FFFFFF,&H000000FF,&H00000000,&H{current_style['bg_alpha']:02x}000000,1,0,0,0,100,100,2,0,{'3' if background_box else '1'},{current_style['outline']},{current_style['shadow']},{alignment},20,20,{margin_v},1
Style: Highlight,{current_style['font']},{current_style['size'] + 2},&H0000FFFF,&H000000FF,&H00000000,&H{current_style['bg_alpha']:02x}000000,1,0,0,0,110,110,2,0,{'3' if background_box else '1'},{current_style['outline'] + 1},{current_style['shadow'] + 1},{alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Process segments with word-level timing
    for seg_idx, segment in enumerate(segments):
        if not segment.get("words") or len(segment["words"]) == 0:
            # Fallback to segment-level timing if no word data
            start_ass = format_time_ass(segment["start"])
            end_ass = format_time_ass(segment["end"])
            text = segment["text"].strip()
            
            # Enhance text with emojis and effects if enabled
            if caption_style.get("auto_effects", True):
                text = enhance_caption_text(text, True)
            
            if current_style["animation"] == "bounce":
                effect_text = f"{{\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)}}{text}"
            elif current_style["animation"] == "slide":
                effect_text = f"{{\\move(-50,0,0,0)}}{text}"
            elif current_style["animation"] == "fade":
                effect_text = f"{{\\fad(200,200)}}{text}"
            else:  # typewriter or default
                effect_text = text
            
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{effect_text}\n"
            continue
        
        # Advanced word-by-word processing
        words = segment["words"]
        if not words:
            continue
            
        # Group words into natural phrases (3-5 words max)
        phrase_groups = []
        current_phrase = []
        
        for word in words:
            current_phrase.append(word)
            
            # Break phrase on punctuation or when reaching max length
            if (len(current_phrase) >= 4 or 
                any(punct in word["text"] for punct in ",.!?;:") or
                word == words[-1]):
                
                if current_phrase:
                    phrase_groups.append(current_phrase)
                    current_phrase = []
        
        # Create captions for each phrase with word highlighting
        for phrase_idx, phrase in enumerate(phrase_groups):
            if not phrase:
                continue
                
            phrase_start = phrase[0]["start"]
            phrase_end = phrase[-1]["end"]
            phrase_duration = phrase_end - phrase_start
            
            # Build karaoke effect with precise timing
            karaoke_text = ""
            cumulative_time = 0
            
            for word_idx, word in enumerate(phrase):
                word_text = word["text"].strip()
                if not word_text:
                    continue
                    
                # Calculate word duration in centiseconds
                if word_idx < len(phrase) - 1:
                    word_duration = (phrase[word_idx + 1]["start"] - word["start"]) * 100
                else:
                    remaining_time = (phrase_end - word["start"]) * 100
                    word_duration = max(remaining_time, 50)  # Min 0.5s per word
                
                word_duration = int(max(word_duration, 30))  # Min 0.3s per word
                
                # Add word with karaoke timing
                if word_idx == 0:
                    karaoke_text += f"{{\\k{word_duration}}}{word_text}"
                else:
                    karaoke_text += f" {{\\k{word_duration}}}{word_text}"
            
            # Add animation effects based on style
            if current_style["animation"] == "bounce":
                karaoke_text = f"{{\\t(0,300,\\fscx110\\fscy110)\\t(300,600,\\fscx100\\fscy100)}}{karaoke_text}"
            elif current_style["animation"] == "slide":
                karaoke_text = f"{{\\move(50,0,0,0,0,300)}}{karaoke_text}"
            elif current_style["animation"] == "fade":
                karaoke_text = f"{{\\fad(150,150)}}{karaoke_text}"
            
            # Convert times to ASS format
            start_ass = format_time_ass(phrase_start)
            end_ass = format_time_ass(phrase_end)
            
            # Add caption line
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{karaoke_text}\n"
    
    # Write ASS file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    return output_path

def enhance_caption_text(text, auto_effects=True):
    """
    Enhance caption text with emojis and formatting for better engagement
    """
    if not auto_effects:
        return text
    
    # Emotion-based emoji mapping
    emoji_map = {
        # Positive emotions
        "amazing": "🤩", "incredible": "😱", "awesome": "🔥", "great": "👌",
        "love": "❤️", "perfect": "✨", "excellent": "💯", "fantastic": "🎉",
        "wonderful": "🌟", "outstanding": "🏆", "brilliant": "💎", "superb": "👏",
        
        # Surprise/shock
        "shocking": "😲", "surprising": "😮", "unbelievable": "🤯", "wow": "😍",
        "omg": "😱", "crazy": "🤪", "insane": "🤯", "mind-blowing": "🤯",
        
        # Questions/thinking
        "think": "🤔", "wonder": "💭", "question": "❓", "why": "🤷",
        "how": "❓", "what": "❓", "when": "⏰", "where": "📍",
        
        # Actions
        "money": "💰", "cash": "💵", "dollars": "💲", "profit": "📈",
        "growth": "📊", "success": "🚀", "win": "🏅", "victory": "🎯",
        "fire": "🔥", "hot": "🌶️", "cool": "😎", "cold": "❄️",
        
        # Warnings/alerts\n        "warning": "⚠️", "danger": "⛔", "stop": "🛑", "alert": "🚨",
        "important": "❗", "urgent": "🔴", "critical": "💥", "serious": "😐",
        
        # Time/numbers
        "first": "1️⃣", "second": "2️⃣", "third": "3️⃣", "one": "1️⃣", 
        "two": "2️⃣", "three": "3️⃣", "four": "4️⃣", "five": "5️⃣",
        
        # Common words
        "yes": "✅", "no": "❌", "right": "✅", "wrong": "❌",
        "up": "⬆️", "down": "⬇️", "new": "🆕", "free": "🆓"
    }
    
    # Apply emoji replacements (case insensitive)
    enhanced_text = text
    for word, emoji in emoji_map.items():
        # Match whole words only, case insensitive
        import re
        pattern = r'\\b' + re.escape(word) + r'\\b'
        enhanced_text = re.sub(pattern, f"{word} {emoji}", enhanced_text, flags=re.IGNORECASE)
    
    # Add emphasis for important phrases
    emphasis_patterns = [
        (r'\\b(never|always|everyone|nobody)\\b', r'{\\b1}\\1{\\b0}'),  # Make absolute words bold
        (r'\\b(\\d+%|\\d+x|\\d+ times)\\b', r'{\\c&H00FFFF&}\\1{\\c&HFFFFFF&}'),  # Highlight numbers/stats
    ]
    
    for pattern, replacement in emphasis_patterns:
        enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
    
    return enhanced_text

def format_time_ass(seconds):
    """Convert seconds to ASS time format H:MM:SS.CS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def format_time_srt(seconds):
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def create_srt_file(segments, output_path, style="simple"):
    """
    Create SRT subtitle file from transcript segments
    
    Args:
        segments: List of transcript segments with start, end, text
        output_path: Path to save the SRT file
        style: 'simple' (basic text) or 'enhanced' (with formatting)
    """
    srt_content = ""
    subtitle_count = 1
    
    for seg_idx, segment in enumerate(segments):
        start_time = format_time_srt(segment["start"])
        end_time = format_time_srt(segment["end"])
        text = segment["text"].strip()
        
        # Apply style formatting
        if style == "enhanced":
            # Add basic formatting for enhanced readability
            # Bold for emphasis words
            text = re.sub(r'\b(amazing|incredible|awesome|important|never|always)\b', r'<b>\1</b>', text, flags=re.IGNORECASE)
            # Italic for questions
            if text.endswith('?'):
                text = f"<i>{text}</i>"
        
        # Handle long lines (split at 42 characters - SRT best practice)
        if len(text) > 42:
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) <= 42:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            text = "\n".join(lines)
        
        # Add subtitle entry
        srt_content += f"{subtitle_count}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"
        
        subtitle_count += 1
    
    # Write SRT file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content.strip())
    
    return output_path

def create_smart_clip(input_video, start_sec, end_sec, output_path, progress_callback=None, clip_segments=None):
    """
    Create a clip with intelligent processing based on current settings
    Handles both horizontal and vertical modes, with optional captions, music, and stock video integration
    """
    try:
        output_mode = config.get("output_mode", "long-form")
        talking_head = config.get("talking_head_mode", False)
        add_captions = config.get("animated_captions", False)
        bg_music_enabled = config.get("background_music.enabled", False)
        stock_enabled = config.get("stock_video.enabled", False)
        # Temporarily disable stock video to fix FFmpeg syntax issues
        stock_enabled = False  # TODO: Remove this line when stock video is fixed
        
        w, h = get_resolution(input_video)
        
        # Determine output resolution and cropping based on mode
        if output_mode == "vertical":
            target_w, target_h = 1080, 1920
            # For vertical mode, we want to crop and scale intelligently
            if talking_head and h < w:  # Landscape video in portrait mode
                # Crop to center or face-detected area
                face_center = detect_face_center(input_video, start_sec + 5) if OPENCV_AVAILABLE else None
                if face_center:
                    crop_x = max(0, min(face_center[0] - h//2, w - h))
                    crop_filter = f"crop={h}:{h}:{crop_x}:0"
                else:
                    # Center crop to square, then scale
                    crop_size = min(w, h)
                    crop_x = (w - crop_size) // 2
                    crop_y = (h - crop_size) // 2
                    crop_filter = f"crop={crop_size}:{crop_size}:{crop_x}:{crop_y}"
                
                scale_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease"
                vf = f"{crop_filter},{scale_filter},pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
            else:
                # Standard vertical scaling with padding
                scale_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease"
                vf = f"{scale_filter},pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
        elif output_mode == "long-form":
            # Long-form content mode - optimized for longer clips with centered content
            target_w, target_h = 1920, 1080  # 16:9 landscape format
            # Center content with minimal cropping, preserve aspect ratio
            scale_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease"
            vf = f"{scale_filter},pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
        else:
            # Horizontal mode (original behavior)
            target_w, target_h = 1920, 1080
            if h < target_h:
                new_h = target_h
                new_w = (int(w * new_h / h) // 2) * 2
                vf = f"scale={new_w}:{new_h}:force_original_aspect_ratio=decrease,pad={new_w}:{new_h}:(ow-iw)/2:(oh-ih)/2:black"
            else:
                vf = None
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", input_video,
            "-t", str(end_sec - start_sec),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k"
        ]
        
        # Handle stock video integration if enabled
        stock_filter_complex = None
        stock_inputs_count = 0
        final_vf = None  # Initialize final_vf before any code paths
        
        if stock_enabled and clip_segments:
            stock_folder = config.get("stock_video.folder_path", "")
            stock_videos = get_stock_videos(stock_folder)
            
            if stock_videos:
                if progress_callback:
                    progress_callback(0.3, "Planning stock video integration...")
                
                usage_percent = config.get("stock_video.usage_percentage", 30)
                selection_mode = config.get("stock_video.selection_mode", "random")
                min_duration = config.get("stock_video.min_segment_duration", 2.0)
                max_duration = config.get("stock_video.max_segment_duration", 8.0)
                
                # Create stock video plan
                stock_plan = create_stock_integration_plan(
                    clip_segments, stock_videos, usage_percent, 
                    selection_mode, min_duration, max_duration
                )
                
                if stock_plan['segments']:
                    if progress_callback:
                        progress_callback(0.4, f"Adding {len(stock_plan['segments'])} stock video segments...")
                    
                    # Add stock video inputs to FFmpeg command
                    for i, stock_segment in enumerate(stock_plan['segments']):
                        stock_duration = stock_segment['end'] - stock_segment['start']
                        cmd.extend(["-ss", "0", "-i", stock_segment['stock_video'], "-t", str(stock_duration)])
                        stock_inputs_count += 1
                    
                    # Build filter complex for stock video compositing
                    filter_parts = []
                    
                    # Scale all stock videos to match output resolution
                    for i in range(stock_inputs_count):
                        input_idx = i + 1  # +1 because main video is input 0
                        filter_parts.append(f"[{input_idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black[stock{i}]")
                    
                    # Create overlay timeline with proper timing
                    main_input = "[0:v]"
                    if vf:  # Apply main video filters first
                        filter_parts.insert(0, f"[0:v]{vf}[main]")
                        main_input = "[main]"
                    
                    current_output = main_input
                    for i, stock_segment in enumerate(stock_plan['segments']):
                        start_time = stock_segment['start']
                        end_time = stock_segment['end']
                        # Proper FFmpeg overlay syntax: [base][overlay]overlay=enable='between(t,start,end)'[output]
                        filter_parts.append(f"{current_output}[stock{i}]overlay=enable='between(t,{start_time},{end_time})'[v{i}]")
                        current_output = f"[v{i}]"
                    
                    stock_filter_complex = ";".join(filter_parts)
                    final_video_map = f"[v{stock_inputs_count-1}]"
        
        # Handle video filtering and captions
        if stock_filter_complex:
            # Stock video integration with filter_complex
            caption_filter = ""
            if add_captions:
                ass_path = output_path.replace('.mp4', '.ass')
                if os.path.exists(ass_path):
                    try:
                        # Add captions to the final composited video
                        # Remove brackets from final_video_map for proper syntax
                        video_input = final_video_map.strip('[]')
                        caption_filter = f";[{video_input}]subtitles={ass_path}[final]"
                        final_video_map = "[final]"
                    except Exception as e:
                        print(f"Caption filter error in stock mode: {e}")
            
            cmd.extend(["-filter_complex", stock_filter_complex + caption_filter])
            cmd.extend(["-map", final_video_map, "-map", "0:a"])  # Map final video and original audio
        else:
            # Standard video filtering without stock integration
            final_vf = None
            if vf:
                final_vf = vf
                # Handle captions if enabled (with fallback)
                if add_captions:
                    ass_path = output_path.replace('.mp4', '.ass')
                    if os.path.exists(ass_path):
                        try:
                            # Properly escape subtitle path for FFmpeg filter
                            escaped_ass_path = ass_path.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
                            final_vf += f",subtitles='{escaped_ass_path}'"
                        except Exception as e:
                            print(f"Caption filter error, continuing without captions: {e}")
            elif add_captions:
                # Captions only, no other video filtering
                ass_path = output_path.replace('.mp4', '.ass')
                if os.path.exists(ass_path):
                    try:
                        # Properly escape subtitle path for FFmpeg filter
                        escaped_ass_path = ass_path.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
                        final_vf = f"subtitles='{escaped_ass_path}'"
                    except Exception as e:
                        print(f"Caption filter error, creating video without captions: {e}")
                        final_vf = None
            
            if final_vf:
                cmd.extend(["-vf", final_vf])
        
        # Add background music if enabled
        if bg_music_enabled:
            music_folder = config.get("background_music.music_folder", "")
            if music_folder and os.path.exists(music_folder):
                music_files = [f for f in os.listdir(music_folder) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
                if music_files:
                    import random
                    music_file = os.path.join(music_folder, random.choice(music_files))
                    volume = config.get("background_music.volume", 0.15)
                    
                    if stock_filter_complex:
                        # When stock video is enabled, add music input and integrate with existing filter_complex
                        music_input_idx = stock_inputs_count + 1  # After main video and stock videos
                        cmd.extend(["-i", music_file])
                        
                        # Update existing filter_complex to include audio mixing
                        audio_filter = f"[{music_input_idx}:a]volume={volume}[bg]; [0:a][bg]amix=inputs=2:duration=first[a]"
                        
                        # Find existing filter_complex in cmd and update it
                        for i, arg in enumerate(cmd):
                            if arg == "-filter_complex":
                                original_complex = cmd[i + 1]
                                cmd[i + 1] = original_complex + ";" + audio_filter
                                break
                        
                        # Update mapping to use mixed audio
                        for i, arg in enumerate(cmd):
                            if arg == "-map" and i + 1 < len(cmd) and cmd[i + 1] == "0:a":
                                cmd[i + 1] = "[a]"
                                break
                    else:
                        # Standard background music without stock video
                        cmd.extend(["-i", music_file])
                        cmd.extend(["-filter_complex", f"[1:a]volume={volume}[bg]; [0:a][bg]amix=inputs=2:duration=first[a]", "-map", "0:v", "-map", "[a]"])
        
        cmd.append(output_path)
        
        if progress_callback:
            progress_callback(0.5, "Rendering clip...")
        
        # Try to run FFmpeg, with fallback if subtitle processing fails
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # If there was a subtitle error, try again without captions
            # Only attempt subtitle fallback for non-stock video mode
            if "subtitles" in str(e.stderr) and not stock_filter_complex and final_vf and "subtitles" in final_vf:
                print(f"Subtitle processing failed, retrying without captions: {e.stderr}")
                # Remove subtitle filter and try again - handle both old and new syntax
                if ",subtitles=" in final_vf:
                    # Find the subtitles part and remove it (handles quoted paths)
                    import re
                    fallback_vf = re.sub(r',subtitles=[^,]*', '', final_vf)
                elif final_vf.startswith("subtitles="):
                    fallback_vf = None
                else:
                    fallback_vf = final_vf
                
                # Build new command without subtitles
                fallback_cmd = []
                for i, arg in enumerate(cmd):
                    if arg == "-vf" and i + 1 < len(cmd):
                        fallback_cmd.extend(["-vf", fallback_vf] if fallback_vf else [])
                        i += 1  # Skip the next argument (original vf)
                    elif i > 0 and cmd[i-1] == "-vf":
                        continue  # Skip this argument as it was the original vf
                    else:
                        fallback_cmd.append(arg)
                
                if progress_callback:
                    progress_callback(0.7, "Retrying without captions...")
                
                result = subprocess.run(fallback_cmd, check=True, capture_output=True, text=True)
            else:
                raise
        
        if progress_callback:
            progress_callback(1.0, "Clip completed!")
        
        return output_path
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg failed: {e.stderr.strip()}"
        if progress_callback:
            progress_callback(1.0, f"Error: {error_msg}")
        raise RuntimeError(error_msg) from e
    except FileNotFoundError:
        error_msg = "FFmpeg not found! Please install it (brew install ffmpeg)"
        if progress_callback:
            progress_callback(1.0, f"Error: {error_msg}")
        raise RuntimeError(error_msg)

def get_stock_videos(stock_folder):
    """Get list of stock video files from the specified folder"""
    if not stock_folder or not os.path.exists(stock_folder):
        return []
    
    stock_videos = []
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v')
    
    try:
        for file in os.listdir(stock_folder):
            if file.lower().endswith(video_extensions):
                full_path = os.path.join(stock_folder, file)
                if os.path.isfile(full_path):
                    stock_videos.append(full_path)
    except (OSError, PermissionError) as e:
        print(f"Error reading stock video folder: {e}")
        return []
    
    return stock_videos

def find_emphasis_segments(transcript_segments, min_segment_duration=2.0):
    """Find segments with high emphasis/energy for potential stock video replacement"""
    emphasis_segments = []
    
    for segment in transcript_segments:
        text = segment.get('text', '').lower()
        duration = segment.get('end', 0) - segment.get('start', 0)
        
        # Skip segments that are too short
        if duration < min_segment_duration:
            continue
        
        # Calculate emphasis score based on content
        emphasis_score = 0
        
        # High-energy words and phrases
        energy_words = [
            'amazing', 'incredible', 'awesome', 'fantastic', 'unbelievable',
            'shocking', 'surprising', 'mind-blowing', 'revolutionary',
            'breakthrough', 'game-changer', 'epic', 'insane', 'crazy'
        ]
        
        for word in energy_words:
            if word in text:
                emphasis_score += 2
        
        # Exclamation points and caps indicate energy
        emphasis_score += text.count('!') * 1.5
        emphasis_score += sum(1 for c in text if c.isupper()) * 0.1
        
        # Questions can be engaging
        if '?' in text:
            emphasis_score += 1
        
        # Numbers and statistics are often interesting
        import re
        if re.search(r'\d+', text):
            emphasis_score += 0.5
        
        segment_data = {
            'start': segment.get('start', 0),
            'end': segment.get('end', 0),
            'text': segment.get('text', ''),
            'emphasis_score': emphasis_score,
            'duration': duration
        }
        
        emphasis_segments.append(segment_data)
    
    # Sort by emphasis score (highest first)
    emphasis_segments.sort(key=lambda x: x['emphasis_score'], reverse=True)
    
    return emphasis_segments

def create_stock_integration_plan(transcript_segments, stock_videos, usage_percentage=30, 
                                selection_mode="random", min_duration=2.0, max_duration=8.0):
    """Create a plan for integrating stock videos at emphasis points"""
    if not stock_videos or usage_percentage <= 0:
        return {'segments': [], 'coverage_percentage': 0}
    
    # Find emphasis segments
    emphasis_segments = find_emphasis_segments(transcript_segments, min_duration)
    
    if not emphasis_segments:
        return {'segments': [], 'coverage_percentage': 0}
    
    # Calculate total clip duration
    total_duration = max([seg.get('end', 0) for seg in transcript_segments]) if transcript_segments else 0
    target_duration = (usage_percentage / 100) * total_duration
    
    # Select segments for stock video replacement
    selected_segments = []
    used_duration = 0
    stock_video_index = 0
    
    for segment in emphasis_segments:
        if used_duration >= target_duration:
            break
            
        # Limit segment duration
        segment_duration = min(segment['duration'], max_duration)
        segment_end = segment['start'] + segment_duration
        
        # Select stock video
        if selection_mode == "sequential":
            stock_video = stock_videos[stock_video_index % len(stock_videos)]
            stock_video_index += 1
        else:  # random
            import random
            stock_video = random.choice(stock_videos)
        
        selected_segments.append({
            'start': segment['start'],
            'end': segment_end,
            'stock_video': stock_video,
            'original_text': segment['text'],
            'emphasis_score': segment['emphasis_score']
        })
        
        used_duration += segment_duration
    
    coverage_percentage = (used_duration / total_duration * 100) if total_duration > 0 else 0
    
    return {
        'segments': selected_segments,
        'coverage_percentage': coverage_percentage,
        'total_stock_duration': used_duration
    }

def calculate_virality_score(segment_text, context_segments=None):
    """
    Calculate a simple virality score based on content analysis
    """
    text = segment_text.lower()
    score = 0
    
    # Hook words/phrases (start strong)
    hook_words = ["but", "however", "surprisingly", "shocking", "amazing", "incredible", "you won't believe", "here's why", "the truth is"]
    for word in hook_words:
        if word in text:
            score += 15
    
    # Emotion words
    emotion_words = ["love", "hate", "crazy", "insane", "mind-blowing", "game-changer", "secret", "mistake", "failure", "success"]
    for word in emotion_words:
        if word in text:
            score += 10
    
    # Question marks (engagement)
    score += text.count("?") * 5
    
    # Exclamation points (energy)
    score += text.count("!") * 3
    
    # Numbers and statistics
    if re.search(r'\d+%|\d+x|\d+ times', text):
        score += 8
    
    # Length penalty for too short/long
    word_count = len(text.split())
    if 30 <= word_count <= 100:
        score += 5
    elif word_count < 15 or word_count > 150:
        score -= 10
    
    return max(0, min(100, score))

def transcribe_with_progress(video_path, progress_callback=None):
    """Transcribe video with progress updates"""
    try:
        if progress_callback:
            progress_callback(0.1, "Loading Whisper model...")
        
        # Determine best compute type for the system
        compute_type = "int8"  # Safe default
        try:
            # Try float32 first (widely supported), then int8 as fallback
            import platform
            if platform.processor() == 'arm':  # Apple Silicon
                compute_type = "int8"  # Most reliable on Apple Silicon
            elif os.path.exists("/usr/local/cuda"):  # CUDA available
                compute_type = "float16"
            else:
                compute_type = "int8"  # Safe fallback
        except:
            compute_type = "int8"
        
        if progress_callback:
            progress_callback(0.15, f"Initializing Whisper model (compute: {compute_type})...")
        
        # Try to load model with fallback compute types
        model = None
        for fallback_type in [compute_type, "int8", "float32"]:
            try:
                model = WhisperModel(
                    "large-v3-turbo", 
                    device="auto", 
                    compute_type=fallback_type
                )
                if progress_callback:
                    progress_callback(0.2, f"✅ Model loaded with {fallback_type} compute type")
                break
            except Exception as e:
                if progress_callback:
                    progress_callback(0.15, f"Retrying with different compute type...")
                if fallback_type == "float32":  # Last attempt
                    raise RuntimeError(f"Could not load Whisper model with any compute type: {str(e)}")
                continue
        
        if model is None:
            raise RuntimeError("Failed to initialize Whisper model")
        
        if progress_callback:
            progress_callback(0.2, "Starting transcription...")
        
        segments, _ = model.transcribe(
            video_path, 
            beam_size=5, 
            vad_filter=True, 
            language="en",
            word_timestamps=True  # Enable word-level timestamps for better captions
        )
        
        if progress_callback:
            progress_callback(0.8, "Processing transcript...")
        
        # Convert to our format with word-level data if available
        transcript = []
        for seg in segments:
            segment_data = {
                "start": round(seg.start, 2), 
                "end": round(seg.end, 2), 
                "text": seg.text.strip(),
                "words": []
            }
            
            # Add word-level timestamps if available
            if hasattr(seg, 'words') and seg.words:
                for word in seg.words:
                    segment_data["words"].append({
                        "start": round(word.start, 2),
                        "end": round(word.end, 2),
                        "text": word.word.strip()
                    })
            
            transcript.append(segment_data)
        
        if progress_callback:
            progress_callback(1.0, f"✅ Transcription complete! {len(transcript)} segments")
        
        return transcript
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"❌ {error_msg}")
        raise RuntimeError(error_msg)

def auto_generate_clips_v2(transcript, video_path, progress_callback=None):
    """
    Enhanced auto clip generation with virality scoring and user preferences
    """
    try:
        min_duration = config.get("clip_preferences.min_duration", 60)
        max_duration = config.get("clip_preferences.max_duration", 180)
        num_clips = config.get("clip_preferences.preferred_count", 4)
        hook_first = config.get("clip_preferences.hook_first_mode", True)
        
        # Determine target resolution based on output mode
        output_mode = config.get("output_mode", "horizontal")
        if output_mode == "vertical":
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080
        
        if progress_callback:
            progress_callback(0.1, "Analyzing transcript for clips...")
        
        # Generate potential clips
        potential_clips = []
        current_start = 0.0
        current_text = ""
        
        i = 0
        while i < len(transcript):
            seg = transcript[i]
            segment_duration = seg["end"] - current_start
            
            # Check if we should finalize current clip
            if (segment_duration > max_duration or 
                (segment_duration >= min_duration and any(p in seg["text"] for p in ".!?"))):
                
                if segment_duration >= min_duration:
                    clip_text = current_text.strip()
                    virality_score = calculate_virality_score(clip_text)
                    
                    potential_clips.append({
                        "start": current_start,
                        "end": seg["end"],
                        "text": clip_text,
                        "score": virality_score,
                        "duration": segment_duration
                    })
                
                current_start = seg["end"]
                current_text = ""
            else:
                current_text += " " + seg["text"]
            
            i += 1
        
        # Sort by score, prioritizing hooks if enabled
        if hook_first:
            # Boost score for clips in first 25% of video
            video_duration = transcript[-1]["end"] if transcript else 0
            for clip in potential_clips:
                if clip["start"] < video_duration * 0.25:
                    clip["score"] += 20
        
        potential_clips.sort(key=lambda x: x["score"], reverse=True)
        selected_clips = potential_clips[:num_clips]
        
        # Sort selected clips by timestamp for processing
        selected_clips.sort(key=lambda x: x["start"])
        
        if progress_callback:
            progress_callback(0.3, f"Selected {len(selected_clips)} clips, generating videos...")
        
        # Create output directory
        output_dir = "openshorts_clips"
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for idx, clip in enumerate(selected_clips):
            if progress_callback:
                progress = 0.3 + (idx / len(selected_clips)) * 0.7
                progress_callback(progress, f"Creating clip {idx+1}/{len(selected_clips)}...")
            
            # Extract segments for this clip (used for both ASS and SRT)
            clip_segments = []
            for seg in transcript:
                if seg["start"] >= clip["start"] and seg["end"] <= clip["end"]:
                    # Adjust timestamps relative to clip start
                    adjusted_seg = {
                        "start": seg["start"] - clip["start"],
                        "end": seg["end"] - clip["start"],
                        "text": seg["text"],
                        "words": []
                    }
                    # Adjust word timestamps if available
                    if "words" in seg and seg["words"]:
                        for word in seg["words"]:
                            if word["start"] >= clip["start"] and word["end"] <= clip["end"]:
                                adjusted_seg["words"].append({
                                    "start": word["start"] - clip["start"],
                                    "end": word["end"] - clip["start"],
                                    "text": word["text"]
                                })
                    clip_segments.append(adjusted_seg)
            
            # Generate clip path first
            out_path = os.path.join(output_dir, f"clip_{idx+1:02d}.mp4")
            
            # Create caption files if enabled
            if config.get("animated_captions", False) or config.get("export_settings.export_ass", True):
                ass_path = out_path.replace('.mp4', '.ass')
                if clip_segments:
                    create_advanced_captions(
                        clip_segments, 
                        ass_path, 
                        config.get("caption_style", {}),
                        (target_w, target_h)
                    )
            
            # Create SRT file if enabled
            if config.get("export_settings.export_srt", False):
                srt_path = out_path.replace('.mp4', '.srt')
                if clip_segments:
                    srt_style = config.get("export_settings.srt_style", "simple")
                    create_srt_file(clip_segments, srt_path, srt_style)
            create_smart_clip(video_path, clip["start"], clip["end"], out_path, progress_callback, clip_segments)
            
            # Create thumbnail
            thumb_path = generate_thumbnail(video_path, clip["start"] + clip["duration"]/2, out_path.replace('.mp4', '_thumb.jpg'))
            
            clip_info = (
                out_path, 
                f"Auto Clip {idx+1} • Score: {clip['score']}/100\n"
                f"{format_time(clip['start'])}–{format_time(clip['end'])} • "
                f"{clip['duration']:.1f}s\n{clip['text'][:120]}..."
            )
            results.append(clip_info)
        
        if progress_callback:
            progress_callback(1.0, f"✅ Generated {len(results)} clips with virality scoring!")
        
        return results
    
    except Exception as e:
        error_msg = f"Auto clip generation failed: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"❌ {error_msg}")
        raise RuntimeError(error_msg)

def llm_smart_clips_v2(transcript, video_path, progress_callback=None):
    """Enhanced LLM clip generation with better prompting and scoring"""
    if not OLLAMA_AVAILABLE:
        if progress_callback:
            progress_callback(1.0, "Ollama not available, falling back to auto generation")
        return auto_generate_clips_v2(transcript, video_path, progress_callback)
    
    try:
        num_clips = config.get("clip_preferences.preferred_count", 4)
        min_dur = config.get("clip_preferences.min_duration", 60)
        max_dur = config.get("clip_preferences.max_duration", 180)
        
        # Determine target resolution based on output mode
        output_mode = config.get("output_mode", "long-form")
        if output_mode == "vertical":
            target_w, target_h = 1080, 1920
        elif output_mode == "long-form":
            target_w, target_h = 1920, 1080  # Long-form content
        else:
            target_w, target_h = 1920, 1080
        
        if progress_callback:
            progress_callback(0.1, "Preparing transcript for AI analysis...")
        
        # Create a more focused transcript for the LLM
        transcript_text = ""
        for i, seg in enumerate(transcript):
            transcript_text += f"[{format_time(seg['start'])} - {format_time(seg['end'])}] {seg['text']}\n"
        
        prompt = f"""You are a professional short-form video editor specializing in viral content creation. 

Analyze this transcript and extract exactly {num_clips} clips that would perform best on social media platforms like TikTok, Instagram Reels, and YouTube Shorts.

REQUIREMENTS:
- Each clip must be {min_dur}-{max_dur} seconds long
- Focus on hooks, surprising moments, valuable insights, or emotional peaks
- Prioritize clips with strong openings that grab attention immediately
- Look for complete thoughts/stories, not fragments
- Consider cliffhangers, reveals, and quotable moments

OUTPUT FORMAT (JSON only, no explanations):
[
  {{"start": 12.5, "end": 67.2, "reason": "Strong hook with surprising statistics", "virality_score": 85}},
  {{"start": 134.0, "end": 189.3, "reason": "Emotional story with clear lesson", "virality_score": 92}}
]

TRANSCRIPT:
{transcript_text}"""

        if progress_callback:
            progress_callback(0.3, "AI analyzing content for viral potential...")
        
        try:
            response = ollama.chat(
                model="llama3.2", 
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3}  # Lower temperature for more consistent JSON
            )
            
            # Extract JSON from response
            response_text = response["message"]["content"].strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                clips_data = json.loads(json_match.group())
            else:
                clips_data = json.loads(response_text)
            
        except Exception as e:
            print(f"LLM processing failed: {e}, falling back to auto generation")
            return auto_generate_clips_v2(transcript, video_path, progress_callback)
        
        if progress_callback:
            progress_callback(0.5, f"AI selected {len(clips_data)} clips, generating videos...")
        
        # Create output directory
        output_dir = "openshorts_clips"
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for idx, clip in enumerate(clips_data[:num_clips]):
            if progress_callback:
                progress = 0.5 + (idx / len(clips_data)) * 0.5
                progress_callback(progress, f"Creating AI clip {idx+1}/{len(clips_data)}...")
            
            # Extract segments for this clip (used for both ASS and SRT)
            clip_segments = []
            for seg in transcript:
                if seg["start"] >= clip["start"] and seg["end"] <= clip["end"]:
                    adjusted_seg = {
                        "start": seg["start"] - clip["start"],
                        "end": seg["end"] - clip["start"],
                        "text": seg["text"],
                        "words": []
                    }
                    # Adjust word timestamps if available  
                    if "words" in seg and seg["words"]:
                        for word in seg["words"]:
                            if word["start"] >= clip["start"] and word["end"] <= clip["end"]:
                                adjusted_seg["words"].append({
                                    "start": word["start"] - clip["start"],
                                    "end": word["end"] - clip["start"],
                                    "text": word["text"]
                                })
                    clip_segments.append(adjusted_seg)
                
            # Generate clip path first
            out_path = os.path.join(output_dir, f"clip_{idx+1:02d}.mp4")
            
            # Create caption files if enabled
            if config.get("animated_captions", False) or config.get("export_settings.export_ass", True):
                ass_path = out_path.replace('.mp4', '.ass')
                if clip_segments:
                    create_advanced_captions(
                        clip_segments, 
                        ass_path, 
                        config.get("caption_style", {}),
                        (target_w, target_h)
                    )
            
            # Create SRT file if enabled
            if config.get("export_settings.export_srt", False):
                srt_path = out_path.replace('.mp4', '.srt')
                if clip_segments:
                    srt_style = config.get("export_settings.srt_style", "simple")
                    create_srt_file(clip_segments, srt_path, srt_style)
            create_smart_clip(video_path, clip["start"], clip["end"], out_path, progress_callback, clip_segments)
            
            # Create thumbnail
            thumb_path = generate_thumbnail(video_path, clip["start"] + (clip["end"] - clip["start"])/2, out_path.replace('.mp4', '_thumb.jpg'))
            
            virality_score = clip.get("virality_score", 0)
            reason = clip.get("reason", "AI-selected highlight")
            
            clip_info = (
                out_path,
                f"AI Clip {idx+1} • Score: {virality_score}/100\n"
                f"{format_time(clip['start'])}–{format_time(clip['end'])}\n"
                f"Reason: {reason}"
            )
            results.append(clip_info)
        
        if progress_callback:
            progress_callback(1.0, f"✅ AI generated {len(results)} viral clips!")
        
        return results
    
    except Exception as e:
        error_msg = f"AI clip generation failed: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"❌ {error_msg}")
        raise RuntimeError(error_msg)

def generate_thumbnail(video_path, timestamp, output_path):
    """Generate thumbnail at specific timestamp"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get video duration to validate timestamp
        duration = get_video_duration(video_path)
        if duration and timestamp >= duration:
            # If timestamp is beyond video duration, use middle of video
            timestamp = duration / 2
            print(f"Timestamp {timestamp} beyond video duration {duration}, using middle timestamp")
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Thumbnail generation failed: {e.stderr}")
        return None
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None

def manual_clip_v2(video_path, start, end, progress_callback=None):
    """Enhanced manual clip creation with all v2 features"""
    try:
        if progress_callback:
            progress_callback(0.2, "Creating manual clip...")
        
        output_dir = "openshorts_clips"
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"manual_{format_time(start)}.mp4")
        
        # Generate subtitle files if we have a transcript in the state
        # Note: This would need to be enhanced to accept transcript data from the calling function
        
        create_smart_clip(video_path, start, end, out_path, progress_callback)
        
        # Generate thumbnail
        thumb_path = generate_thumbnail(video_path, start + (end - start)/2, out_path.replace('.mp4', '_thumb.jpg'))
        
        if progress_callback:
            progress_callback(1.0, "✅ Manual clip created!")
        
        return out_path
    except Exception as e:
        error_msg = f"Manual clip creation failed: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"❌ {error_msg}")
        raise RuntimeError(error_msg)

def export_full_transcript_srt(transcript, output_path, style="simple"):
    """
    Export the full transcript as an SRT file
    
    Args:
        transcript: Full transcript data from whisper
        output_path: Path to save the SRT file
        style: 'simple' or 'enhanced'
    """
    try:
        create_srt_file(transcript, output_path, style)
        return output_path
    except Exception as e:
        raise RuntimeError(f"Full transcript SRT export failed: {str(e)}")

def is_valid_video_url(url):
    """
    Check if the provided URL is a valid video URL that can be downloaded
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
        
    # Common video URL patterns
    video_domains = [
        'youtube.com', 'youtu.be', 'vimeo.com', 'tiktok.com', 'twitter.com', 'x.com',
        'instagram.com', 'facebook.com', 'twitch.tv', 'dailymotion.com',
        'rumble.com', 'bitchute.com', 'brighteon.com'
    ]
    
    return any(domain in url.lower() for domain in video_domains) and (url.startswith('http://') or url.startswith('https://'))

def download_video_from_url(url, progress_callback=None):
    """
    Download video from URL using yt-dlp
    
    Args:
        url: Video URL to download
        progress_callback: Optional callback for progress updates
    
    Returns:
        Path to downloaded video file
    """
    if not YTDLP_AVAILABLE:
        raise RuntimeError("yt-dlp is not installed. Please install it: pip install yt-dlp")
    
    if not is_valid_video_url(url):
        raise ValueError("Invalid video URL provided")
    
    try:
        if progress_callback:
            progress_callback(0.1, "Initializing video download...")
        
        # Create temporary download directory
        download_dir = tempfile.mkdtemp(prefix="openshorts_download_")
        
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    percent = d['downloaded_bytes'] / d['total_bytes']
                    progress_callback(0.1 + (percent * 0.8), f"Downloading: {percent*100:.1f}%")
                elif '_percent_str' in d:
                    progress_callback(0.5, f"Downloading: {d['_percent_str']}")
            elif progress_callback and d['status'] == 'finished':
                progress_callback(0.9, "Download complete, processing...")
        
        # Configure yt-dlp options for best quality video
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
            'progress_hooks': [progress_hook],
            'no_warnings': True,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            video_path = None
            for file in os.listdir(download_dir):
                if file.lower().endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov')):
                    video_path = os.path.join(download_dir, file)
                    break
            
            if not video_path or not os.path.exists(video_path):
                raise RuntimeError("Downloaded video file not found")
            
            # Move to a more permanent location for processing
            final_path = os.path.join(tempfile.gettempdir(), f"openshorts_video_{int(time.time())}.mp4")
            shutil.move(video_path, final_path)
            
            # Clean up download directory
            shutil.rmtree(download_dir, ignore_errors=True)
            
            if progress_callback:
                progress_callback(1.0, "✅ Video downloaded successfully!")
            
            return final_path, info.get('title', 'Downloaded Video')
            
    except Exception as e:
        # Clean up on error
        if 'download_dir' in locals() and os.path.exists(download_dir):
            shutil.rmtree(download_dir, ignore_errors=True)
        
        error_msg = f"Video download failed: {str(e)}"
        if "not supported" in str(e).lower():
            error_msg = "This video URL is not supported. Try a direct video link or supported platform."
        elif "private" in str(e).lower() or "unavailable" in str(e).lower():
            error_msg = "This video is private or unavailable for download."
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            error_msg = "Network error. Please check your internet connection and try again."
        
        if progress_callback:
            progress_callback(1.0, f"❌ {error_msg}")
        
        raise RuntimeError(error_msg)

def batch_process_videos(video_files, progress_callback=None):
    """Process multiple videos automatically"""
    results = []
    total_files = len(video_files)
    
    for idx, video_file in enumerate(video_files):
        if progress_callback:
            progress_callback(idx / total_files, f"Processing video {idx+1}/{total_files}: {os.path.basename(video_file.name)}")
        
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_batch_{idx}_{os.path.basename(video_file.name)}"
            with open(temp_path, 'wb') as f:
                f.write(video_file.read())
            
            # Transcribe
            transcript = transcribe_with_progress(temp_path)
            
            # Generate clips
            clips = auto_generate_clips_v2(transcript, temp_path)
            
            results.extend(clips)
            
            # Cleanup
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Batch processing failed for {video_file.name}: {e}")
            continue
    
    if progress_callback:
        progress_callback(1.0, f"✅ Batch processing complete! Generated {len(results)} clips")
    
    return results

def quick_generate_shorts(video_path, transcript, progress_callback=None):
    """One-click generate optimized clips with current duration preferences"""
    # Temporarily set config for optimal generation
    original_mode = config.get("output_mode")
    original_captions = config.get("animated_captions")
    original_count = config.get("clip_preferences.preferred_count")
    original_talking_head = config.get("talking_head_mode")
    
    try:
        # Set optimal settings while respecting user's duration preferences
        config.set("output_mode", "vertical")  # Shorts format
        config.set("animated_captions", True)  # Always add captions for shorts
        config.set("clip_preferences.preferred_count", 6)  # Reasonable number for longer clips
        config.set("talking_head_mode", True)  # Better for vertical format
        
        # Keep user's duration preferences - don't override them
        # This respects whether they want 60+ second clips or shorter ones
        
        if progress_callback:
            progress_callback(0.1, "Generating optimized clips with your duration settings...")
        
        # Generate clips with AI if available, otherwise auto
        if OLLAMA_AVAILABLE:
            clips = llm_smart_clips_v2(transcript, video_path, progress_callback)
        else:
            clips = auto_generate_clips_v2(transcript, video_path, progress_callback)
        
        return clips
        
    finally:
        # Restore original settings
        config.set("output_mode", original_mode)
        config.set("animated_captions", original_captions)
        config.set("clip_preferences.preferred_count", original_count)
        config.set("talking_head_mode", original_talking_head)

# UI Components
def create_ui():
    """Create the modern tabbed Gradio interface"""
    
    with gr.Blocks(
        title="OpenShorts v2 - Local Video Clipper"
    ) as demo:
        
        # Header
        gr.Markdown("""
        # 🎬 OpenShorts v2
        **Your Personal AI Video Editor** • 100% Local • No Internet Required
        
        Transform long videos into engaging shorts with intelligent cropping, animated captions, and AI-powered clip selection.
        """)
        
        # Global state variables
        video_state = gr.State()
        transcript_state = gr.State()
        
        with gr.Tabs():
            
            # UPLOAD & TRANSCRIBE TAB
            with gr.Tab("📹 Upload & Transcribe", id=0):
                gr.Markdown("### Upload your video and generate transcript")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### Upload Method")
                        upload_method = gr.Radio(
                            choices=["File Upload", "Video URL"],
                            label="Choose input method",
                            value="File Upload",
                            interactive=True
                        )
                        
                        video_input = gr.Video(
                            label="Drop your video here",
                            height=400,
                            interactive=True,
                            visible=True
                        )
                        
                        url_input = gr.Textbox(
                            label="Video URL",
                            placeholder="https://youtube.com/watch?v=...",
                            info="Supports YouTube, TikTok, Twitter/X, Instagram, Vimeo, and more",
                            interactive=True,
                            visible=False
                        )
                        
                        with gr.Row():
                            transcribe_btn = gr.Button(
                                "🎯 Start Transcription",
                                variant="primary",
                                size="lg"
                            )
                            download_btn = gr.Button(
                                "⬇️ Download & Transcribe",
                                variant="primary", 
                                size="lg",
                                visible=False
                            )
                            batch_upload = gr.File(
                                label="Batch Upload (Multiple Videos)",
                                file_count="multiple",
                                file_types=["video"]
                            )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### Next Steps")
                        gr.Markdown("1. **Upload & transcribe** your video")
                        gr.Markdown("2. Go to **Generate Clips** tab")  
                        gr.Markdown("3. Choose generation method")
                        gr.Markdown("4. Adjust settings as needed")
                        gr.Markdown("5. Generate your clips!")
                
                # Progress and status
                transcribe_progress = gr.Progress()
                transcribe_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    placeholder="Upload a video to begin..."
                )
                
                # Transcript display
                transcript_display = gr.DataFrame(
                    headers=["Start", "End", "Text", "Score"],
                    label="📝 Full Transcript",
                    interactive=True,
                    wrap=True
                )
                
                with gr.Row():
                    export_srt_btn = gr.Button(
                        "📄 Export Full Transcript as SRT",
                        variant="secondary",
                        size="sm"
                    )
                    export_status = gr.Textbox(
                        label="Export Status",
                        interactive=False,
                        placeholder="Transcribe video first, then export..."
                    )
            
            # TRANSCRIPT & MANUAL TAB
            with gr.Tab("✂️ Manual Clips", id=1):
                gr.Markdown("### Create custom clips from transcript")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Click any transcript row to auto-fill times**")
                        
                        with gr.Row():
                            manual_start = gr.Number(
                                label="Start Time (seconds)",
                                value=0,
                                minimum=0
                            )
                            manual_end = gr.Number(
                                label="End Time (seconds)",
                                value=60,
                                minimum=0
                            )
                        
                        with gr.Row():
                            preview_btn = gr.Button("👁️ Preview", size="sm")
                            create_manual_btn = gr.Button(
                                "Create Manual Clip",
                                variant="primary"
                            )
                        
                        manual_status = gr.Textbox(
                            label="Status",
                            interactive=False
                        )
                    
                    with gr.Column():
                        gr.Markdown("**Transcript Navigator**")
                        transcript_selector = gr.DataFrame(
                            headers=["Time", "Duration", "Text"],
                            label="Click to select",
                            interactive=True
                        )
            
            # AUTO CLIPS TAB
            with gr.Tab("🤖 Generate Clips", id=2):
                gr.Markdown("### Choose your generation method")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📋 **Use Your Settings**")
                        gr.Markdown("*Generates clips according to your preferences below*")
                        
                        auto_generate_btn = gr.Button(
                            "🛠️ Generate with My Settings",
                            variant="primary",
                            size="lg"
                        )
                        
                        if OLLAMA_AVAILABLE:
                            ai_generate_btn = gr.Button(
                                "🧠 AI Generate with My Settings",
                                variant="secondary",
                                size="lg"
                            )
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### ⚡ **Quick Presets**") 
                        gr.Markdown("*Uses optimized settings for specific formats*")
                        
                        quick_shorts_btn = gr.Button(
                            "📱 Quick Vertical Shorts",
                            variant="secondary",
                            size="lg"
                        )
                        gr.Markdown("*Creates 6 vertical clips with your duration preferences*")
                        
                        auto_progress = gr.Progress()
                        auto_status = gr.Textbox(
                            label="Generation Status",
                            interactive=False
                        )
                    
                    with gr.Column():
                        gr.Markdown("### ⚙️ Your Clip Preferences")
                        gr.Markdown("*These settings are used by 'Generate with My Settings' above*")
                        with gr.Group():
                            clip_count = gr.Slider(
                                label="Number of clips",
                                minimum=2,
                                maximum=15,
                                value=config.get("clip_preferences.preferred_count", 4),
                                step=1,
                                info="Fewer, higher-quality clips for long-form content"
                            )
                            
                            min_duration = gr.Slider(
                                label="Minimum duration (seconds)",
                                minimum=30,
                                maximum=120,
                                value=config.get("clip_preferences.min_duration", 60),
                                step=5,
                                info="Longer clips provide better context and engagement"
                            )
                            
                            max_duration = gr.Slider(
                                label="Maximum duration (seconds)",
                                minimum=60,
                                maximum=300,
                                value=config.get("clip_preferences.max_duration", 180),
                                step=10,
                                info="Up to 5 minutes for comprehensive segments"
                            )
                            
                            hook_first = gr.Checkbox(
                                label="Prioritize strong openings",
                                value=config.get("clip_preferences.hook_first_mode", True)
                            )
            
            # SETTINGS TAB
            with gr.Tab("⚙️ Settings", id=3):
                gr.Markdown("### Global Settings")
                gr.Markdown("*These settings are used when you click 'Generate with My Settings' in the Generate Clips tab*")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Output Format**")
                        output_mode = gr.Radio(
                            choices=["long-form", "horizontal", "vertical"],
                            label="Video Orientation", 
                            value=config.get("output_mode", "long-form"),
                            info="Long-form: 1920x1080 (Optimized for longer clips) | Horizontal: 1920x1080 | Vertical: 1080x1920 (Shorts)"
                        )
                        
                        talking_head_mode = gr.Checkbox(
                            label="Talking Head Mode (Smart Crop)",
                            value=config.get("talking_head_mode", False),
                            info="Intelligently crop for face-centered vertical videos"
                        )
                        
                        gr.Markdown("**Animated Captions**")
                        animated_captions = gr.Checkbox(
                            label="Enable Animated Captions",
                            value=config.get("animated_captions", False),
                            info="Professional word-by-word highlighting"
                        )
                        
                        with gr.Group():
                            caption_style_preset = gr.Radio(
                                choices=["tiktok", "youtube", "professional", "minimal"],
                                label="Caption Style",
                                value=config.get("caption_style.style", "tiktok"),
                                info="TikTok: Bold & bouncy | YouTube: Clean & sliding | Professional: Elegant | Minimal: Subtle"
                            )
                            
                            caption_font_size = gr.Slider(
                                label="Caption Font Size",
                                minimum=18,
                                maximum=48,
                                value=config.get("caption_style.font_size", 28),
                                step=2
                            )
                            
                            caption_position = gr.Radio(
                                choices=["bottom", "top", "center"],
                                label="Caption Position",
                                value=config.get("caption_style.position", "bottom")
                            )
                            
                            with gr.Row():
                                caption_background = gr.Checkbox(
                                    label="Background Box",
                                    value=config.get("caption_style.background_box", True)
                                )
                                word_emphasis = gr.Checkbox(
                                    label="Word Emphasis Effects",
                                    value=config.get("caption_style.word_emphasis", True),
                                    info="Bounce/slide effects on words"
                                )
                    
                    with gr.Column():
                        gr.Markdown("**Background Music**")
                        bg_music_enabled = gr.Checkbox(
                            label="Add Background Music",
                            value=config.get("background_music.enabled", False)
                        )
                        
                        music_folder = gr.Textbox(
                            label="Music Folder Path",
                            value=config.get("background_music.music_folder", ""),
                            placeholder="/path/to/music/folder",
                            info="Folder containing .mp3/.wav files"
                        )
                        
                        music_volume = gr.Slider(
                            label="Music Volume",
                            minimum=0.05,
                            maximum=0.5,
                            value=config.get("background_music.volume", 0.15),
                            step=0.05
                        )
                        
                        gr.Markdown("**Subtitle Export**")
                        export_srt = gr.Checkbox(
                            label="Export SRT Files",
                            value=config.get("export_settings.export_srt", False),
                            info="Generate standard SRT subtitle files alongside videos"
                        )
                        
                        export_ass = gr.Checkbox(
                            label="Export ASS Files",
                            value=config.get("export_settings.export_ass", True),
                            info="Generate advanced ASS subtitle files (with animations)"
                        )
                        
                        srt_style = gr.Radio(
                            choices=["simple", "enhanced"],
                            label="SRT Style",
                            value=config.get("export_settings.srt_style", "simple"),
                            info="Simple: Plain text | Enhanced: Basic formatting and line breaks"
                        )
                        
                        gr.Markdown("**Stock Videos (B-Roll)**")
                        stock_enabled = gr.Checkbox(
                            label="Enable Stock Video Integration",
                            value=config.get("stock_video.enabled", False),
                            info="Automatically add B-roll footage at emphasis points"
                        )
                        
                        stock_folder = gr.Textbox(
                            label="Stock Videos Folder Path",
                            value=config.get("stock_video.folder_path", ""),
                            placeholder="/path/to/stock/videos",
                            info="Folder containing MP4/MOV stock footage files"
                        )
                        
                        stock_usage = gr.Slider(
                            label="Usage Percentage",
                            minimum=10,
                            maximum=80,
                            value=config.get("stock_video.usage_percentage", 30),
                            step=5,
                            info="Percentage of clip duration that uses stock footage"
                        )
                        
                        stock_selection = gr.Radio(
                            choices=["random", "manual"],
                            label="Selection Mode",
                            value=config.get("stock_video.selection_mode", "random"),
                            info="Random: Auto-select | Manual: User chooses per clip"
                        )
                        
                        gr.Markdown("**System Info**")
                        with gr.Group():
                            gr.Markdown(f"""
                            - FFmpeg: {'✅ Available' if shutil.which('ffmpeg') else '❌ Not found'}
                            - yt-dlp: {'✅ Available' if YTDLP_AVAILABLE else '❌ Not installed'}
                            - Ollama: {'✅ Available' if OLLAMA_AVAILABLE else '❌ Not installed'}
                            - OpenCV: {'✅ Available' if OPENCV_AVAILABLE else '❌ Not installed'}
                            - MoviePy: {'✅ Available' if MOVIEPY_AVAILABLE else '❌ Not installed'}
                            """)
                        
                        save_settings_btn = gr.Button(
                            "💾 Save Settings",
                            variant="primary"
                        )
                        settings_status = gr.Textbox(
                            label="Settings Status",
                            interactive=False
                        )
            
            # OUTPUT TAB
            with gr.Tab("🎥 Generated Clips", id=4):
                gr.Markdown("### Your generated clips")
                
                with gr.Row():
                    refresh_gallery_btn = gr.Button("🔄 Refresh Gallery")
                    open_folder_btn = gr.Button("📁 Open Clips Folder")
                    clear_clips_btn = gr.Button("🗑️ Clear All Clips", variant="stop")
                
                clips_gallery = gr.Gallery(
                    label="Generated Clips",
                    show_label=True,
                    elem_id="clips_gallery",
                    columns=3,
                    rows=3,
                    height="auto",
                    preview=True,
                    allow_preview=True
                )
                
                generation_log = gr.Textbox(
                    label="Generation Log",
                    lines=5,
                    max_lines=10,
                    interactive=False,
                    placeholder="Clip generation activity will appear here..."
                )
        
        # Event Handlers
        
        def handle_transcribe(video, progress=gr.Progress()):
            """Handle video transcription with progress"""
            if not video:
                return None, None, "Please upload a video first!", None
            
            try:
                def progress_callback(pct, msg):
                    progress(pct, desc=msg)
                
                transcript = transcribe_with_progress(video, progress_callback)
                
                # Format for display
                display_data = []
                for seg in transcript:
                    score = calculate_virality_score(seg["text"])
                    display_data.append([
                        format_time(seg["start"]),
                        format_time(seg["end"]),
                        seg["text"][:100] + "..." if len(seg["text"]) > 100 else seg["text"],
                        f"{score}/100"
                    ])
                
                return (
                    display_data,
                    transcript,
                    f"✅ Transcription complete! {len(transcript)} segments processed.",
                    video
                )
            
            except Exception as e:
                return None, None, f"❌ Transcription failed: {str(e)}", None
        
        def handle_url_download(url, progress=gr.Progress()):
            """Handle video URL download and transcription"""
            if not url or not url.strip():
                return None, None, "Please enter a video URL!", None
            
            if not YTDLP_AVAILABLE:
                return None, None, "❌ yt-dlp not installed. Run: pip install yt-dlp", None
                
            try:
                def progress_callback(pct, msg):
                    progress(pct, desc=msg)
                
                # Download video
                video_path, video_title = download_video_from_url(url, progress_callback)
                
                # Transcribe downloaded video
                progress_callback(0.1, "Starting transcription...")
                transcript = transcribe_with_progress(video_path, 
                    lambda pct, msg: progress_callback(0.1 + pct * 0.9, msg))
                
                # Format for display
                display_data = []
                for seg in transcript:
                    score = calculate_virality_score(seg["text"])
                    display_data.append([
                        format_time(seg["start"]),
                        format_time(seg["end"]),
                        seg["text"][:100] + "..." if len(seg["text"]) > 100 else seg["text"],
                        f"{score}/100"
                    ])
                
                return (
                    display_data,
                    transcript,
                    f"✅ Downloaded '{video_title}' and transcribed {len(transcript)} segments!",
                    video_path
                )
                
            except Exception as e:
                return None, None, f"❌ {str(e)}", None
        
        def toggle_input_method(method):
            """Toggle between file upload and URL input"""
            if method == "File Upload":
                return (
                    gr.update(visible=True),   # video_input
                    gr.update(visible=False),  # url_input
                    gr.update(visible=True),   # transcribe_btn
                    gr.update(visible=False)   # download_btn
                )
            else:  # Video URL
                return (
                    gr.update(visible=False),  # video_input
                    gr.update(visible=True),   # url_input
                    gr.update(visible=False),  # transcribe_btn
                    gr.update(visible=True)    # download_btn
                )
        
        def handle_auto_clips(transcript, video, clip_count, min_dur, max_dur, hook_first, progress=gr.Progress()):
            """Handle automatic clip generation"""
            if not transcript or not video:
                return None, "Please transcribe video first!"
            
            try:
                # Update config with current settings
                config.set("clip_preferences.preferred_count", int(clip_count))
                config.set("clip_preferences.min_duration", int(min_dur))
                config.set("clip_preferences.max_duration", int(max_dur))
                config.set("clip_preferences.hook_first_mode", bool(hook_first))
                
                def progress_callback(pct, msg):
                    progress(pct, desc=msg)
                
                clips = auto_generate_clips_v2(transcript, video, progress_callback)
                return clips, f"✅ Generated {len(clips)} clips with virality scoring!"
            
            except Exception as e:
                return None, f"❌ Auto generation failed: {str(e)}"
        
        def handle_ai_clips(transcript, video, clip_count, progress=gr.Progress()):
            """Handle AI-powered clip generation"""
            if not transcript or not video:
                return None, "Please transcribe video first!"
            
            config.set("clip_preferences.preferred_count", int(clip_count))
            
            def progress_callback(pct, msg):
                progress(pct, desc=msg)
            
            clips = llm_smart_clips_v2(transcript, video, progress_callback)
            return clips, f"✅ AI generated {len(clips)} viral clips!"
        
        def handle_manual_clip(video, start, end, progress=gr.Progress()):
            """Handle manual clip creation"""
            if not video:
                return None, "Please upload a video first!"
            
            def progress_callback(pct, msg):
                progress(pct, desc=msg)
            
            try:
                clip_path = manual_clip_v2(video, start, end, progress_callback)
                return [(clip_path, f"Manual {format_time(start)}–{format_time(end)}")], f"✅ Manual clip created!"
            except Exception as e:
                return None, f"❌ Manual clip failed: {str(e)}"
        
        def handle_export_full_transcript(transcript):
            """Handle full transcript SRT export"""
            if not transcript:
                return "Please transcribe a video first!"
            
            try:
                output_path = os.path.join("openshorts_clips", "full_transcript.srt")
                os.makedirs("openshorts_clips", exist_ok=True)
                
                srt_style = config.get("export_settings.srt_style", "simple")
                export_full_transcript_srt(transcript, output_path, srt_style)
                
                return f"✅ Full transcript exported to: {output_path}"
            except Exception as e:
                return f"❌ Export failed: {str(e)}"
        
        def handle_quick_shorts(video, transcript, progress=gr.Progress()):
            """Handle quick shorts generation"""
            if not video or not transcript:
                return None, "Please upload and transcribe a video first!"
            
            def progress_callback(pct, msg):
                progress(pct, desc=msg)
            
            try:
                clips = quick_generate_shorts(video, transcript, progress_callback)
                return clips, f"✅ Generated {len(clips)} optimized shorts!"
            except Exception as e:
                return None, f"❌ Quick shorts failed: {str(e)}"
        
        def save_user_settings(
            output_mode_val, talking_head_val, animated_captions_val,
            caption_style_preset_val, caption_font_size_val, caption_position_val, 
            caption_background_val, word_emphasis_val, bg_music_enabled_val, music_folder_val, music_volume_val,
            export_srt_val, export_ass_val, srt_style_val,
            stock_enabled_val, stock_folder_val, stock_usage_val, stock_selection_val
        ):
            """Save user settings to config"""
            try:
                config.set("output_mode", output_mode_val)
                config.set("talking_head_mode", talking_head_val)
                config.set("animated_captions", animated_captions_val)
                config.set("caption_style.style", caption_style_preset_val)
                config.set("caption_style.font_size", int(caption_font_size_val))
                config.set("caption_style.position", caption_position_val)
                config.set("caption_style.background_box", caption_background_val)
                config.set("caption_style.word_emphasis", word_emphasis_val)
                config.set("background_music.enabled", bg_music_enabled_val)
                config.set("background_music.music_folder", music_folder_val)
                config.set("background_music.volume", float(music_volume_val))
                config.set("export_settings.export_srt", export_srt_val)
                config.set("export_settings.export_ass", export_ass_val)
                config.set("export_settings.srt_style", srt_style_val)
                config.set("stock_video.enabled", stock_enabled_val)
                config.set("stock_video.folder_path", stock_folder_val)
                config.set("stock_video.usage_percentage", int(stock_usage_val))
                config.set("stock_video.selection_mode", stock_selection_val)
                
                return "✅ Settings saved successfully!"
            except Exception as e:
                return f"❌ Settings save failed: {str(e)}"
        
        def open_clips_folder():
            """Open the clips output folder"""
            clips_dir = os.path.abspath("openshorts_clips")
            if os.path.exists(clips_dir):
                subprocess.run(["open", clips_dir])  # macOS
                return f"Opened folder: {clips_dir}"
            else:
                return "No clips folder found. Generate some clips first!"
        
        def clear_all_clips():
            """Clear all generated clips"""
            clips_dir = "openshorts_clips"
            if os.path.exists(clips_dir):
                shutil.rmtree(clips_dir)
                return "✅ All clips cleared!"
            return "No clips to clear."
        
        # Wire up events
        
        upload_method.change(
            fn=toggle_input_method,
            inputs=[upload_method],
            outputs=[video_input, url_input, transcribe_btn, download_btn]
        )
        
        transcribe_btn.click(
            fn=handle_transcribe,
            inputs=[video_input],
            outputs=[transcript_display, transcript_state, transcribe_status, video_state]
        )
        
        download_btn.click(
            fn=handle_url_download,
            inputs=[url_input],
            outputs=[transcript_display, transcript_state, transcribe_status, video_state]
        )
        
        export_srt_btn.click(
            fn=handle_export_full_transcript,
            inputs=[transcript_state],
            outputs=[export_status]
        )
        
        auto_generate_btn.click(
            fn=handle_auto_clips,
            inputs=[transcript_state, video_state, clip_count, min_duration, max_duration, hook_first],
            outputs=[clips_gallery, auto_status]
        )
        
        if OLLAMA_AVAILABLE:
            ai_generate_btn.click(
                fn=handle_ai_clips,
                inputs=[transcript_state, video_state, clip_count],
                outputs=[clips_gallery, auto_status]
            )
        
        create_manual_btn.click(
            fn=handle_manual_clip,
            inputs=[video_state, manual_start, manual_end],
            outputs=[clips_gallery, manual_status]
        )
        
        quick_shorts_btn.click(
            fn=handle_quick_shorts,
            inputs=[video_state, transcript_state],
            outputs=[clips_gallery, transcribe_status]
        )
        
        save_settings_btn.click(
            fn=save_user_settings,
            inputs=[
                output_mode, talking_head_mode, animated_captions,
                caption_style_preset, caption_font_size, caption_position, 
                caption_background, word_emphasis, bg_music_enabled, music_folder, music_volume,
                export_srt, export_ass, srt_style,
                stock_enabled, stock_folder, stock_usage, stock_selection
            ],
            outputs=[settings_status]
        )
        
        open_folder_btn.click(
            fn=open_clips_folder,
            outputs=[generation_log]
        )
        
        clear_clips_btn.click(
            fn=clear_all_clips,
            outputs=[generation_log]
        )
    
    return demo

def main():
    """Main entry point for OpenShorts application"""
    print("🎬 Starting OpenShorts v2...")
    
    # Check system requirements
    if not shutil.which('ffmpeg'):
        print("❌ FFmpeg not found! Please install FFmpeg first:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")  
        print("  Windows: winget install ffmpeg")
        exit(1)
    
    print("✅ System check passed")
    print(f"✅ Ollama: {'Available' if OLLAMA_AVAILABLE else 'Not available'}")
    print(f"✅ OpenCV: {'Available' if OPENCV_AVAILABLE else 'Not available'}")
    
    # Create output directory
    os.makedirs("openshorts_clips", exist_ok=True)
    
    # Launch UI
    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,  # Use Gradio's default port
        share=False,
        show_error=True,
        quiet=False,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate"
        )
    )

# Main execution
if __name__ == "__main__":
    main()
