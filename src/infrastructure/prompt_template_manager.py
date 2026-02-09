"""
Infrastructure Layer: Prompt Template Manager

Manages prompt templates stored in Notion for different content categories.
Supports fully dynamic, user-customizable templates with keyword matching.
Now includes output schema support for Structured Output API.

Optimizations:
- TTL cache for Notion template loading (5 min)
- Merged classify + schema generation (1 AI call instead of 2)
"""

import time
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

# TTL for Notion template cache (seconds)
TEMPLATE_TTL = 300  # 5 minutes


@dataclass
class PromptTemplate:
    """A prompt template for a specific content category."""
    name: str
    category: str  # Now a string to support custom categories
    prompt: str
    keywords: List[str] = field(default_factory=list)
    active: bool = True
    output_format: str = "標準摘要"  # 輸出格式（預設或自動推斷）


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
        self.notion_client = notion_client
        self.template_database_id = template_database_id
        self._templates: Dict[str, PromptTemplate] = dict(self.DEFAULT_TEMPLATES)
        self._loaded_from_notion = False
        self._last_loaded_at = 0.0  # TTL timestamp

        # Schema 相關元件
        self._schema_cache = SchemaCache()
        self._schema_generator = SchemaGenerator()

    def _should_reload(self) -> bool:
        """Check if templates should be reloaded (TTL expired)."""
        return time.time() - self._last_loaded_at > TEMPLATE_TTL

    def get_template(self, category: str) -> PromptTemplate:
        """Get the prompt template for a category."""
        return self._templates.get(category, self._templates.get("lifestyle"))

    def get_prompt(self, category: str) -> str:
        """Get just the prompt string for a category."""
        template = self.get_template(category)
        return template.prompt if template else ""

    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """Get all templates as a dict."""
        return self._templates

    async def get_template_with_schema(
        self,
        category: str,
        content: str,
        ai_service
    ) -> Tuple[PromptTemplate, dict]:
        """
        取得模板及其對應的輸出結構（已知分類時使用）。
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

        # 情況 2：自動推斷 - 根據內容動態生成
        print(f"🔄 [Templates] 自動推斷 Schema: {category}")
        schema = await self._schema_generator.generate_schema(
            role_prompt=template.prompt,
            content=content,
            ai_service=ai_service
        )

        return template, schema

    async def classify_and_get_template_with_schema(
        self,
        content: str,
        ai_service,
        url: Optional[str] = None
    ) -> Tuple[PromptTemplate, dict, str]:
        """
        智慧分類 + Schema 生成的合併入口。

        流程：
        1. URL pattern match → 快速分類（無 AI）
        2. Keyword match → 快速分類（無 AI）
        3. 都沒中 → 合併 AI 呼叫（分類 + Schema 同時生成）

        對於預設格式的模板，不需要 AI 生成 Schema。
        對於自動推斷的模板，步驟 1/2 中需要額外 1 次 AI 生成 Schema，
        步驟 3 中則合併為 1 次 AI 呼叫完成。

        Returns:
            Tuple[template, schema, category]
        """
        from src.infrastructure.content_classifier import ContentClassifier

        # Step 1: URL pattern match (fast, no AI)
        if url:
            category = ContentClassifier._classify_by_url_static(url)
            if category:
                print(f"🏷️ [SmartMatch] URL 快速匹配: {category}")
                template, schema = await self.get_template_with_schema(
                    category, content, ai_service
                )
                return template, schema, category

        # Step 2: Keyword match (fast, no AI)
        keyword_match = self.match_by_keywords(content)
        if keyword_match:
            print(f"🏷️ [SmartMatch] 關鍵字匹配: {keyword_match}")
            template, schema = await self.get_template_with_schema(
                keyword_match, content, ai_service
            )
            return template, schema, keyword_match

        # Step 3: 合併 AI 呼叫 (classify + schema in 1 call)
        print(f"🤖 [SmartMatch] 無快速匹配，使用合併 AI 分類+Schema 生成")
        category, schema = await self._schema_generator.classify_and_generate_schema(
            content=content,
            templates=self._templates,
            ai_service=ai_service
        )

        template = self.get_template(category)

        # 如果分類到的模板是預設格式，覆蓋 AI 生成的 schema
        if template and is_preset_format(template.output_format):
            schema = get_preset_schema(template.output_format)
            print(f"📋 [SmartMatch] 分類={category}，使用預設格式: {template.output_format}")

        return template, schema, category

    def list_templates(self) -> List[PromptTemplate]:
        """List all available templates."""
        return list(self._templates.values())

    def get_all_categories(self) -> List[str]:
        """Get all available category names."""
        return list(self._templates.keys())

    def get_all_keywords_map(self) -> Dict[str, List[str]]:
        """Get a mapping of category -> keywords."""
        return {
            category: template.keywords
            for category, template in self._templates.items()
            if template.keywords
        }

    def match_by_keywords(self, content: str) -> Optional[str]:
        """Match content to a category based on keywords."""
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

        if best_score >= 2:
            print(f"🏷️ [Templates] Keyword match: {best_match} (score: {best_score})")
            return best_match

        return None

    async def load_from_notion(self) -> None:
        """
        Load templates from Notion database.
        Respects TTL cache - skips reload if loaded recently.
        """
        if not self.notion_client or not self.template_database_id:
            print("⚠️ [Templates] Notion not configured, using defaults only")
            return

        # TTL check
        if not self._should_reload():
            print(f"✅ [Templates] 使用快取模板 (TTL 剩餘 {int(TEMPLATE_TTL - (time.time() - self._last_loaded_at))} 秒)")
            return

        try:
            print(f"📋 [Templates] Loading from Notion: {self.template_database_id[:8]}...")

            # Use raw request API (notion-client v2.7.0 doesn't have databases.query)
            response = await self.notion_client.request(
                path=f"databases/{self.template_database_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "Active",
                        "checkbox": {"equals": True}
                    }
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

                    # Extract category
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

                    # Extract output format
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

                    self._templates[category] = template
                    loaded_count += 1
                    print(f"✅ [Templates] Loaded: {name} → {category} (format: {output_format})")

                except Exception as e:
                    print(f"⚠️ [Templates] Error parsing template: {e}")
                    continue

            self._loaded_from_notion = True
            self._last_loaded_at = time.time()
            print(f"📋 [Templates] Loaded {loaded_count} templates from Notion")
            print(f"📋 [Templates] Total categories: {list(self._templates.keys())}")

        except Exception as e:
            print(f"❌ [Templates] Failed to load from Notion: {e}")
            # Still update timestamp to avoid hammering Notion on repeated failures
            self._last_loaded_at = time.time()

    def clear_schema_cache(self) -> None:
        """清除所有 Schema 快取"""
        self._schema_cache.clear()
