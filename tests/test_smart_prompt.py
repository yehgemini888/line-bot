"""
Test Script: Smart Prompt System

Tests content classification and prompt template selection.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.content_classifier import ContentClassifier, ContentCategory
from src.infrastructure.prompt_template_manager import PromptTemplateManager


# Test content samples
TEST_SAMPLES = [
    {
        "name": "GitHub 專案",
        "url": "https://github.com/openai/whisper",
        "content": "OpenAI Whisper 是一個自動語音識別系統，支援多語言轉錄...",
        "expected": ContentCategory.TECH
    },
    {
        "name": "育兒文章",
        "url": "https://babyhome.com.tw/article/12345",
        "content": "寶寶六個月大開始可以嘗試副食品，建議從米糊開始...",
        "expected": ContentCategory.PARENTING
    },
    {
        "name": "投資理財",
        "url": "https://example.com/finance",
        "content": "台股今日收盤上漲，投資人關注聯準會利率決策...",
        "expected": ContentCategory.FINANCE
    },
    {
        "name": "一般文章",
        "url": "https://example.com/lifestyle",
        "content": "今天天氣很好，適合出去走走...",
        "expected": ContentCategory.LIFESTYLE
    }
]


async def test_classifier():
    """Test content classification."""
    print("=" * 60)
    print("Content Classifier Test")
    print("=" * 60)
    
    # Check for AI service
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not gemini_key and not openai_key:
        print("❌ No AI API key found")
        return False
    
    # Initialize AI service
    if gemini_key:
        from src.infrastructure.gemini_service import GeminiService
        ai_service = GeminiService(api_key=gemini_key)
        print(f"✅ Using Gemini API")
    else:
        from src.infrastructure.openai_service import OpenAIService
        ai_service = OpenAIService(api_key=openai_key)
        print(f"✅ Using OpenAI API")
    
    # Initialize classifier
    classifier = ContentClassifier(ai_service=ai_service)
    print("✅ ContentClassifier initialized\n")
    
    # Test each sample
    results = []
    for sample in TEST_SAMPLES:
        print(f"📝 Testing: {sample['name']}")
        print(f"   URL: {sample['url']}")
        print("-" * 40)
        
        result = await classifier.classify(
            content=sample["content"],
            url=sample["url"]
        )
        
        match = "✅" if result.category == sample["expected"] else "❌"
        results.append(result.category == sample["expected"])
        
        print(f"   {match} Category: {result.category.value}")
        print(f"   Reason: {result.reason}\n")
    
    return all(results)


def test_templates():
    """Test prompt template manager."""
    print("=" * 60)
    print("Prompt Template Manager Test")
    print("=" * 60)
    
    manager = PromptTemplateManager()
    print("✅ PromptTemplateManager initialized\n")
    
    # List all templates
    templates = manager.list_templates()
    print(f"📋 Available templates ({len(templates)}):\n")
    
    for template in templates:
        print(f"  [{template.category.value}] {template.name}")
        print(f"   Preview: {template.prompt[:60]}...\n")
    
    return True


async def main():
    print("\n🔬 Smart Prompt System Test\n")
    
    # Test templates (no API needed)
    template_ok = test_templates()
    
    # Test classifier (needs API)
    classifier_ok = await test_classifier()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Templates: {'✅ PASS' if template_ok else '❌ FAIL'}")
    print(f"  Classifier: {'✅ PASS' if classifier_ok else '❌ FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
