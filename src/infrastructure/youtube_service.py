"""
Infrastructure Layer: YouTube Service

Extracts video information and captions from YouTube videos using yt-dlp.
"""

import asyncio
import re
from typing import Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running sync yt-dlp calls
_executor = ThreadPoolExecutor(max_workers=2)


@dataclass
class YouTubeVideoInfo:
    """YouTube video information."""
    video_id: str
    title: str
    description: str
    channel_name: str
    duration: str  # Formatted as "HH:MM:SS" or "MM:SS"
    duration_seconds: int
    thumbnail_url: Optional[str] = None
    view_count: Optional[int] = None
    captions: Optional[str] = None  # Extracted captions/subtitles
    has_captions: bool = False


class YouTubeService:
    """
    Extracts video information and captions from YouTube.
    
    Uses yt-dlp for reliable video info extraction.
    Prioritizes Traditional Chinese (zh-TW) captions, falls back to auto-generated.
    """

    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'),
    ]

    # Caption language priority (Traditional Chinese first)
    CAPTION_LANGS = ['zh-TW', 'zh-Hant', 'zh', 'zh-Hans', 'en', 'en-US']

    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        for pattern in cls.YOUTUBE_PATTERNS:
            match = pattern.search(url)
            if match:
                return match.group(1)
        return None

    @classmethod
    def is_youtube_url(cls, url: str) -> bool:
        """Check if URL is a valid YouTube video URL."""
        return cls.extract_video_id(url) is not None

    async def get_video_info(self, url: str) -> Optional[YouTubeVideoInfo]:
        """
        Get video information and captions from YouTube.
        
        Args:
            url: YouTube video URL
            
        Returns:
            YouTubeVideoInfo with video details and captions (if available)
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            print(f"⚠️ [YouTube] Invalid YouTube URL: {url}")
            return None

        print(f"🎬 [YouTube] Fetching video info for: {video_id}")

        try:
            # Run yt-dlp in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(_executor, self._fetch_video_info, url)
            
            if not info:
                return None

            # Try to get captions
            captions = await loop.run_in_executor(
                _executor, 
                self._fetch_captions, 
                url, 
                info.get('subtitles', {}),
                info.get('automatic_captions', {})
            )

            # Format duration
            duration_seconds = info.get('duration', 0) or 0
            duration_str = self._format_duration(duration_seconds)

            video_info = YouTubeVideoInfo(
                video_id=video_id,
                title=info.get('title', 'Unknown Title'),
                description=info.get('description', '') or '',
                channel_name=info.get('uploader', info.get('channel', 'Unknown Channel')),
                duration=duration_str,
                duration_seconds=duration_seconds,
                thumbnail_url=info.get('thumbnail'),
                view_count=info.get('view_count'),
                captions=captions,
                has_captions=bool(captions)
            )

            print(f"✅ [YouTube] Video info fetched: {video_info.title[:50]}...")
            print(f"   Duration: {video_info.duration}, Has Captions: {video_info.has_captions}")

            return video_info

        except Exception as e:
            print(f"❌ [YouTube] Error fetching video info: {e}")
            return None

    def _fetch_video_info(self, url: str) -> Optional[dict]:
        """Synchronously fetch video info using yt-dlp."""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': self.CAPTION_LANGS,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
                
        except Exception as e:
            print(f"❌ [YouTube] yt-dlp error: {e}")
            return None

    def _fetch_captions(
        self, 
        url: str, 
        subtitles: dict, 
        automatic_captions: dict
    ) -> Optional[str]:
        """
        Fetch captions/subtitles for the video.
        
        Priority:
        1. Manual subtitles in zh-TW
        2. Manual subtitles in zh/en
        3. Auto-generated subtitles in zh-TW
        4. Auto-generated subtitles in zh/en
        """
        try:
            import yt_dlp

            # Check for available caption languages
            available_manual = list(subtitles.keys()) if subtitles else []
            available_auto = list(automatic_captions.keys()) if automatic_captions else []
            
            print(f"   Manual captions available: {available_manual}")
            print(f"   Auto captions available: {available_auto[:5]}...")  # Limit log

            # Find best caption language
            caption_url = None
            caption_lang = None
            
            # Try manual subtitles first
            for lang in self.CAPTION_LANGS:
                if lang in subtitles:
                    caption_lang = lang
                    formats = subtitles[lang]
                    # Prefer vtt or srv3 format
                    for fmt in formats:
                        if fmt.get('ext') in ['vtt', 'srv3', 'ttml']:
                            caption_url = fmt.get('url')
                            break
                    if not caption_url and formats:
                        caption_url = formats[0].get('url')
                    if caption_url:
                        print(f"   Using manual captions: {caption_lang}")
                        break

            # Fall back to auto-generated
            if not caption_url:
                for lang in self.CAPTION_LANGS:
                    if lang in automatic_captions:
                        caption_lang = lang
                        formats = automatic_captions[lang]
                        for fmt in formats:
                            if fmt.get('ext') in ['vtt', 'srv3', 'ttml', 'json3']:
                                caption_url = fmt.get('url')
                                break
                        if not caption_url and formats:
                            caption_url = formats[0].get('url')
                        if caption_url:
                            print(f"   Using auto captions: {caption_lang}")
                            break

            if not caption_url:
                print(f"⚠️ [YouTube] No suitable captions found")
                return None

            # Download and parse captions
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.get(caption_url)
                response.raise_for_status()
                caption_text = response.text

            # Parse VTT/SRV3 format to plain text
            cleaned_text = self._parse_captions(caption_text)
            
            print(f"✅ [YouTube] Captions extracted: {len(cleaned_text)} chars")
            return cleaned_text

        except Exception as e:
            print(f"⚠️ [YouTube] Error fetching captions: {e}")
            return None

    def _parse_captions(self, raw_text: str) -> str:
        """Parse VTT/SRV3 caption format to plain text."""
        lines = raw_text.split('\n')
        text_lines = []
        seen_lines = set()  # Deduplicate
        
        for line in lines:
            line = line.strip()
            
            # Skip VTT headers and timestamps
            if not line:
                continue
            if line.startswith('WEBVTT'):
                continue
            if line.startswith('Kind:') or line.startswith('Language:'):
                continue
            if '-->' in line:  # Timestamp line
                continue
            if re.match(r'^\d+$', line):  # Line number
                continue
            if line.startswith('NOTE'):
                continue
            
            # Remove HTML tags
            line = re.sub(r'<[^>]+>', '', line)
            # Remove VTT position tags
            line = re.sub(r'align:start position:\d+%', '', line)
            
            line = line.strip()
            if line and line not in seen_lines:
                seen_lines.add(line)
                text_lines.append(line)
        
        return ' '.join(text_lines)

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS or MM:SS."""
        if seconds <= 0:
            return "0:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
