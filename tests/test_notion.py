"""
Test Script: Notion Repository

Tests saving content to Notion database.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.notion_repo import NotionRepository
from src.domain.content import Content, ContentType


async def test_notion():
    print("=" * 60)
    print("Notion Repository Test")
    print("=" * 60)
    
    notion_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_key or not database_id:
        print("❌ NOTION_API_KEY or NOTION_DATABASE_ID not set")
        return
    
    print(f"✅ Notion API Key: {notion_key[:20]}...")
    print(f"✅ Database ID: {database_id[:10]}...")
    
    repo = NotionRepository(api_key=notion_key, database_id=database_id)
    
    # Create test content
    test_content = Content(
        id="test-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        content_type=ContentType.TEXT,
        raw_content="這是一個測試內容",
        source_url=None,
        title="[測試] 單元測試項目",
        summary="這是由單元測試自動產生的測試項目，可以安全刪除。",
        tags=["測試", "自動產生"],
        created_at=datetime.now()
    )
    
    print("\n📝 Saving test content to Notion...")
    
    try:
        result = await repo.save(test_content)
        if result.success:
            print(f"   ✅ Saved successfully!")
            print(f"   📄 Page URL: {result.page_url}")
        else:
            print(f"   ❌ Failed: {result.error_message}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_notion())
