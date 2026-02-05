"""
Infrastructure Layer: Schema Generator

根據「角色定義（Prompt）+ 內容」動態決定最適合的輸出結構。
AI 會以指定角色的視角分析內容，決定最佳的輸出格式。
"""

import json
from typing import Protocol

from src.infrastructure.output_schemas import DEFAULT_SCHEMA


class AIServiceProtocol(Protocol):
    """AI 服務介面"""
    async def generate_simple(self, prompt: str) -> str:
        ...


# Schema 生成用的 Prompt 模板
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
            schema = self._parse_response(response)
            
            # 確保包含基礎欄位
            schema = self._ensure_base_fields(schema)
            
            print(f"✅ [SchemaGenerator] Schema 生成成功: {list(schema.get('properties', {}).keys())}")
            return schema
            
        except Exception as e:
            print(f"❌ [SchemaGenerator] Schema 生成失敗: {e}")
            print(f"⚠️ [SchemaGenerator] 使用預設 Schema")
            return DEFAULT_SCHEMA
    
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
        # 使用空內容呼叫新方法
        return await self.generate_schema(prompt, "", ai_service)
    
    def _parse_response(self, response: str) -> dict:
        """
        解析 AI 回應為 JSON Schema。
        
        Args:
            response: AI 的回應文字
            
        Returns:
            解析後的 JSON Schema
        """
        # 清理回應（移除可能的 markdown 格式）
        cleaned = response.strip()
        
        # 移除 ```json 和 ``` 標記
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        # 解析 JSON
        schema = json.loads(cleaned)
        
        # 驗證基本結構
        if "type" not in schema:
            schema["type"] = "object"
        
        if "properties" not in schema:
            raise ValueError("Schema 缺少 properties 欄位")
        
        # 清理不支援的欄位
        schema = self._sanitize_schema(schema)
        
        return schema
    
    def _sanitize_schema(self, schema: dict) -> dict:
        """
        清理 Schema，移除 Gemini/OpenAI 不支援的欄位。
        
        Gemini 不支援：maxLength, minLength, pattern, format 等
        OpenAI 需要：additionalProperties: false
        
        Args:
            schema: 原始 Schema
            
        Returns:
            清理後的 Schema
        """
        # 不支援的欄位列表
        UNSUPPORTED_FIELDS = {
            "maxLength", "minLength", "pattern", "format",
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
            "multipleOf", "minItems", "maxItems", "uniqueItems",
            "minProperties", "maxProperties", "enum", "const",
            "$schema", "$id", "$ref", "definitions", "$defs"
        }
        
        def clean_property(prop: dict) -> dict:
            """清理單一屬性"""
            cleaned = {}
            for key, value in prop.items():
                if key in UNSUPPORTED_FIELDS:
                    continue
                if key == "items" and isinstance(value, dict):
                    cleaned[key] = clean_property(value)
                elif isinstance(value, dict):
                    cleaned[key] = clean_property(value)
                else:
                    cleaned[key] = value
            return cleaned
        
        # 清理每個屬性
        if "properties" in schema:
            cleaned_properties = {}
            for prop_name, prop_value in schema["properties"].items():
                if isinstance(prop_value, dict):
                    cleaned_properties[prop_name] = clean_property(prop_value)
                else:
                    cleaned_properties[prop_name] = prop_value
            schema["properties"] = cleaned_properties
        
        # 注意：additionalProperties 由各 AI 服務自行處理
        # Gemini 不支援，OpenAI 需要
        
        return schema
    
    def _ensure_base_fields(self, schema: dict) -> dict:
        """
        確保 Schema 包含必要的基礎欄位。
        
        Args:
            schema: 原始 Schema
            
        Returns:
            包含基礎欄位的 Schema
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # 確保有 標題
        if "標題" not in properties:
            properties["標題"] = self.BASE_PROPERTIES["標題"]
            if "標題" not in required:
                required.append("標題")
        
        # 確保有 標籤
        if "標籤" not in properties:
            properties["標籤"] = self.BASE_PROPERTIES["標籤"]
            if "標籤" not in required:
                required.append("標籤")
        
        schema["properties"] = properties
        schema["required"] = required
        
        return schema
