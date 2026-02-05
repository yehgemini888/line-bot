"""
Infrastructure Layer: OpenAI Service

Handles AI summarization and image analysis using OpenAI GPT models.
"""

import base64
from openai import AsyncOpenAI
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SummaryResult:
    """Result of AI summarization."""
    title: str
    summary: str
    tags: List[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class ImageAnalysisResult:
    """Result of image analysis."""
    title: str
    description: str
    tags: List[str]
    success: bool
    error_message: Optional[str] = None


class OpenAIService:
    """
    AI service for content summarization and image analysis using OpenAI.
    """

    def __init__(
        self,
        api_key: str,
        text_model: str = "gpt-4o-mini",
        vision_model: str = "gpt-4o-mini"
    ):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key
            text_model: Model for text summarization (default: gpt-4o-mini)
            vision_model: Model for image analysis (default: gpt-4o)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.text_model = text_model
        self.vision_model = vision_model

    async def summarize(
        self, 
        content: str, 
        content_type: str = "text",
        custom_prompt: str = None
    ) -> SummaryResult:
        """
        Summarize content using OpenAI.

        Args:
            content: The text content to summarize
            content_type: Type of content ("text" or "url")
            custom_prompt: Optional custom prompt template to use

        Returns:
            SummaryResult with title, summary, and tags
        """
        try:
            prompt = self._build_prompt(content, content_type, custom_prompt)

            response = await self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {"role": "system", "content": "你是一個專業的內容摘要助手，請用繁體中文回覆。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content
            parsed = self._parse_response(result_text)

            return SummaryResult(
                title=parsed["title"],
                summary=parsed["summary"],
                tags=parsed["tags"],
                success=True
            )

        except Exception as e:
            print(f"❌ [OpenAI] Summarization failed: {e}")
            return SummaryResult(
                title="Error",
                summary="",
                tags=[],
                success=False,
                error_message=str(e)
            )

    async def generate_simple(self, prompt: str) -> str:
        """
        Generate a simple text response (for classification, etc).

        Args:
            prompt: The prompt to send

        Returns:
            Generated text response
        """
        try:
            # Detect if this is a Schema generation request (needs more tokens)
            is_schema_generation = "JSON Schema" in prompt or "輸出結構" in prompt
            max_tokens = 1000 if is_schema_generation else 100
            
            response = await self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ [OpenAI] generate_simple error: {e}")
            return ""

    async def summarize_with_schema(
        self,
        content: str,
        prompt: str,
        schema: dict
    ) -> dict:
        """
        使用 Structured Output API 進行摘要。
        
        AI 會根據提供的 JSON Schema 回傳結構化的 JSON 輸出，
        確保輸出格式一致且可靠。
        
        Args:
            content: 要摘要的內容
            prompt: 分析指示（Prompt 模板）
            schema: 輸出結構定義（JSON Schema）
            
        Returns:
            dict: 符合 Schema 結構的摘要結果
            
        Raises:
            Exception: 當 API 呼叫失敗或 JSON 解析失敗時
        """
        import json
        
        # 截斷過長的內容
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "...(已截斷)"
        
        # 組合完整的 Prompt
        full_prompt = f"""{prompt}

---

以下是需要分析的內容：

{content}

---

請根據上述指示進行分析。"""
        
        try:
            print(f"🎯 [OpenAI] 使用 Structured Output API")
            print(f"📋 [OpenAI] Schema 欄位: {list(schema.get('properties', {}).keys())}")
            
            # OpenAI 需要 additionalProperties: false
            openai_schema = dict(schema)
            openai_schema["additionalProperties"] = False
            
            # 使用 Structured Output API
            response = await self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {"role": "system", "content": "你是一個專業的內容分析助手，請用繁體中文回覆。"},
                    {"role": "user", "content": full_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "summary_response",
                        "strict": True,
                        "schema": openai_schema
                    }
                },
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析 JSON 回應
            result = json.loads(response.choices[0].message.content)
            print(f"✅ [OpenAI] Structured Output 成功")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ [OpenAI] JSON 解析失敗: {e}")
            raise
        except Exception as e:
            print(f"❌ [OpenAI] Structured Output 失敗: {e}")
            raise

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg"
    ) -> ImageAnalysisResult:
        """
        Analyze an image using OpenAI Vision.

        Args:
            image_data: Image binary data
            mime_type: MIME type of the image

        Returns:
            ImageAnalysisResult with title, description, and tags
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            prompt = self._build_image_prompt()

            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            result_text = response.choices[0].message.content
            parsed = self._parse_image_response(result_text)

            print(f"🔍 [OpenAI Vision] Analysis complete: {parsed['title']}")

            return ImageAnalysisResult(
                title=parsed["title"],
                description=parsed["description"],
                tags=parsed["tags"],
                success=True
            )

        except Exception as e:
            print(f"❌ [OpenAI Vision] Analysis failed: {e}")
            return ImageAnalysisResult(
                title="Error",
                description="",
                tags=[],
                success=False,
                error_message=str(e)
            )

    def _build_prompt(
        self, 
        content: str, 
        content_type: str,
        custom_prompt: str = None
    ) -> str:
        """Build the summarization prompt."""
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "...(truncated)"

        # Use custom prompt if provided
        if custom_prompt:
            print(f"🎯 [OpenAI] Using custom prompt: {custom_prompt[:50]}...")
            return f"""{custom_prompt}

---

以下是需要分析的內容（類型：{content_type}）：

{content}

---

請根據上述指示進行分析和摘要。
請嚴格按照以下格式回覆：

標題：[用一句話概括主題，15字以內]

摘要：[請根據自訂 Prompt 的要求撰寫摘要內容]

標籤：[提供3-5個相關標籤，用逗號分隔]
"""

        # Default prompt
        source_desc = "網頁內容" if content_type == "url" else "文字內容"

        return f"""請分析以下{source_desc}，並以繁體中文回覆：

---
{content}
---

請嚴格按照以下格式回覆（不要加入其他內容）：

標題：[用一句話概括主題，15字以內]

摘要：[用3-5句話總結重點內容]

標籤：[提供3-5個相關標籤，用逗號分隔]
"""

    def _build_image_prompt(self) -> str:
        """Build the image analysis prompt."""
        return """請分析這張圖片，並以繁體中文回覆。

請嚴格按照以下格式回覆（不要加入其他內容）：

標題：[用一句話描述圖片內容，15字以內]

描述：[用3-5句話詳細描述圖片中的內容、場景、物體、人物、文字等]

標籤：[提供3-5個相關標籤，用逗號分隔，例如：風景、美食、寵物、科技等]
"""

    def _parse_response(self, response_text: str) -> dict:
        """Parse OpenAI response into structured data."""
        result = {
            "title": "",
            "summary": "",
            "tags": []
        }

        lines = response_text.strip().split("\n")
        current_field = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("標題：") or line.startswith("標題:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "title"
                current_content = [line.replace("標題：", "").replace("標題:", "").strip()]

            elif line.startswith("摘要：") or line.startswith("摘要:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "summary"
                current_content = [line.replace("摘要：", "").replace("摘要:", "").strip()]

            elif line.startswith("標籤：") or line.startswith("標籤:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "tags_raw"
                tags_text = line.replace("標籤：", "").replace("標籤:", "").strip()
                tags = [t.strip() for t in tags_text.replace("，", ",").split(",") if t.strip()]
                result["tags"] = tags
                current_field = None
                current_content = []

            elif current_field:
                current_content.append(line)

        if current_field and current_content:
            result[current_field] = "\n".join(current_content).strip()

        if not result["title"]:
            result["title"] = "未能解析標題"
        if not result["summary"]:
            result["summary"] = response_text[:500] if response_text else "未能產生摘要"

        return result

    def _parse_image_response(self, response_text: str) -> dict:
        """Parse OpenAI image analysis response into structured data."""
        result = {
            "title": "",
            "description": "",
            "tags": []
        }

        lines = response_text.strip().split("\n")
        current_field = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("標題：") or line.startswith("標題:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "title"
                current_content = [line.replace("標題：", "").replace("標題:", "").strip()]

            elif line.startswith("描述：") or line.startswith("描述:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "description"
                current_content = [line.replace("描述：", "").replace("描述:", "").strip()]

            elif line.startswith("標籤：") or line.startswith("標籤:"):
                if current_field and current_content:
                    result[current_field] = "\n".join(current_content).strip()
                current_field = "tags_raw"
                tags_text = line.replace("標籤：", "").replace("標籤:", "").strip()
                tags = [t.strip() for t in tags_text.replace("，", ",").split(",") if t.strip()]
                result["tags"] = tags
                current_field = None
                current_content = []

            elif current_field:
                current_content.append(line)

        if current_field and current_content:
            result[current_field] = "\n".join(current_content).strip()

        if not result["title"]:
            result["title"] = "圖片分析"
        if not result["description"]:
            result["description"] = response_text[:500] if response_text else "未能產生描述"

        return result
