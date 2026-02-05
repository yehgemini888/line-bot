"""
Infrastructure Layer: Response Builder

統一的回應訊息建構器，供 Line 和 Telegram Handler 共用。
確保兩個平台的用戶獲得一致的回應品質。
"""

from typing import Optional


class ResponseBuilder:
    """
    統一的回應訊息建構器。
    
    所有平台（Line, Telegram）共用相同的訊息格式，
    確保用戶體驗一致且易於維護。
    """
    
    @staticmethod
    def build_youtube_response(
        content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """
        建構 YouTube 影片處理成功的回應訊息。
        
        Args:
            content: 內容實體（包含 title, summary, tags）
            video_info: YouTube 影片資訊（channel_name, duration）
            has_captions: 是否有字幕
            page_url: Notion 頁面連結
            template_used: 使用的模板名稱
            output_format_used: 使用的輸出格式
            
        Returns:
            格式化的回應訊息
        """
        tags_str = ", ".join(content.tags) if content.tags else "無"
        
        # Add warning if no captions
        caption_note = ""
        if not has_captions:
            caption_note = "\n\n⚠️ 此影片無字幕，僅能提供基本摘要"
        
        response = f"""✅ YouTube 影片已儲存至 Notion！

🎬 頻道：{video_info.channel_name}
⏱️ 時長：{video_info.duration}

📌 標題：{content.title}

📝 摘要：
{content.summary}

🏷️ 標籤：{tags_str}{caption_note}"""

        # Add template info if available
        if template_used:
            response += f"\n\n🎯 使用模板：{template_used}"
        if output_format_used:
            response += f"\n📋 輸出格式：{output_format_used}"

        if page_url:
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response
    
    @staticmethod
    def build_audio_response(
        content,
        transcription: str,
        duration: Optional[float],
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """
        建構語音訊息處理成功的回應訊息。
        
        Args:
            content: 內容實體（包含 title, summary, tags）
            transcription: 轉錄文字
            duration: 語音時長（秒）
            page_url: Notion 頁面連結
            template_used: 使用的模板名稱
            output_format_used: 使用的輸出格式
            
        Returns:
            格式化的回應訊息
        """
        tags_str = ", ".join(content.tags) if content.tags else "無"
        duration_str = f"{int(duration)}秒" if duration else "未知"

        # Truncate transcription if too long
        display_transcription = transcription
        if len(transcription) > 200:
            display_transcription = transcription[:200] + "..."

        response = f"""✅ 語音訊息已儲存至 Notion！

🎙️ 時長：{duration_str}

📝 轉錄內容：
{display_transcription}

📌 標題：{content.title}

📋 摘要：
{content.summary}

🏷️ 標籤：{tags_str}"""

        # Add template info if available
        if template_used:
            response += f"\n\n🎯 使用模板：{template_used}"
        if output_format_used:
            response += f"\n📋 輸出格式：{output_format_used}"

        if page_url:
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response
    
    @staticmethod
    def build_image_response(
        content,
        page_url: Optional[str] = None,
        caption: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:
        """
        建構圖片處理成功的回應訊息。
        
        Args:
            content: 內容實體（包含 title, image_description, tags, image_url）
            page_url: Notion 頁面連結
            caption: 用戶提供的圖片說明（Telegram 專用）
            template_used: 使用的模板名稱
            output_format_used: 使用的輸出格式
            
        Returns:
            格式化的回應訊息
        """
        tags_str = ", ".join(content.tags) if content.tags else "無"
        
        # 使用 image_description 或 summary
        description = content.image_description or content.summary

        response = f"""✅ 圖片已儲存至 Notion！

📌 標題：{content.title}

📝 描述：
{description}

🏷️ 標籤：{tags_str}

🖼️ 圖片連結：{content.image_url}"""

        # Add user caption if provided (Telegram)
        if caption:
            response = f"""✅ 圖片已儲存至 Notion！

📝 您的說明：{caption}

📌 標題：{content.title}

🖼️ AI 分析：
{description}

🏷️ 標籤：{tags_str}

🖼️ 圖片連結：{content.image_url}"""

        # Add template info if available
        if template_used:
            response += f"\n\n🎯 使用模板：{template_used}"
        if output_format_used:
            response += f"\n📋 輸出格式：{output_format_used}"

        if page_url:
            response += f"\n\n📄 Notion 連結：{page_url}"

        return response
