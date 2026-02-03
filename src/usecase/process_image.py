"""
UseCase Layer: Process Image

Orchestrates image upload to Drive, AI analysis, and saving to Notion.
"""

from dataclasses import dataclass
from typing import Protocol, Optional, List
from datetime import datetime

from src.domain.content import Content, create_image_content


# Define interfaces (ports) for dependency injection
class ImageAnalyzerService(Protocol):
    """Interface for image analysis service."""

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str
    ) -> "ImageAnalysisResult":
        ...


class ImageUploadService(Protocol):
    """Interface for image upload service."""

    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        mime_type: str
    ) -> "UploadResult":
        ...


class ImageContentRepository(Protocol):
    """Interface for content persistence with image support."""

    async def save(
        self,
        title: str,
        summary: str,
        content: str,
        content_type: str,
        tags: List[str],
        source_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        author: Optional[str] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        shares: Optional[int] = None,
        image_url: Optional[str] = None,
        image_description: Optional[str] = None
    ) -> "RepositorySaveResult":
        ...


@dataclass
class ImageAnalysisResult:
    """Expected result from image analyzer."""
    title: str
    description: str
    tags: List[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class UploadResult:
    """Expected result from upload service."""
    success: bool
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RepositorySaveResult:
    """Expected result from repository."""
    success: bool
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ProcessImageResult:
    """Result of the process image use case."""
    content: Optional[Content]
    success: bool
    page_url: Optional[str] = None
    error_message: Optional[str] = None


class ProcessImageUseCase:
    """
    Use case for processing images.

    Takes image data, uploads to Google Drive, analyzes with AI,
    and saves the result to Notion.
    """

    def __init__(
        self,
        image_analyzer: ImageAnalyzerService,
        image_uploader: ImageUploadService,
        repository: ImageContentRepository
    ):
        """
        Initialize the use case.

        Args:
            image_analyzer: AI service for image analysis (Gemini Vision)
            image_uploader: Service for uploading images (Google Drive)
            repository: Content repository (Notion)
        """
        self.image_analyzer = image_analyzer
        self.image_uploader = image_uploader
        self.repository = repository

    async def execute(
        self,
        image_data: bytes,
        filename: str,
        mime_type: str = "image/jpeg"
    ) -> ProcessImageResult:
        """
        Execute the process image use case.

        Args:
            image_data: Raw image binary data
            filename: Name for the uploaded file
            mime_type: MIME type of the image

        Returns:
            ProcessImageResult containing the processed Content entity
        """
        print(f"📸 [ProcessImage] Starting image processing: {filename}")

        # Step 1: Upload image to Google Drive
        upload_result = self.image_uploader.upload_image(
            image_data=image_data,
            filename=filename,
            mime_type=mime_type
        )

        if not upload_result.success:
            return ProcessImageResult(
                content=None,
                success=False,
                error_message=f"圖片上傳失敗: {upload_result.error_message}"
            )

        drive_url = upload_result.file_url
        print(f"📤 [ProcessImage] Image uploaded to Drive: {drive_url}")

        # Step 2: Analyze image with AI
        analysis_result = await self.image_analyzer.analyze_image(
            image_data=image_data,
            mime_type=mime_type
        )

        if not analysis_result.success:
            return ProcessImageResult(
                content=None,
                success=False,
                error_message=f"圖片分析失敗: {analysis_result.error_message}"
            )

        print(f"🔍 [ProcessImage] Image analyzed: {analysis_result.title}")

        # Step 3: Create content entity
        content = create_image_content(
            image_url=drive_url,
            image_description=analysis_result.description,
            title=analysis_result.title,
            tags=analysis_result.tags
        )

        # Step 4: Save to Notion
        save_result = await self.repository.save(
            title=content.title,
            summary=content.summary,
            content=content.raw_content,
            content_type=content.content_type.value,
            tags=content.tags,
            source_url=None,
            created_at=content.created_at,
            image_url=drive_url,
            image_description=analysis_result.description
        )

        if not save_result.success:
            return ProcessImageResult(
                content=content,
                success=False,
                error_message=f"儲存至 Notion 失敗: {save_result.error_message}"
            )

        print(f"✅ [ProcessImage] Saved to Notion: {save_result.page_url}")

        return ProcessImageResult(
            content=content,
            success=True,
            page_url=save_result.page_url
        )
