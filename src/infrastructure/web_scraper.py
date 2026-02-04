"""
Infrastructure Layer: Web Scraper

Fetches and extracts text content from URLs.
Includes Jina Reader fallback for SPA/JavaScript-rendered sites.
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
    used_jina: bool = False  # Track if Jina Reader was used


class WebScraper:
    """
    Fetches web pages and extracts readable text content.
    Uses Jina Reader (r.jina.ai) as fallback for SPA sites.
    """

    # Jina Reader API endpoint
    JINA_READER_URL = "https://r.jina.ai/"
    
    # Minimum content length to consider a page successfully scraped
    MIN_CONTENT_LENGTH = 100

    def __init__(self, timeout: float = 15.0):
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
        
        Strategy:
        1. Try direct scraping with httpx + BeautifulSoup
        2. If content is too short (<100 chars), fallback to Jina Reader

        Args:
            url: The URL to scrape

        Returns:
            ScrapedContent with extracted text and metadata
        """
        # Step 1: Try direct scraping
        result = await self._scrape_direct(url)
        
        # Step 2: If content is too short, try Jina Reader fallback
        if result.success and len(result.text_content) < self.MIN_CONTENT_LENGTH:
            print(f"⚠️ [Scraper] Content too short ({len(result.text_content)} chars), trying Jina Reader...")
            jina_result = await self._scrape_via_jina(url)
            if jina_result.success:
                return jina_result
        
        # Step 3: If direct scraping failed, try Jina Reader
        if not result.success:
            print(f"⚠️ [Scraper] Direct scraping failed, trying Jina Reader...")
            jina_result = await self._scrape_via_jina(url)
            if jina_result.success:
                return jina_result
        
        return result

    async def _scrape_direct(self, url: str) -> ScrapedContent:
        """Direct scraping with httpx + BeautifulSoup."""
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
                    success=True,
                    used_jina=False
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

    async def _scrape_via_jina(self, url: str) -> ScrapedContent:
        """
        Scrape using Jina Reader API.
        
        Jina Reader converts any URL to clean Markdown, handling:
        - JavaScript-rendered content (SPA)
        - Complex layouts
        - PDF files
        """
        jina_url = f"{self.JINA_READER_URL}{url}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Jina may take longer
                response = await client.get(
                    jina_url,
                    headers={
                        "Accept": "text/plain",
                        "User-Agent": "Mozilla/5.0"
                    },
                    follow_redirects=True
                )
                response.raise_for_status()

                content = response.text
                
                # Jina returns Markdown with title in first line
                lines = content.strip().split('\n')
                title = None
                text_content = content
                
                # Extract title if first line starts with #
                if lines and lines[0].startswith('# '):
                    title = lines[0][2:].strip()
                    text_content = '\n'.join(lines[1:]).strip()
                
                print(f"✅ [Jina] Successfully fetched: {title[:50] if title else 'No title'}...")
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    text_content=text_content,
                    success=True,
                    used_jina=True
                )

        except Exception as e:
            print(f"❌ [Jina] Failed: {e}")
            return ScrapedContent(
                url=url,
                title=None,
                text_content="",
                success=False,
                error_message=f"Jina Reader failed: {str(e)}",
                used_jina=True
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
