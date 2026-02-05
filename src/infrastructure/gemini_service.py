"""
Infrastructure Layer: Gemini AI Service

Handles AI summarization and analysis using Google Gemini API.
Supports both text summarization and image analysis (Vision API).
"""

import base64
import google.generativeai as genai
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


class GeminiService:
    """
    AI service for content summarization using Google Gemini.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Gemini service.

        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.0-flash)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def summarize(
        self, 
        content: str, 
        content_type: str = "text",
        custom_prompt: str = None
    ) -> SummaryResult:
        """
        Summarize content using Gemini AI.

        Args:
            content: The text content to summarize
            content_type: Type of content ("text" or "url")
            custom_prompt: Optional custom prompt template to use

        Returns:
            SummaryResult with title, summary, and tags
        """
        try:
            prompt = self._build_prompt(content, content_type, custom_prompt)
            response = await self.model.generate_content_async(prompt)

            # Parse the response
            result_text = response.text
            parsed = self._parse_response(result_text)

            return SummaryResult(
                title=parsed["title"],
                summary=parsed["summary"],
                tags=parsed["tags"],
                success=True
            )

        except Exception as e:
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
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ [Gemini] generate_simple error: {e}")
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
        
        # 組合完整的 Prompt，明確要求使用繁體中文
        full_prompt = f"""【重要】請全程使用繁體中文回覆，不要使用其他語言。

{prompt}

---

以下是需要分析的內容：

{content}

---

請根據上述指示進行分析。記得全部使用繁體中文。"""
        
        try:
            print(f"🎯 [Gemini] 使用 Structured Output API")
            print(f"📋 [Gemini] Schema 欄位: {list(schema.get('properties', {}).keys())}")
            
            # 使用 Structured Output API
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )
            
            # 解析 JSON 回應
            result = json.loads(response.text)
            print(f"✅ [Gemini] Structured Output 成功")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ [Gemini] JSON 解析失敗: {e}")
            raise
        except Exception as e:
            print(f"❌ [Gemini] Structured Output 失敗: {e}")
            raise

    def _build_prompt(
        self, 
        content: str, 
        content_type: str,
        custom_prompt: str = None
    ) -> str:
        """Build the summarization prompt."""
        # Truncate content if too long
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "...(truncated)"

        # Use custom prompt if provided
        if custom_prompt:
            print(f"🎯 [Gemini] Using custom prompt: {custom_prompt[:50]}...")
            return f"""{custom_prompt}

---

以下是需要分析的內容（類型：{content_type}）：

{content}

---

請根據上述指示進行分析和摘要。
請嚴格按照以下格式回覆：

標題：[用一句話概括主題，15字以內]

摘要：[根據上述指示產生的摘要內容]

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

摘要：[請根據自訂 Prompt 的要求撰寫摘要內容]

標籤：[提供3-5個相關標籤，用逗號分隔]
"""

    def _parse_response(self, response_text: str) -> dict:
        """Parse Gemini response into structured data."""
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
                # Parse tags (comma or space separated)
                tags = [t.strip() for t in tags_text.replace("，", ",").split(",") if t.strip()]
                result["tags"] = tags
                current_field = None
                current_content = []

            elif current_field:
                current_content.append(line)

        # Handle last field
        if current_field and current_content:
            result[current_field] = "\n".join(current_content).strip()

        # Fallback if parsing failed
        if not result["title"]:
            result["title"] = "未能解析標題"
        if not result["summary"]:
            result["summary"] = response_text[:500] if response_text else "未能產生摘要"

        return result

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg"
    ) -> ImageAnalysisResult:
        """
        Analyze an image using Gemini Vision API.

        Args:
            image_data: Image binary data
            mime_type: MIME type of the image

        Returns:
            ImageAnalysisResult with title, description, and tags
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Build the prompt with image
            prompt = self._build_image_prompt()

            # Create image part for multimodal input
            image_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_base64
                }
            }

            # Generate content with image
            response = await self.model.generate_content_async([prompt, image_part])

            # Parse the response
            result_text = response.text
            parsed = self._parse_image_response(result_text)

            print(f"🔍 [Gemini Vision] Analysis complete: {parsed['title']}")

            return ImageAnalysisResult(
                title=parsed["title"],
                description=parsed["description"],
                tags=parsed["tags"],
                success=True
            )

        except Exception as e:
            print(f"❌ [Gemini Vision] Analysis failed: {e}")
            return ImageAnalysisResult(
                title="Error",
                description="",
                tags=[],
                success=False,
                error_message=str(e)
            )

    def _build_image_prompt(self) -> str:
        """Build the image analysis prompt."""
        return """請分析這張圖片，並以繁體中文回覆。

請嚴格按照以下格式回覆（不要加入其他內容）：

標題：[用一句話描述圖片內容，15字以內]

描述：[用3-5句話詳細描述圖片中的內容、場景、物體、人物、文字等]

標籤：[提供3-5個相關標籤，用逗號分隔，例如：風景、美食、寵物、科技等]
"""

    def _parse_image_response(self, response_text: str) -> dict:
        """Parse Gemini image analysis response into structured data."""
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
                # Parse tags (comma or space separated)
                tags = [t.strip() for t in tags_text.replace("，", ",").split(",") if t.strip()]
                result["tags"] = tags
                current_field = None
                current_content = []

            elif current_field:
                current_content.append(line)

        # Handle last field
        if current_field and current_content:
            result[current_field] = "\n".join(current_content).strip()

        # Fallback if parsing failed
        if not result["title"]:
            result["title"] = "圖片分析"
        if not result["description"]:
            result["description"] = response_text[:500] if response_text else "未能產生描述"

        return result
