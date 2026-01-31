"""
Infrastructure Layer: Web Scraper

Fetches and extracts text content from URLs.
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from dataclasses import dataclass


@dataclass
class ScrapedContent:
    """Result of web scraping."""
    url: str
    title: Optional[str]
    text_content: str
    success: bool
    error_message: Optional[str] = None


class WebScraper:
    """
    Fetches web pages and extracts readable text content.
    """

    def __init__(self, timeout: float = 10.0):
        """
        Initialize the web scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def scrape(self, url: str) -> ScrapedContent:
        """
        Scrape content from a URL.

        Args:
            url: The URL to scrape

        Returns:
            ScrapedContent with extracted text and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # Extract title
                title = self._extract_title(soup)

                # Extract main text content
                text_content = self._extract_text(soup)

                return ScrapedContent(
                    url=url,
                    title=title,
                    text_content=text_content,
                    success=True
                )

        except httpx.TimeoutException:
            return ScrapedContent(
                url=url,
                title=None,
                text_content="",
                success=False,
                error_message="Request timed out"
            )
        except httpx.HTTPStatusError as e:
            return ScrapedContent(
                url=url,
                title=None,
                text_content="",
                success=False,
                error_message=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return ScrapedContent(
                url=url,
                title=None,
                text_content="",
                success=False,
                error_message=str(e)
            )

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        # Try og:title first
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # Fallback to <title> tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return None

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract readable text from HTML."""
        # Remove script, style, nav, footer, header elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()

        # Try to find main content areas
        main_content = (
            soup.find("article") or
            soup.find("main") or
            soup.find(class_=["content", "post-content", "article-content", "entry-content"]) or
            soup.find("body")
        )

        if main_content:
            # Get text with proper spacing
            text = main_content.get_text(separator="\n", strip=True)
            # Clean up excessive newlines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)

        return ""
