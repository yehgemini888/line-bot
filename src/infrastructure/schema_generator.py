"""
Infrastructure Layer: Schema Generator

根據「角色定義（Prompt）+ 內容」動態決定最適合的輸出結構。
AI 會以指定角色的視角分析內容，決定最佳的輸出格式。

支援兩種模式：
1. generate_schema(): 已知分類，只生成 Schema
2. classify_and_generate_schema(): 同時分類 + 生成 Schema（合併為 1 次 AI 呼叫）
"""

import json
from typing import Protocol, Dict, Tuple, Optional

from src.infrastructure.output_schemas import DEFAULT_SCHEMA


class AIServiceProtocol(Protocol):
    """AI 服務介面"""
    async def generate_simple(self, prompt: str) -> str:
        ...


# Schema 生成用的 Prompt 模板（僅生成 Schema，已知分類）
SCHEMA_GENERATOR_PROMPT = """你是一個輸出結構設計專家。

你的任務是根據「角色定義」和「內容摘要」，決定最適合的輸出結構。

## 角色定義
{role_prompt}

## 內容摘要（前 500 字）
{content_preview}

---

請以這個角色的視角，思考如何最好地呈現這篇內容的分析結果。
設計一個 JSON Schema 來定義輸出結構。

規則：
1. 一定要包含 "標題"（15字以內）和 "標籤"（3-5個標籤）
2. 根據角色定義中要求的分析項目，為每個項目建立對應欄位
3. 如果角色定義中有編號列表（如 1. 2. 3.），將每一項轉換為對應的欄位
4. 【重要】欄位名稱必須使用繁體中文，不要用英文
5. 如果某項需要多個要點，使用 array 類型；如果是敘述，使用 string 類型

請直接輸出 JSON Schema，格式如下：
{{
  "type": "object",
  "properties": {{
    "標題": {{"type": "string", "description": "用一句話概括主題，15字以內"}},
    "核心訊息": {{"type": "string", "description": "文章的核心觀點"}},
    "重點分析": {{"type": "array", "items": {{"type": "string"}}, "description": "主要的分析要點"}},
    "標籤": {{"type": "array", "items": {{"type": "string"}}, "description": "3-5個相關標籤"}}
  }},
  "required": ["標題", "其他必要欄位", "標籤"]
}}

只輸出 JSON，不要其他文字。"""


# 合併分類 + Schema 生成的 Prompt 模板
CLASSIFY_AND_SCHEMA_PROMPT = """你是一個內容分類與輸出結構設計專家。

你的任務是：
1. 判斷以下內容最適合哪個分析角色
2. 以該角色的視角，為這篇內容設計最適合的輸出 JSON Schema

## 可用的分析角色

{templates_description}

## 內容摘要（前 500 字）
{content_preview}

---

## 判斷規則
1. 如果內容是**打招呼**（如 "hi", "你好"）、**測試**（"test", "123"）、**極短語句**或**無意義語詞**，請選擇 **casual**。
2. 根據內容主題選擇最匹配的角色。
3. 如果都不明確符合，選擇 **lifestyle**。

## Schema 設計規則
1. 一定要包含 "標題"（15字以內）和 "標籤"（3-5個標籤）
2. 根據所選角色的分析項目，為每個項目建立對應欄位
3. 【重要】欄位名稱必須使用繁體中文，不要用英文
4. 如果某項需要多個要點，使用 array 類型；如果是敘述，使用 string 類型

## 輸出格式
請輸出以下 JSON（不要其他文字）：
{{
  "category": "選擇的分類名稱",
  "schema": {{
    "type": "object",
    "properties": {{
      "標題": {{"type": "string", "description": "用一句話概括主題，15字以內"}},
      "核心訊息": {{"type": "string", "description": "文章的核心觀點"}},
      "標籤": {{"type": "array", "items": {{"type": "string"}}, "description": "3-5個相關標籤"}}
    }},
    "required": ["標題", "其他必要欄位", "標籤"]
  }}
}}"""


class SchemaGenerator:
    """
    根據「角色定義 + 內容」動態生成輸出結構。

    流程：
    1. 接收角色定義（Prompt）和內容
    2. AI 以該角色視角分析內容
    3. 決定最適合的輸出結構（Schema）
    """

    # 基礎欄位（一定要有的）- 使用繁體中文
    BASE_PROPERTIES = {
        "標題": {
            "type": "string",
            "description": "用一句話概括主題，15字以內"
        },
        "標籤": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5個相關標籤"
        }
    }

    async def generate_schema(
        self,
        role_prompt: str,
        content: str,
        ai_service: AIServiceProtocol
    ) -> dict:
        """
        根據角色定義和內容，生成最適合的輸出結構。

        Args:
            role_prompt: 角色定義（Prompt 模板）
            content: 要分析的內容
            ai_service: AI 服務

        Returns:
            生成的 JSON Schema
        """
        try:
            print(f"🔄 [SchemaGenerator] 分析角色+內容，生成最佳 Schema...")

            # 截取內容預覽（避免太長）
            content_preview = content[:500] + "..." if len(content) > 500 else content

            # 組合生成用的 Prompt
            generator_prompt = SCHEMA_GENERATOR_PROMPT.format(
                role_prompt=role_prompt,
                content_preview=content_preview
            )

            # 使用 AI 生成 Schema
            response = await ai_service.generate_simple(generator_prompt)

            # 解析回應
            schema = self._parse_schema_response(response)

            # 確保包含基礎欄位
            schema = self._ensure_base_fields(schema)

            print(f"✅ [SchemaGenerator] Schema 生成成功: {list(schema.get('properties', {}).keys())}")
            return schema

        except Exception as e:
            print(f"❌ [SchemaGenerator] Schema 生成失敗: {e}")
            print(f"⚠️ [SchemaGenerator] 使用預設 Schema")
            return DEFAULT_SCHEMA

    async def classify_and_generate_schema(
        self,
        content: str,
        templates: Dict[str, object],
        ai_service: AIServiceProtocol
    ) -> Tuple[str, dict]:
        """
        合併分類 + Schema 生成為單一 AI 呼叫。

        Args:
            content: 要分析的內容
            templates: 所有可用模板 {category: PromptTemplate}
            ai_service: AI 服務

        Returns:
            Tuple[category, schema]: 分類結果和動態生成的 Schema
        """
        try:
            print(f"🔄 [SchemaGenerator] 合併分類+Schema 生成...")

            # 構建模板描述
            templates_desc = self._build_templates_description(templates)

            # 截取內容預覽
            content_preview = content[:500] + "..." if len(content) > 500 else content

            # 組合 prompt
            prompt = CLASSIFY_AND_SCHEMA_PROMPT.format(
                templates_description=templates_desc,
                content_preview=content_preview
            )

            # 使用 AI 生成
            response = await ai_service.generate_simple(prompt)

            # 解析回應
            result = self._parse_classify_and_schema_response(response, templates)
            category = result["category"]
            schema = result["schema"]

            # 確保 Schema 包含基礎欄位
            schema = self._ensure_base_fields(schema)

            print(f"✅ [SchemaGenerator] 合併結果: 分類={category}, Schema 欄位={list(schema.get('properties', {}).keys())}")
            return category, schema

        except Exception as e:
            print(f"❌ [SchemaGenerator] 合併分類+Schema 失敗: {e}")
            print(f"⚠️ [SchemaGenerator] 回退到 lifestyle + 預設 Schema")
            return "lifestyle", DEFAULT_SCHEMA

    def _build_templates_description(self, templates: Dict[str, object]) -> str:
        """構建所有模板的描述文字，供 AI 參考。"""
        descriptions = []
        for category, template in templates.items():
            keywords = getattr(template, 'keywords', [])
            keywords_str = ", ".join(keywords) if keywords else "無"
            prompt_preview = getattr(template, 'prompt', '')[:200]
            descriptions.append(
                f"### {category} ({getattr(template, 'name', category)})\n"
                f"- 關鍵字: {keywords_str}\n"
                f"- 角色定義: {prompt_preview}..."
            )
        return "\n\n".join(descriptions)

    def _parse_classify_and_schema_response(
        self, response: str, templates: Dict[str, object]
    ) -> dict:
        """解析合併分類+Schema 的 AI 回應。"""
        cleaned = self._clean_json_response(response)
        result = json.loads(cleaned)

        # 驗證 category
        category = result.get("category", "lifestyle").strip().lower()
        valid_categories = list(templates.keys())
        if category not in valid_categories:
            category = "lifestyle"

        # 驗證 schema
        schema = result.get("schema", {})
        if not isinstance(schema, dict) or "properties" not in schema:
            raise ValueError("回應中缺少有效的 schema")

        if "type" not in schema:
            schema["type"] = "object"

        # 清理 schema
        schema = self._sanitize_schema(schema)

        return {"category": category, "schema": schema}

    # 向後相容：保留舊的方法簽名
    async def generate_schema_from_prompt(
        self,
        prompt: str,
        ai_service: AIServiceProtocol
    ) -> dict:
        """
        （已棄用）僅根據 Prompt 生成 Schema。
        建議使用 generate_schema(role_prompt, content, ai_service)。
        """
        return await self.generate_schema(prompt, "", ai_service)

    def _clean_json_response(self, response: str) -> str:
        """清理 AI 回應中的 markdown 格式。"""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _parse_schema_response(self, response: str) -> dict:
        """解析 AI 回應為 JSON Schema。"""
        cleaned = self._clean_json_response(response)
        schema = json.loads(cleaned)

        if "type" not in schema:
            schema["type"] = "object"
        if "properties" not in schema:
            raise ValueError("Schema 缺少 properties 欄位")

        schema = self._sanitize_schema(schema)
        return schema

    def _sanitize_schema(self, schema: dict) -> dict:
        """
        清理 Schema，移除 Gemini/OpenAI 不支援的欄位。
        """
        UNSUPPORTED_FIELDS = {
            "maxLength", "minLength", "pattern", "format",
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
            "multipleOf", "minItems", "maxItems", "uniqueItems",
            "minProperties", "maxProperties", "enum", "const",
            "$schema", "$id", "$ref", "definitions", "$defs"
        }

        def clean_property(prop: dict) -> dict:
            cleaned = {}
            for key, value in prop.items():
                if key in UNSUPPORTED_FIELDS:
                    continue
                if isinstance(value, dict):
                    cleaned[key] = clean_property(value)
                else:
                    cleaned[key] = value
            return cleaned

        if "properties" in schema:
            cleaned_properties = {}
            for prop_name, prop_value in schema["properties"].items():
                if isinstance(prop_value, dict):
                    cleaned_properties[prop_name] = clean_property(prop_value)
                else:
                    cleaned_properties[prop_name] = prop_value
            schema["properties"] = cleaned_properties

        return schema

    def _ensure_base_fields(self, schema: dict) -> dict:
        """
        確保 Schema 包含必要的基礎欄位，並符合 Strict Mode 要求。
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        if "標題" not in properties:
            properties["標題"] = self.BASE_PROPERTIES["標題"]
        if "標籤" not in properties:
            properties["標籤"] = self.BASE_PROPERTIES["標籤"]

        # OpenAI Strict Mode: 所有屬性都必須是 required
        all_keys = list(properties.keys())
        required = list(set(required + all_keys))

        schema["properties"] = properties
        schema["required"] = required
        schema["additionalProperties"] = False

        return schema
