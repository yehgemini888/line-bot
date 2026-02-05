#!/usr/bin/env python3
"""
Script to update Telegram handlers to use SummarizeUseCase
"""

def update_telegram_handlers():
    file_path = 'src/infrastructure/telegram_handler.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update _handle_youtube method
    old_youtube = '''    async def _handle_youtube(self, youtube_url: str) -> str:
        """Handle YouTube URL processing."""
        from src.domain.content import create_youtube_content

        print(f"🎬 [YouTube] Processing: {youtube_url}")

        # Get video info
        video_info = await self.youtube_service.get_video_info(youtube_url)
        if not video_info:
            return "❌ 無法取得 YouTube 影片資訊，請確認網址是否正確"

        # Prepare content for AI
        if video_info.has_captions and video_info.captions:
            text_to_summarize = f"""影片標題：{video_info.title}
頻道：{video_info.channel_name}
時長：{video_info.duration}

字幕內容：
{video_info.captions[:15000]}"""
            has_captions = True
        else:
            text_to_summarize = f"""影片標題：{video_info.title}
頻道：{video_info.channel_name}
時長：{video_info.duration}

影片描述：
{video_info.description[:3000] if video_info.description else '(無描述)'}"""
            has_captions = False

        # AI Summarization
        summary_result = await self.ai_service.summarize(
            content=text_to_summarize,
            content_type="youtube"
        )

        if not summary_result.success:
            return f"❌ AI 摘要失敗：{summary_result.error_message}"

        # Create content entity
        content = create_youtube_content(
            url=youtube_url,
            title=video_info.title,
            channel_name=video_info.channel_name,
            video_duration=video_info.duration
        )
        content.summary = summary_result.summary
        content.title = summary_result.title or video_info.title
        content.tags = summary_result.tags

        # Save to Notion
        save_result = await self.save_usecase.execute(content)
        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build response
        return self._build_youtube_response(content, video_info, has_captions, save_result.page_url)'''
    
    new_youtube = '''    async def _handle_youtube(self, youtube_url: str) -> str:
        """Handle YouTube URL processing."""
        if not self.youtube_service:
            return "❌ YouTube 功能未啟用"

        print(f"🎬 [YouTube] Processing: {youtube_url}")

        # Step 1: Get video info
        video_info = await self.youtube_service.get_video_info(youtube_url)
        if not video_info:
            return "❌ 無法取得 YouTube 影片資訊，請確認網址是否正確"

        # Step 2: Summarize via SummarizeUseCase (NEW - uses template system)
        summarize_result = await self.summarize_usecase.execute(
            raw_input=youtube_url,
            input_type=ContentType.YOUTUBE,
            youtube_info={
                "title": video_info.title,
                "captions": video_info.captions,
                "description": video_info.description,
                "channel": video_info.channel_name,
                "duration": video_info.duration
            }
        )

        if not summarize_result.success:
            return f"❌ 處理失敗：{summarize_result.error_message}"

        content = summarize_result.content

        # Step 3: Save to Notion
        save_result = await self.save_usecase.execute(content)
        if not save_result.success:
            return f"❌ 儲存失敗：{save_result.error_message}"

        # Build response with template info
        has_captions = video_info.has_captions and video_info.captions
        return self._build_youtube_response(
            content,
            video_info,
            has_captions,
            save_result.page_url,
            template_used=summarize_result.template_used,
            output_format_used=summarize_result.output_format_used
        )'''
    
    # Replace (handle both \n and \r\n)
    content = content.replace(old_youtube.replace('\n', '\r\n'), new_youtube.replace('\n', '\r\n'))
    if old_youtube in content:  # Fallback to \n only
        content = content.replace(old_youtube, new_youtube)
    
    # 2. Update _build_youtube_response signature
    old_sig = '''    def _build_youtube_response(
        self,
        content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None
    ) -> str:'''
    
    new_sig = '''    def _build_youtube_response(
        self,
        content,
        video_info,
        has_captions: bool,
        page_url: Optional[str] = None,
        template_used: Optional[str] = None,
        output_format_used: Optional[str] = None
    ) -> str:'''
    
    content = content.replace(old_sig.replace('\n', '\r\n'), new_sig.replace('\n', '\r\n'))
    if old_sig in content:
        content = content.replace(old_sig, new_sig)
    
    # 3. Add template info to _build_youtube_response
    # Find the line with 🏷️ 標籤 and add template info after it
    import re
    pattern = r'(🏷️ 標籤：\{tags_str\}\{caption_note\}""")\s*\n\s*\n\s*(if page_url:)'
    replacement = r'\1\n\n        # Add template info if available\n        if template_used:\n            response += f"\\n\\n🎯 使用模板：{template_used}"\n        if output_format_used:\n            response += f"\\n📋 輸出格式：{output_format_used}"\n\n        \2'
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated Telegram YouTube handler")

if __name__ == '__main__':
    update_telegram_handlers()
