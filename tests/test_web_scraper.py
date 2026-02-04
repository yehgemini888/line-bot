"""
Test Script: Web Scraper

Tests the web scraper's ability to fetch and parse web page content.
Includes both SSR and SPA website tests.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.web_scraper import WebScraper


async def test_web_scraper():
    print("=" * 60)
    print("Web Scraper Test (with Jina Reader Fallback)")
    print("=" * 60)
    
    scraper = WebScraper()
    
    # Test URLs - mix of SSR and SPA sites
    test_urls = [
        ("中央社新聞 (SSR)", "https://www.cna.com.tw/news/aloc/202602030165.aspx"),
        ("Zentropy (SPA/Next.js)", "https://zentropy.cc"),
        ("Wikipedia (SSR)", "https://zh.wikipedia.org/wiki/Python"),
    ]
    
    results = []
    
    for name, url in test_urls:
        print(f"\n📰 Testing: {name}")
        print(f"   URL: {url}")
        print("-" * 60)
        
        result = await scraper.scrape(url)
        
        if result.success:
            jina_note = " (via Jina)" if result.used_jina else " (direct)"
            print(f"   ✅ Title: {result.title[:50] if result.title else 'N/A'}...{jina_note}")
            print(f"   📝 Content length: {len(result.text_content)} chars")
            print(f"   Preview: {result.text_content[:150].replace(chr(10), ' ')}...")
            results.append((name, True, result.used_jina))
        else:
            print(f"   ❌ Failed: {result.error_message}")
            results.append((name, False, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    for name, success, used_jina in results:
        status = "✅ PASS" if success else "❌ FAIL"
        method = " (Jina)" if used_jina else " (Direct)"
        print(f"  {status}{method} - {name}")


if __name__ == "__main__":
    asyncio.run(test_web_scraper())
