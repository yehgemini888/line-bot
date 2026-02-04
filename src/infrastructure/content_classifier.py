"""
Infrastructure Layer: Content Classifier

AI-powered content classification to determine the appropriate
prompt template for summarization.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ContentCategory(Enum):
    """Supported content categories for prompt selection."""
    TECH = "tech"           # 科技/程式/工具
    PARENTING = "parenting" # 親子/育兒
    FINANCE = "finance"     # 理財/投資
    LIFESTYLE = "lifestyle" # 一般生活 (fallback)


@dataclass
class ClassificationResult:
    """Result of content classification."""
    category: ContentCategory
    confidence: Optional[float] = None
    reason: Optional[str] = None


class ContentClassifier:
    """
    Classifies content into categories using AI.
    
    This determines which prompt template to use for summarization.
    """

    # Classification prompt template
    CLASSIFICATION_PROMPT = """請分析以下內容，判斷它屬於哪個類別。

類別選項：
- tech: 科技、程式設計、軟體工具、AI、開源專案、技術教學
- parenting: 親子教育、育兒、寶寶發展、家庭生活
- finance: 投資理財、股票、加密貨幣、財務規劃
- lifestyle: 其他生活類內容（預設）

內容：
{content}

請只回答一個類別名稱（tech/parenting/finance/lifestyle），不要加任何其他文字。"""

    def __init__(self, ai_service):
        """
        Initialize the classifier.

        Args:
            ai_service: AI service (Gemini or OpenAI) for classification
        """
        self.ai_service = ai_service

    async def classify(self, content: str, url: Optional[str] = None) -> ClassificationResult:
        """
        Classify content into a category.

        Strategy:
        1. First check URL patterns (fast path)
        2. Fall back to AI classification

        Args:
            content: Content text to classify
            url: Optional URL for pattern matching

        Returns:
            ClassificationResult with category
        """
        # Step 1: Try URL-based classification (fast)
        if url:
            url_category = self._classify_by_url(url)
            if url_category:
                print(f"🏷️ [Classifier] URL match: {url_category.value}")
                return ClassificationResult(
                    category=url_category,
                    reason="URL pattern match"
                )

        # Step 2: AI classification
        return await self._classify_by_ai(content)

    def _classify_by_url(self, url: str) -> Optional[ContentCategory]:
        """Classify by URL pattern (fast path)."""
        url_lower = url.lower()
        
        # Tech patterns
        tech_patterns = [
            "github.com", "gitlab.com", "stackoverflow.com",
            "medium.com", "dev.to", "hackernews", "techcrunch",
            "wired.com", "theverge.com", "arstechnica.com"
        ]
        if any(p in url_lower for p in tech_patterns):
            return ContentCategory.TECH

        # Parenting patterns
        parenting_patterns = [
            "babyhome", "mombaby", "親子", "育兒",
            "parenting", "baby"
        ]
        if any(p in url_lower for p in parenting_patterns):
            return ContentCategory.PARENTING

        # Finance patterns
        finance_patterns = [
            "investing", "財經", "理財", "stock",
            "yahoo.com/finance", "bloomberg", "cnbc"
        ]
        if any(p in url_lower for p in finance_patterns):
            return ContentCategory.FINANCE

        return None

    async def _classify_by_ai(self, content: str) -> ClassificationResult:
        """Classify using AI (slower but more accurate)."""
        try:
            # Truncate content if too long
            content_preview = content[:1500] if len(content) > 1500 else content
            
            prompt = self.CLASSIFICATION_PROMPT.format(content=content_preview)
            
            # Use the AI service to classify
            # We'll use a simple generate method
            result = await self.ai_service.generate_simple(prompt)
            
            # Parse result
            category_str = result.strip().lower()
            
            # Map to enum
            category_map = {
                "tech": ContentCategory.TECH,
                "parenting": ContentCategory.PARENTING,
                "finance": ContentCategory.FINANCE,
                "lifestyle": ContentCategory.LIFESTYLE
            }
            
            category = category_map.get(category_str, ContentCategory.LIFESTYLE)
            print(f"🏷️ [Classifier] AI classified as: {category.value}")
            
            return ClassificationResult(
                category=category,
                reason="AI classification"
            )

        except Exception as e:
            print(f"⚠️ [Classifier] AI classification failed: {e}, using lifestyle")
            return ClassificationResult(
                category=ContentCategory.LIFESTYLE,
                reason=f"Fallback due to error: {str(e)}"
            )
