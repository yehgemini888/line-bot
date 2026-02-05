"""
Infrastructure Layer: Prompt Template Manager

Manages prompt templates stored in Notion for different content categories.
Supports fully dynamic, user-customizable templates with keyword matching.
Now includes output schema support for Structured Output API.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.infrastructure.output_schemas import (
    PRESET_SCHEMAS, 
    DEFAULT_SCHEMA, 
    get_preset_schema, 
    is_preset_format
)
from src.infrastructure.schema_cache import SchemaCache
from src.infrastructure.schema_generator import SchemaGenerator


@dataclass
class PromptTemplate:
    """A prompt template for a specific content category."""
    name: str
    category: str  # Now a string to support custom categories
    prompt: str
    keywords: List[str] = field(default_factory=list)
    active: bool = True
    output_format: str = "標準摘要"  # 新增：輸出格式（預設或自動推斷）


class PromptTemplateManager:
    """
    Manages prompt templates for different content categories.
    
    Supports dynamic categories from Notion with keyword matching.
    Now includes output schema support for Structured Output API.
    """

    # Default prompt templates (fallback when Notion not configured)
    DEFAULT_TEMPLATES: Dict[str, PromptTemplate] = {
        "tech": PromptTemplate(
            name="科技分析",
            category="tech",
            prompt="""你是一位專業的科技評論家和技術分析師。請以客觀、專業的角度分析這段內容。

請提供：
1. **核心技術/工具**：這是什麼技術或工具？
2. **用途與應用場景**：可以用來做什麼？
3. **優缺點分析**：有什麼優勢和限制？
4. **關鍵重點**：最重要的 3 個 takeaway

請用繁體中文回答，風格專業但易懂。""",
            keywords=["github", "api", "程式", "開源", "軟體", "AI", "python", "javascript"],
            output_format="自動推斷"
        ),
        
        "parenting": PromptTemplate(
            name="親子教育",
            category="parenting",
            prompt="""你是一位溫暖且經驗豐富的親子教育專家。請以鼓勵、支持的口吻分析這段內容。

請提供：
1. **核心觀點**：這篇內容的主要訊息是什麼？
2. **實用建議**：父母可以怎麼應用在日常生活中？
3. **注意事項**：有什麼需要特別留意的地方？
4. **暖心小語**：給爸媽的一句鼓勵

請用繁體中文回答，語氣溫和、正向。""",
            keywords=["育兒", "寶寶", "親子", "教養", "小孩", "兒童", "媽媽", "爸爸"],
            output_format="自動推斷"
        ),
        
        "finance": PromptTemplate(
            name="投資理財",
            category="finance",
            prompt="""你是一位專業的財務顧問。請以數據導向、謹慎的態度分析這段內容。

請提供：
1. **核心觀點**：這篇內容的主要論點是什麼？
2. **市場分析**：對投資/理財有什麼啟示？
3. **風險提醒**：有什麼潛在風險需要注意？
4. **行動建議**：讀者可以考慮的下一步

⚠️ 免責聲明：此為資訊分享，非投資建議。

請用繁體中文回答，風格專業、謹慎。""",
            keywords=["投資", "理財", "股票", "ETF", "基金", "財經", "存股"],
            output_format="自動推斷"
        ),
        
        "lifestyle": PromptTemplate(
            name="一般摘要",
            category="lifestyle",
            prompt="""請分析並摘要這段內容。

請提供：
1. **主題**：這篇內容在談什麼？
2. **重點摘要**：最重要的 3-5 個重點
3. **結論/洞見**：作者想傳達的核心訊息

請用繁體中文回答，簡潔清晰。""",
            keywords=[],
            output_format="標準摘要"
        ),

        "casual": PromptTemplate(
            name="閒聊回應",
            category="casual",
            prompt="""你是一個友善、幽默的 AI 助手。
用戶剛剛傳送了一則簡短的閒聊訊息、測試訊號、或無意義的語詞（如 "嗨"、"123"、"test"）。

請只要：
1. **確認收到**：簡單回應即可，不用長篇大論。
2. **友善互動**：保持語氣輕鬆、幽默。
3. **不要分析**：這不是文章，不需要摘要、主題分析或重點整理。

請直接回應那句話，不用任何格式。""",
            keywords=["嗨", "hello", "hi", "你好", "測試", "test", "123"],
            output_format="閒聊模式"
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
        self._templates: Dict[str, PromptTemplate] = dict(self.DEFAULT_TEMPLATES)
        self._loaded_from_notion = False
        
        # 新增：Schema 相關元件
        self._schema_cache = SchemaCache()
        self._schema_generator = SchemaGenerator()

    def get_template(self, category: str) -> PromptTemplate:
        """
        Get the prompt template for a category.

        Args:
            category: Content category (string)

        Returns:
            PromptTemplate for the category, or lifestyle as fallback
        """
        return self._templates.get(category, self._templates.get("lifestyle"))

    def get_prompt(self, category: str) -> str:
        """
        Get just the prompt string for a category.

        Args:
            category: Content category

        Returns:
            Prompt string
        """
        template = self.get_template(category)
        return template.prompt if template else ""

    async def get_template_with_schema(
        self, 
        category: str, 
        content: str,
        ai_service
    ) -> Tuple[PromptTemplate, dict]:
        """
        取得模板及其對應的輸出結構。
        
        根據模板的 output_format 設定：
        - 如果是預設格式（如「標準摘要」），使用預定義的 Schema
        - 如果是「自動推斷」，AI 會以指定角色分析內容，決定最適合的 Schema
        
        Args:
            category: 內容分類
            content: 要分析的內容（用於自動推斷 Schema）
            ai_service: AI 服務（用於自動推斷時生成 Schema）
            
        Returns:
            Tuple[PromptTemplate, dict]: 模板和對應的 JSON Schema
        """
        template = self.get_template(category)
        
        if not template:
            print(f"⚠️ [Templates] 找不到分類 '{category}'，使用預設")
            template = self._templates.get("lifestyle")
            return template, DEFAULT_SCHEMA
        
        output_format = template.output_format
        
        # 情況 1：使用預設格式
        if is_preset_format(output_format):
            schema = get_preset_schema(output_format)
            print(f"📋 [Templates] 使用預設格式: {output_format}")
            return template, schema
        
        # 情況 2：自動推斷 - 每次都根據內容動態生成
        # 注意：不使用快取，因為每篇內容可能需要不同的結構
        print(f"🔄 [Templates] 自動推斷 Schema: {category}")
        schema = await self._schema_generator.generate_schema(
            role_prompt=template.prompt,
            content=content,
            ai_service=ai_service
        )
        
        return template, schema

    def list_templates(self) -> List[PromptTemplate]:
        """List all available templates."""
        return list(self._templates.values())

    def get_all_categories(self) -> List[str]:
        """Get all available category names."""
        return list(self._templates.keys())

    def get_all_keywords_map(self) -> Dict[str, List[str]]:
        """
        Get a mapping of category -> keywords.
        Used by the classifier for keyword matching.
        """
        return {
            category: template.keywords 
            for category, template in self._templates.items()
            if template.keywords
        }

    def match_by_keywords(self, content: str) -> Optional[str]:
        """
        Match content to a category based on keywords.
        
        Args:
            content: Content text to match
            
        Returns:
            Category name if matched, None otherwise
        """
        content_lower = content.lower()
        
        best_match = None
        best_score = 0
        
        for category, template in self._templates.items():
            if not template.keywords:
                continue
                
            score = sum(1 for kw in template.keywords if kw.lower() in content_lower)
            
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_score >= 2:  # Require at least 2 keyword matches
            print(f"🏷️ [Templates] Keyword match: {best_match} (score: {best_score})")
            return best_match
            
        return None

    async def load_from_notion(self) -> None:
        """
        Load templates from Notion database.
        Replaces/extends default templates with user-defined ones.
        """
        if not self.notion_client or not self.template_database_id:
            print("⚠️ [Templates] Notion not configured, using defaults only")
            return

        try:
            print(f"📋 [Templates] Loading from Notion: {self.template_database_id[:8]}...")
            
            # Query the database (async)
            response = await self.notion_client.databases.query(
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
                    name_prop = props.get("Name") or {}
                    name_titles = name_prop.get("title", [])
                    name = name_titles[0]["text"]["content"] if name_titles else "Unnamed"
                    
                    # Extract category (now a free-form string)
                    category_prop = props.get("Category") or {}
                    category_select = category_prop.get("select") or {}
                    category = category_select.get("name", "lifestyle").lower()
                    
                    # Extract prompt
                    prompt_prop = props.get("Prompt") or {}
                    prompt_texts = prompt_prop.get("rich_text", [])
                    prompt = prompt_texts[0]["text"]["content"] if prompt_texts else ""
                    
                    if not prompt:
                        print(f"⚠️ [Templates] Skipping '{name}': empty prompt")
                        continue
                    
                    # Extract keywords
                    keywords_prop = props.get("Keywords") or {}
                    keywords_texts = keywords_prop.get("rich_text", [])
                    keywords_str = keywords_texts[0]["text"]["content"] if keywords_texts else ""
                    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
                    
                    # 新增：Extract output format
                    output_format_prop = props.get("Output Format") or {}
                    output_format_select = output_format_prop.get("select") or {}
                    output_format = output_format_select.get("name", "標準摘要")
                    
                    # Create template
                    template = PromptTemplate(
                        name=name,
                        category=category,
                        prompt=prompt,
                        keywords=keywords,
                        active=True,
                        output_format=output_format
                    )
                    
                    # Store it (overwrites defaults if same category)
                    self._templates[category] = template
                    loaded_count += 1
                    print(f"✅ [Templates] Loaded: {name} → {category} (format: {output_format})")
                    
                except Exception as e:
                    print(f"⚠️ [Templates] Error parsing template: {e}")
                    continue
            
            self._loaded_from_notion = True
            print(f"📋 [Templates] Loaded {loaded_count} templates from Notion")
            print(f"📋 [Templates] Total categories: {list(self._templates.keys())}")
            
        except Exception as e:
            print(f"❌ [Templates] Failed to load from Notion: {e}")
    
    def clear_schema_cache(self) -> None:
        """清除所有 Schema 快取"""
        self._schema_cache.clear()
