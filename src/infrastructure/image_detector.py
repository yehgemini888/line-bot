"""
Infrastructure Layer: Image URL Detector

Detects if a URL points to an image.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageDetectResult:
    """Result of image URL detection."""
    is_image: bool
    url: Optional[str] = None
    mime_type: Optional[str] = None


class ImageDetector:
    """
    Detects image URLs from text.

    Supports common image extensions and popular image hosting services.
    """

    # Common image file extensions
    IMAGE_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.bmp', '.tiff', '.tif', '.svg'
    )

    # Image hosting patterns (URLs that are images even without extensions)
    IMAGE_HOST_PATTERNS = [
        # Imgur
        r'https?://(?:i\.)?imgur\.com/\w+',
        # Giphy
        r'https?://(?:media\.)?giphy\.com/media/\w+',
        # Unsplash
        r'https?://images\.unsplash\.com/\S+',
        # Pexels
        r'https?://images\.pexels\.com/\S+',
        # Flickr
        r'https?://(?:live\.)?staticflickr\.com/\S+',
        # Google Photos direct link
        r'https?://lh\d\.googleusercontent\.com/\S+',
        # Discord CDN
        r'https?://cdn\.discordapp\.com/attachments/\S+',
        # Twitter/X media
        r'https?://pbs\.twimg\.com/media/\S+',
    ]

    # Extension to MIME type mapping
    MIME_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.svg': 'image/svg+xml',
    }

    def __init__(self):
        """Initialize the image detector."""
        # Compile host patterns for efficiency
        self._host_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.IMAGE_HOST_PATTERNS
        ]

    def detect(self, url: str) -> ImageDetectResult:
        """
        Detect if a URL points to an image.

        Args:
            url: URL to check

        Returns:
            ImageDetectResult indicating if URL is an image
        """
        url_lower = url.lower()

        # Remove query parameters for extension check
        base_url = url_lower.split('?')[0]

        # Check by file extension
        for ext in self.IMAGE_EXTENSIONS:
            if base_url.endswith(ext):
                return ImageDetectResult(
                    is_image=True,
                    url=url,
                    mime_type=self.MIME_TYPES.get(ext, 'image/jpeg')
                )

        # Check by image hosting patterns
        for pattern in self._host_patterns:
            if pattern.match(url):
                # Default to jpeg for hosting services
                return ImageDetectResult(
                    is_image=True,
                    url=url,
                    mime_type='image/jpeg'
                )

        return ImageDetectResult(is_image=False)

    def get_mime_type(self, url: str) -> str:
        """
        Get MIME type for an image URL.

        Args:
            url: Image URL

        Returns:
            MIME type string (defaults to image/jpeg)
        """
        url_lower = url.lower().split('?')[0]

        for ext, mime_type in self.MIME_TYPES.items():
            if url_lower.endswith(ext):
                return mime_type

        return 'image/jpeg'
