"""
Test Script: AI Summarization

Tests AI summarization with both Gemini and OpenAI.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.gemini_service import GeminiService
from src.infrastructure.openai_service import OpenAIService


async def test_summarize():
    print("=" * 60)
    print("AI Summarization Test")
    print("=" * 60)
    
    # Test content
    test_content = """
    人工智慧（Artificial Intelligence，AI）是電腦科學的一個分支，
    致力於創建能夠執行通常需要人類智慧的任務的系統。這些任務包括
    視覺感知、語音識別、決策制定和語言翻譯。近年來，深度學習和
    大型語言模型的發展使 AI 技術取得了突破性進展，ChatGPT 和
    Gemini 等生成式 AI 正在改變我們與技術互動的方式。
    """
    
    # Test Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("\n🤖 Testing Gemini...")
        try:
            gemini = GeminiService(api_key=gemini_key)
            result = await gemini.summarize(test_content, content_type="text")
            if result.success:
                print(f"   ✅ Title: {result.title}")
                print(f"   📝 Summary: {result.summary[:100]}...")
                print(f"   🏷️ Tags: {result.tags}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("\n⚠️ GEMINI_API_KEY not set, skipping Gemini test")
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("\n🤖 Testing OpenAI...")
        try:
            openai_svc = OpenAIService(api_key=openai_key)
            result = await openai_svc.summarize(test_content, content_type="text")
            if result.success:
                print(f"   ✅ Title: {result.title}")
                print(f"   📝 Summary: {result.summary[:100]}...")
                print(f"   🏷️ Tags: {result.tags}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("\n⚠️ OPENAI_API_KEY not set, skipping OpenAI test")


if __name__ == "__main__":
    asyncio.run(test_summarize())
