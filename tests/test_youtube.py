"""
Test Script: YouTube Service

Tests the YouTube video info and caption extraction via Apify.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.youtube_service import YouTubeService


async def test_youtube():
    print("=" * 60)
    print("YouTube Service Test")
    print("=" * 60)
    
    # Check API token
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ APIFY_API_TOKEN not set in environment")
        return
    
    print(f"✅ APIFY_API_TOKEN found: {api_token[:10]}...")
    
    # Initialize service
    service = YouTubeService(api_token=api_token)
    
    # Test URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short video for quick test
    print(f"\n📹 Testing URL: {test_url}")
    print("-" * 60)
    
    # Test URL extraction
    video_id = service.extract_video_id(test_url)
    print(f"   Video ID: {video_id}")
    
    # Fetch video info
    result = await service.get_video_info(test_url)
    
    if result:
        print("\n✅ SUCCESS! Video info retrieved:")
        print(f"   Title: {result.title}")
        print(f"   Channel: {result.channel_name}")
        print(f"   Duration: {result.duration}")
        print(f"   Views: {result.view_count}")
        print(f"   Likes: {result.likes}")
        print(f"   Has Captions: {result.has_captions}")
        
        if result.captions:
            print(f"\n📝 Captions preview (first 300 chars):")
            print(result.captions[:300])
    else:
        print("\n❌ FAILED: No result returned")


if __name__ == "__main__":
    asyncio.run(test_youtube())
