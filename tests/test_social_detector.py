"""
Tests for Social Media URL Detector.
"""

import pytest
from src.domain.content import SocialPlatform
from src.infrastructure.social_detector import SocialDetector


def test_facebook_detection():
    detector = SocialDetector()
    
    # Valid Facebook URLs
    assert detector.detect("https://www.facebook.com/zuck/posts/10114136427387341").is_social
    assert detector.detect("https://www.facebook.com/zuck/posts/10114136427387341").platform == SocialPlatform.FACEBOOK
    assert detector.detect("https://fb.watch/123456").is_social
    assert detector.detect("https://fb.watch/123456").platform == SocialPlatform.FACEBOOK
    
    # Invalid
    assert not detector.detect("https://example.com").is_social


def test_threads_detection():
    detector = SocialDetector()
    
    # Valid Threads URLs
    assert detector.detect("https://www.threads.net/@zuck").is_social
    assert detector.detect("https://www.threads.net/@zuck").platform == SocialPlatform.THREADS
    assert detector.detect("https://www.threads.net/@zuck/post/CuZsgfWLyiI").is_social
    assert detector.detect("https://www.threads.net/@zuck/post/CuZsgfWLyiI").platform == SocialPlatform.THREADS
    
    # Short URLs or variations
    assert detector.detect("https://threads.net/@zuck").is_social
    
    # Invalid
    assert not detector.detect("https://instagram.com/zuck").is_social 
