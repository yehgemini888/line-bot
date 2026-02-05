# 🔧 Telegram Handler 重構指令

## 需要修改的檔案
`src/infrastructure/telegram_handler.py`

---

## 修改 1: _build_youtube_response (約第 324-358 行)

**找到這個方法：**
```python
def _build_youtube_response(
    self,
    content,
    video_info,
    has_captions: bool,
    page_url: Optional[str] = None,
    template_used: Optional[str] = None,
    output_format_used: Optional[str] = None
) -> str:
    """Build YouTube success response."""
    tags_str = ", ".join(content.tags) if content.tags else "無"
    caption_note = "" if has_captions else "\n\n⚠️ 此影片無字幕，僅能提供基本摘要"

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
```

**替換為：**
```python
def _build_youtube_response(
    self,
    content,
    video_info,
    has_captions: bool,
    page_url: Optional[str] = None,
    template_used: Optional[str] = None,
    output_format_used: Optional[str] = None
) -> str:
    """Build YouTube success response."""
    return ResponseBuilder.build_youtube_response(
        content=content,
        video_info=video_info,
        has_captions=has_captions,
        page_url=page_url,
        template_used=template_used,
        output_format_used=output_format_used
    )
```

---

## 修改 2: _build_audio_success_response (約第 467-503 行)

**找到這個方法並替換為：**
```python
def _build_audio_success_response(
    self,
    content,
    transcription: str,
    duration: float,
    page_url: Optional[str] = None,
    template_used: Optional[str] = None,
    output_format_used: Optional[str] = None
) -> str:
    """Build success response for audio processing."""
    return ResponseBuilder.build_audio_response(
        content=content,
        transcription=transcription,
        duration=duration,
        page_url=page_url,
        template_used=template_used,
        output_format_used=output_format_used
    )
```

---

## 修改 3: _build_photo_success_response (約第 676-704 行)

**找到這個方法並替換為：**
```python
def _build_photo_success_response(
    self,
    content,
    caption: str,
    page_url: Optional[str] = None,
    template_used: Optional[str] = None,
    output_format_used: Optional[str] = None
) -> str:
    """Build success response for photo processing."""
    return ResponseBuilder.build_image_response(
        content=content,
        page_url=page_url,
        caption=caption if caption else None,
        template_used=template_used,
        output_format_used=output_format_used
    )
```

---

## ✅ 完成後

所有三個方法都會變得非常簡潔，只是調用 `ResponseBuilder` 的對應方法。

**優點：**
- Line 和 Telegram 使用相同的回應格式
- 修改一次，兩邊都更新
- 代碼更簡潔易維護
