"""
Infrastructure Layer: YouTube Service

Extracts video information and captions from YouTube videos using Apify.
Uses streamers/youtube-scraper actor for reliable extraction.
"""

import asyncio
import re
from typing import Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from apify_client import ApifyClient

# Thread pool for running sync Apify calls
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
    likes: Optional[int] = None
    captions: Optional[str] = None  # Extracted captions/subtitles
    has_captions: bool = False


class YouTubeService:
    """
    Extracts video information and captions from YouTube using Apify.
    
    Uses streamers/youtube-scraper actor for reliable extraction.
    Handles IP blocking issues by leveraging Apify's proxy infrastructure.
    """

    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})'),
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'),
    ]

    # Apify actor for YouTube scraping
    YOUTUBE_ACTOR = "streamers/youtube-scraper"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize YouTube service with Apify.
        
        Args:
            api_token: Apify API token (uses APIFY_API_TOKEN env var if not provided)
        """
        import os
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        if self.api_token:
            self.client = ApifyClient(self.api_token)
        else:
            self.client = None
            print("⚠️ [YouTube] APIFY_API_TOKEN not set, YouTube scraping disabled")

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
        Get video information and captions from YouTube via Apify.
        
        Args:
            url: YouTube video URL
            
        Returns:
            YouTubeVideoInfo with video details and captions (if available)
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            print(f"⚠️ [YouTube] Invalid YouTube URL: {url}")
            return None

        if not self.client:
            print(f"❌ [YouTube] Apify client not initialized")
            return None

        print(f"🎬 [YouTube] Fetching video info via Apify for: {video_id}")

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                _executor, 
                self._run_apify_actor, 
                url
            )
            
            if not result:
                print(f"❌ [YouTube] Apify actor returned no results")
                return None

            # Parse the result
            video_info = self._parse_apify_result(result, video_id)
            
            if video_info:
                print(f"✅ [YouTube] Video info fetched: {video_info.title[:50]}...")
                print(f"   Duration: {video_info.duration}, Has Captions: {video_info.has_captions}")
            
            return video_info

        except Exception as e:
            print(f"❌ [YouTube] Error fetching video info: {e}")
            return None

    def _run_apify_actor(self, url: str) -> Optional[dict]:
        """Run Apify YouTube scraper actor synchronously."""
        try:
            print(f"🔍 [Apify] Running actor: {self.YOUTUBE_ACTOR}")
            
            # Input for streamers/youtube-scraper
            run_input = {
                "startUrls": [{"url": url}],
                "maxResults": 1,
                "downloadSubtitles": True,
                "subtitlesLanguage": "zh-TW,zh,en",  # Prefer Traditional Chinese
                "subtitlesFormat": "srt"
            }
            
            # Run the actor
            run = self.client.actor(self.YOUTUBE_ACTOR).call(run_input=run_input)
            
            # Poll for status
            run_id = run.get("id")
            print(f"[{self.YOUTUBE_ACTOR} runId:{run_id}] -> Status: {run.get('status')}")
            
            # Get results from dataset
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if items:
                print(f"✅ [Apify] Got {len(items)} result(s)")
                return items[0]
            else:
                print(f"⚠️ [Apify] No items in dataset")
                return None
                
        except Exception as e:
            print(f"❌ [Apify] Actor error: {e}")
            return None

    def _parse_apify_result(self, item: dict, video_id: str) -> Optional[YouTubeVideoInfo]:
        """Parse Apify result to YouTubeVideoInfo."""
        try:
            # Debug output
            print(f"🐛 [Debug] Apify item keys: {list(item.keys())}")
            
            # Extract basic info
            title = item.get("title", "Unknown Title")
            description = item.get("text", "") or item.get("description", "") or ""
            channel_name = item.get("channelName", "Unknown Channel")
            thumbnail_url = item.get("thumbnailUrl")
            view_count = item.get("viewCount")
            likes = item.get("likes")
            
            # Parse duration (format: "00:03:17" -> "3:17" or "1:23:45")
            duration_str = item.get("duration", "0:00")
            duration_seconds = self._parse_duration(duration_str)
            formatted_duration = self._format_duration(duration_seconds)
            
            # Extract captions/subtitles
            captions = None
            has_captions = False
            
            subtitles_data = item.get("subtitles")
            if subtitles_data and isinstance(subtitles_data, list) and len(subtitles_data) > 0:
                # Find best subtitle (prefer zh-TW, zh, then en)
                best_subtitle = self._find_best_subtitle(subtitles_data)
                if best_subtitle:
                    srt_content = best_subtitle.get("srt", "")
                    if srt_content:
                        captions = self._parse_srt_to_text(srt_content)
                        has_captions = bool(captions)
                        print(f"   Found {best_subtitle.get('language')} subtitles: {len(captions)} chars")
            
            return YouTubeVideoInfo(
                video_id=video_id,
                title=title,
                description=description,
                channel_name=channel_name,
                duration=formatted_duration,
                duration_seconds=duration_seconds,
                thumbnail_url=thumbnail_url,
                view_count=view_count,
                likes=likes,
                captions=captions,
                has_captions=has_captions
            )
            
        except Exception as e:
            print(f"❌ [YouTube] Error parsing result: {e}")
            return None

    def _find_best_subtitle(self, subtitles: list) -> Optional[dict]:
        """Find best subtitle by language preference."""
        # Language priority: Traditional Chinese > Chinese > English
        priority = ['zh-TW', 'zh-Hant', 'zh', 'zh-Hans', 'en', 'en-US']
        
        # Create lookup by language
        by_lang = {s.get('language', ''): s for s in subtitles}
        
        for lang in priority:
            if lang in by_lang:
                return by_lang[lang]
        
        # Return first available if no priority match
        return subtitles[0] if subtitles else None

    def _parse_srt_to_text(self, srt_content: str) -> str:
        """Parse SRT format subtitles to plain text."""
        lines = srt_content.split('\n')
        text_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, numbers, and timestamps
            if not line:
                continue
            if re.match(r'^\d+$', line):  # Line number
                continue
            if '-->' in line:  # Timestamp
                continue
            
            # Clean up the text
            line = line.strip()
            if line and line not in seen_lines:
                seen_lines.add(line)
                text_lines.append(line)
        
        return ' '.join(text_lines)

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string (HH:MM:SS or MM:SS) to seconds."""
        if not duration_str:
            return 0
        
        try:
            parts = duration_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return 0
        except:
            return 0

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
