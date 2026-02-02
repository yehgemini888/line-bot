"""
Manual verification script for social detection.
"""
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.social_detector import SocialDetector
from src.domain.content import SocialPlatform

def test_detector():
    detector = SocialDetector()
    print("Testing SocialDetector...")
    
    # Facebook
    fb_url = "https://www.facebook.com/zuck/posts/10114136427387341"
    res = detector.detect(fb_url)
    if res.is_social and res.platform == SocialPlatform.FACEBOOK:
        print(f"✅ Facebook detection: PASS ({fb_url})")
    else:
        print(f"❌ Facebook detection: FAIL ({fb_url}) -> {res}")

    # Threads
    th_url = "https://www.threads.net/@zuck/post/CuZsgfWLyiI"
    res = detector.detect(th_url)
    if res.is_social and res.platform == SocialPlatform.THREADS:
        print(f"✅ Threads detection: PASS ({th_url})")
    else:
        print(f"❌ Threads detection: FAIL ({th_url}) -> {res}")

    # Invalid
    inv_url = "https://example.com"
    res = detector.detect(inv_url)
    if not res.is_social:
        print(f"✅ Invalid URL detection: PASS ({inv_url})")
    else:
        print(f"❌ Invalid URL detection: FAIL ({inv_url}) -> {res}")

if __name__ == "__main__":
    test_detector()
