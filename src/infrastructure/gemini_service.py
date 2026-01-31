"""
Infrastructure Layer: Gemini AI Service

Handles AI summarization and analysis using Google Gemini API.
"""

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


class GeminiService:
    """
    AI service for content summarization using Google Gemini.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Gemini service.

        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-1.5-flash)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def summarize(self, content: str, content_type: str = "text") -> SummaryResult:
        """
        Summarize content using Gemini AI.

        Args:
            content: The text content to summarize
            content_type: Type of content ("text" or "url")

        Returns:
            SummaryResult with title, summary, and tags
        """
        try:
            prompt = self._build_prompt(content, content_type)
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

    def _build_prompt(self, content: str, content_type: str) -> str:
        """Build the summarization prompt."""
        # Truncate content if too long
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "...(truncated)"

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
