"""
Infrastructure Layer: Prompt Template Manager

Manages prompt templates stored in Notion for different content categories.
Supports user-customizable templates.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from src.infrastructure.content_classifier import ContentCategory


@dataclass
class PromptTemplate:
    """A prompt template for a specific content category."""
    name: str
    category: ContentCategory
    prompt: str
    active: bool = True


class PromptTemplateManager:
    """
    Manages prompt templates for different content categories.
    
    Currently uses in-memory defaults, with future support for
    Notion-based user-customizable templates.
    """

    # Default prompt templates
    DEFAULT_TEMPLATES: Dict[ContentCategory, PromptTemplate] = {
        ContentCategory.TECH: PromptTemplate(
            name="科技分析",
            category=ContentCategory.TECH,
            prompt="""你是一位專業的科技評論家和技術分析師。請以客觀、專業的角度分析這段內容。

請提供：
1. **核心技術/工具**：這是什麼技術或工具？
2. **用途與應用場景**：可以用來做什麼？
3. **優缺點分析**：有什麼優勢和限制？
4. **關鍵重點**：最重要的 3 個 takeaway

請用繁體中文回答，風格專業但易懂。""",
        ),
        
        ContentCategory.PARENTING: PromptTemplate(
            name="親子教育",
            category=ContentCategory.PARENTING,
            prompt="""你是一位溫暖且經驗豐富的親子教育專家。請以鼓勵、支持的口吻分析這段內容。

請提供：
1. **核心觀點**：這篇內容的主要訊息是什麼？
2. **實用建議**：父母可以怎麼應用在日常生活中？
3. **注意事項**：有什麼需要特別留意的地方？
4. **暖心小語**：給爸媽的一句鼓勵

請用繁體中文回答，語氣溫和、正向。""",
        ),
        
        ContentCategory.FINANCE: PromptTemplate(
            name="投資理財",
            category=ContentCategory.FINANCE,
            prompt="""你是一位專業的財務顧問。請以數據導向、謹慎的態度分析這段內容。

請提供：
1. **核心觀點**：這篇內容的主要論點是什麼？
2. **市場分析**：對投資/理財有什麼啟示？
3. **風險提醒**：有什麼潛在風險需要注意？
4. **行動建議**：讀者可以考慮的下一步

⚠️ 免責聲明：此為資訊分享，非投資建議。

請用繁體中文回答，風格專業、謹慎。""",
        ),
        
        ContentCategory.LIFESTYLE: PromptTemplate(
            name="一般摘要",
            category=ContentCategory.LIFESTYLE,
            prompt="""請分析並摘要這段內容。

請提供：
1. **主題**：這篇內容在談什麼？
2. **重點摘要**：最重要的 3-5 個重點
3. **結論/洞見**：作者想傳達的核心訊息

請用繁體中文回答，簡潔清晰。""",
        ),
    }

    def __init__(self, notion_client=None, template_database_id: Optional[str] = None):
        """
        Initialize the template manager.

        Args:
            notion_client: Optional Notion client for custom templates
            template_database_id: Optional Notion database ID for templates
        """
        self.notion_client = notion_client
        self.template_database_id = template_database_id
        self._custom_templates: Dict[ContentCategory, PromptTemplate] = {}

    def get_template(self, category: ContentCategory) -> PromptTemplate:
        """
        Get the prompt template for a category.

        Priority:
        1. Custom template (from Notion)
        2. Default template

        Args:
            category: Content category

        Returns:
            PromptTemplate for the category
        """
        # Check custom templates first
        if category in self._custom_templates:
            return self._custom_templates[category]
        
        # Fall back to default
        return self.DEFAULT_TEMPLATES.get(
            category, 
            self.DEFAULT_TEMPLATES[ContentCategory.LIFESTYLE]
        )

    def get_prompt(self, category: ContentCategory) -> str:
        """
        Get just the prompt string for a category.

        Args:
            category: Content category

        Returns:
            Prompt string
        """
        template = self.get_template(category)
        return template.prompt

    def list_templates(self) -> List[PromptTemplate]:
        """List all available templates."""
        templates = []
        for category in ContentCategory:
            templates.append(self.get_template(category))
        return templates

    def add_custom_template(self, template: PromptTemplate) -> None:
        """
        Add a custom template (in-memory).

        Args:
            template: Custom template to add
        """
        self._custom_templates[template.category] = template
        print(f"✅ [Templates] Added custom template: {template.name}")

    async def load_from_notion(self) -> None:
        """
        Load custom templates from Notion database.
        
        Reads templates from Notion and populates _custom_templates.
        """
        if not self.notion_client or not self.template_database_id:
            print("⚠️ [Templates] Notion not configured, using defaults only")
            return

        try:
            print(f"📋 [Templates] Loading from Notion: {self.template_database_id[:8]}...")
            
            # Query the database
            response = self.notion_client.databases.query(
                database_id=self.template_database_id,
                filter={
                    "property": "Active",
                    "checkbox": {"equals": True}
                }
            )
            
            loaded_count = 0
            for page in response.get("results", []):
                try:
                    props = page.get("properties", {})
                    
                    # Extract name
                    name_prop = props.get("Name", {}).get("title", [])
                    name = name_prop[0]["text"]["content"] if name_prop else "Unnamed"
                    
                    # Extract category
                    category_prop = props.get("Category", {}).get("select", {})
                    category_str = category_prop.get("name", "lifestyle").lower()
                    
                    # Map to ContentCategory
                    category_map = {
                        "tech": ContentCategory.TECH,
                        "parenting": ContentCategory.PARENTING,
                        "finance": ContentCategory.FINANCE,
                        "lifestyle": ContentCategory.LIFESTYLE
                    }
                    category = category_map.get(category_str, ContentCategory.LIFESTYLE)
                    
                    # Extract prompt
                    prompt_prop = props.get("Prompt", {}).get("rich_text", [])
                    prompt = prompt_prop[0]["text"]["content"] if prompt_prop else ""
                    
                    if not prompt:
                        print(f"⚠️ [Templates] Skipping '{name}': empty prompt")
                        continue
                    
                    # Extract keywords (optional)
                    keywords_prop = props.get("Keywords", {}).get("rich_text", [])
                    keywords_str = keywords_prop[0]["text"]["content"] if keywords_prop else ""
                    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
                    
                    # Create template
                    template = PromptTemplate(
                        name=name,
                        category=category,
                        prompt=prompt,
                        active=True
                    )
                    
                    # Store it
                    self._custom_templates[category] = template
                    loaded_count += 1
                    print(f"✅ [Templates] Loaded: {name} → {category.value}")
                    
                except Exception as e:
                    print(f"⚠️ [Templates] Error parsing template: {e}")
                    continue
            
            print(f"📋 [Templates] Loaded {loaded_count} custom templates from Notion")
            
        except Exception as e:
            print(f"❌ [Templates] Failed to load from Notion: {e}")


# Convenience function to build full summarization prompt
def build_summarization_prompt(
    content: str, 
    template: PromptTemplate,
    content_type: str = "text"
) -> str:
    """
    Build the full prompt for summarization.

    Args:
        content: Content to summarize
        template: Prompt template to use
        content_type: Type of content (text/url/youtube/etc)

    Returns:
        Complete prompt string
    """
    return f"""{template.prompt}

---

以下是需要分析的內容（類型：{content_type}）：

{content}

---

請根據上述指示進行分析和摘要。
另外請產生：
- 一個简短的標題（10-20 字）
- 3-5 個相關標籤（用於分類）

格式：
標題：[標題]
標籤：[標籤1], [標籤2], [標籤3]
摘要：[摘要內容]"""
