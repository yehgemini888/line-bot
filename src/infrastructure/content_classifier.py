"""
Infrastructure Layer: Content Classifier

AI-powered content classification with dynamic category support.
Uses keyword matching and AI classification based on available templates.
"""

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.prompt_template_manager import PromptTemplateManager


@dataclass
class ClassificationResult:
    """Result of content classification."""
    category: str  # Now a string to support custom categories
    confidence: Optional[float] = None
    reason: Optional[str] = None


class ContentClassifier:
    """
    Classifies content into categories using keywords and AI.
    
    Supports dynamic categories based on templates in PromptTemplateManager.
    """

    def __init__(self, ai_service, template_manager: "PromptTemplateManager" = None):
        """
        Initialize the classifier.

        Args:
            ai_service: AI service (Gemini or OpenAI) for classification
            template_manager: Optional template manager for dynamic categories
        """
        self.ai_service = ai_service
        self.template_manager = template_manager

    async def classify(
        self, 
        content: str, 
        url: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify content into a category.

        Strategy:
        1. First check URL patterns (fast path)
        2. Then try keyword matching from templates
        3. Fall back to AI classification with available categories

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
                print(f"🏷️ [Classifier] URL match: {url_category}")
                return ClassificationResult(
                    category=url_category,
                    reason="URL pattern match"
                )

        # Step 2: Try keyword matching from templates
        if self.template_manager:
            keyword_match = self.template_manager.match_by_keywords(content)
            if keyword_match:
                return ClassificationResult(
                    category=keyword_match,
                    reason="Keyword match"
                )

        # Step 3: AI classification with dynamic categories
        return await self._classify_by_ai(content)

    def _classify_by_url(self, url: str) -> Optional[str]:
        """Classify by URL pattern (fast path)."""
        url_lower = url.lower()
        
        # Tech patterns
        tech_patterns = [
            "github.com", "gitlab.com", "stackoverflow.com",
            "medium.com", "dev.to", "hackernews", "techcrunch",
            "wired.com", "theverge.com", "arstechnica.com"
        ]
        if any(p in url_lower for p in tech_patterns):
            return "tech"

        # Parenting patterns
        parenting_patterns = [
            "babyhome", "mombaby", "親子", "育兒",
            "parenting", "baby", "flipedu.parenting"
        ]
        if any(p in url_lower for p in parenting_patterns):
            return "parenting"

        # Finance patterns
        finance_patterns = [
            "investing", "財經", "理財", "stock",
            "yahoo.com/finance", "bloomberg", "cnbc"
        ]
        if any(p in url_lower for p in finance_patterns):
            return "finance"

        return None

    async def _classify_by_ai(self, content: str) -> ClassificationResult:
        """Classify using AI with dynamic categories."""
        try:
            # Get available categories from template manager
            if self.template_manager:
                categories = self.template_manager.get_all_categories()
            else:
                categories = ["tech", "parenting", "finance", "lifestyle"]

            # Add casual to categories if not present
            if "casual" not in categories:
                categories.append("casual")
            
            # Build category descriptions for AI
            category_list = ", ".join(categories)
            
            # Truncate content if too long
            content_preview = content[:1500] if len(content) > 1500 else content
            
            prompt = f"""請分析以下內容，判斷它最適合哪個類別。

可用類別：{category_list}

判斷規則：
1. 如果內容是**打招呼**（如 "hi", "你好"）、**測試**（"test", "123"）、**極短語句**或**無意義語詞**，請務必選擇 **casual**。
2. 如果是某些特定主題（科技、親子、財經...），請選擇對應類別。
3. 如果都不符合，選擇 lifestyle。

內容：
{content_preview}

請只回答一個類別名稱（從上述選項中選擇），不要加任何其他文字。"""
            
            # Use the AI service to classify
            result = await self.ai_service.generate_simple(prompt)
            
            # Parse result
            category_str = result.strip().lower()
            
            # Validate it's a known category
            if category_str not in categories:
                category_str = "lifestyle"  # Default fallback
            
            print(f"🏷️ [Classifier] AI classified as: {category_str}")
            
            return ClassificationResult(
                category=category_str,
                reason="AI classification"
            )

        except Exception as e:
            print(f"⚠️ [Classifier] AI classification failed: {e}, using lifestyle")
            return ClassificationResult(
                category="lifestyle",
                reason=f"Fallback due to error: {str(e)}"
            )
