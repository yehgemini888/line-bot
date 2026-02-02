"""
Infrastructure Layer: Apify Social Media Scraper

Uses Apify actors to scrape content from Facebook and Threads.
"""

import os
import asyncio
from typing import Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from apify_client import ApifyClient

from src.domain.content import SocialPlatform
from src.usecase.summarize import SocialScrapeResult

# Thread pool for running sync Apify calls
_executor = ThreadPoolExecutor(max_workers=3)


class ApifyScraper:
    """
    Scrapes social media content using Apify actors.

    Supported actors:
    - Facebook: apify/facebook-posts-scraper (page/profile posts)
    - Threads: sinam7/threads-post-scraper (single post by URL)
    """

    ACTORS = {
        SocialPlatform.FACEBOOK: "apify/facebook-posts-scraper",
        SocialPlatform.THREADS: "sinam7/threads-post-scraper"
    }

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the Apify scraper.

        Args:
            api_token: Apify API token (defaults to APIFY_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN is required")
        self.client = ApifyClient(self.api_token)

    async def scrape(self, url: str, platform: SocialPlatform) -> SocialScrapeResult:
        """
        Scrape content from a social media URL.

        Args:
            url: The social media post URL
            platform: The social media platform

        Returns:
            SocialScrapedContent with extracted data
        """
        try:
            if platform == SocialPlatform.FACEBOOK:
                return await self._scrape_facebook(url)
            elif platform == SocialPlatform.THREADS:
                return await self._scrape_threads(url)
            else:
                return SocialScrapeResult(
                    platform=platform,
                    url=url,
                    author=None,
                    text_content="",
                    likes=None,
                    comments=None,
                    success=False,
                    error_message=f"Unsupported platform: {platform.value}"
                )
        except Exception as e:
            return SocialScrapeResult(
                platform=platform,
                url=url,
                author=None,
                text_content="",
                likes=None,
                comments=None,
                success=False,
                error_message=str(e)
            )

    async def _scrape_facebook(self, url: str) -> SocialScrapeResult:
        """
        Scrape Facebook post using apify/facebook-posts-scraper.

        This actor accepts Facebook page/profile URLs and returns posts including:
        - text/postText: The post content
        - pageName/userName: Author information
        - likes/reactions: Engagement count
        - comments: Comment count
        """
        actor_id = self.ACTORS[SocialPlatform.FACEBOOK]

        # Input for facebook-posts-scraper
        run_input = {
            "startUrls": [{"url": url}],
            "resultsLimit": 1,
        }

        print(f"🔍 [Apify] Scraping Facebook post: {url}")
        print(f"🔍 [Apify] Using actor: {actor_id}")

        # Run the sync Apify client in thread pool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        run = await loop.run_in_executor(
            _executor,
            lambda: self.client.actor(actor_id).call(run_input=run_input)
        )

        # Get the results (also sync, run in executor)
        items = await loop.run_in_executor(
            _executor,
            lambda: list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        )

        if not items:
            print("⚠️ [Apify] No items returned in dataset")
            return SocialScrapeResult(
                platform=SocialPlatform.FACEBOOK,
                url=url,
                author=None,
                text_content="",
                likes=None,
                comments=None,
                success=False,
                error_message="No data returned from Facebook scraper"
            )

        item = items[0]
        print(f"🐛 [Debug] Facebook Item Keys: {list(item.keys())}")
        print(f"🐛 [Debug] Facebook Item: {item}")

        # Extract text content - try multiple possible field names
        text_content = (
            item.get("text") or
            item.get("postText") or
            item.get("message") or
            item.get("content") or
            item.get("description") or
            ""
        )

        # Extract author - check multiple possible field names
        author = None
        if "user" in item and isinstance(item["user"], dict):
            author = item["user"].get("name") or item["user"].get("username")
        if not author:
            author = (
                item.get("pageName") or
                item.get("userName") or
                item.get("author") or
                item.get("name")
            )

        # Extract engagement metrics - Facebook uses various field names
        likes = (
            item.get("likes") or
            item.get("likesCount") or
            item.get("reactions") or
            item.get("reactionsCount")
        )
        comments = (
            item.get("comments") or
            item.get("commentsCount") or
            item.get("commentCount")
        )

        # Check if we got any content
        if not text_content:
            print(f"⚠️ [Apify] Facebook post has no text content. Full item: {item}")
            # Still return success if we got the item, just with empty text
            # Some posts might be image/video only

        print(f"✅ [Apify] Successfully scraped Facebook post. Text length: {len(str(text_content))}")

        return SocialScrapeResult(
            platform=SocialPlatform.FACEBOOK,
            url=url,
            author=author,
            text_content=str(text_content) if text_content else "",
            likes=likes,
            comments=comments,
            success=bool(text_content)  # Only success if we got text
        )

    async def _scrape_threads(self, url: str) -> SocialScrapeResult:
        """
        Scrape Threads post using sinam7/threads-post-scraper.

        This actor accepts post URLs directly and returns post data including:
        - caption: The post text content
        - user: Author information
        - like_count: Number of likes
        - reply_count: Number of replies
        """
        import re
        actor_id = self.ACTORS[SocialPlatform.THREADS]

        # Extract username for fallback author info
        username_match = re.search(r'threads\.(?:net|com)/@([\w.]+)', url)
        fallback_username = username_match.group(1) if username_match else None

        # Input for sinam7/threads-post-scraper - requires single URL
        # Clean URL by removing query parameters
        clean_url = url.split('?')[0]
        run_input = {
            "url": clean_url,
            "maxReplies": 0,  # We only need the main post, not replies
        }

        print(f"🔍 [Apify] Scraping Threads post: {url}")
        print(f"🔍 [Apify] Using actor: {actor_id}")

        # Run the sync Apify client in thread pool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        run = await loop.run_in_executor(
            _executor,
            lambda: self.client.actor(actor_id).call(run_input=run_input)
        )

        # Get the results (also sync, run in executor)
        items = await loop.run_in_executor(
            _executor,
            lambda: list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        )

        if not items:
            print("⚠️ [Apify] No items returned from Threads scraper")
            return SocialScrapeResult(
                platform=SocialPlatform.THREADS,
                url=url,
                author=fallback_username,
                text_content="",
                likes=None,
                comments=None,
                success=False,
                error_message="No data returned from Threads scraper"
            )

        # Log for debugging
        item = items[0]
        print(f"🐛 [Debug] Threads Item Keys: {list(item.keys())}")
        print(f"🐛 [Debug] Threads Item: {item}")

        # Extract text content - sinam7/threads-post-scraper uses 'content' field
        text_content = (
            item.get("content") or
            item.get("caption") or
            item.get("text") or
            item.get("post_text") or
            ""
        )

        # Handle caption that might be a dict with 'text' key
        if isinstance(text_content, dict):
            text_content = text_content.get("text", "")

        # Extract likes from content before cleaning
        # The scraper embeds like count at the end of content (e.g., "110")
        extracted_likes = None
        if text_content:
            lines = text_content.split('\n')
            # Check last few lines for a pure number (like count)
            for line in reversed(lines[-3:]):
                line_stripped = line.strip()
                if line_stripped.isdigit():
                    extracted_likes = int(line_stripped)
                    print(f"🐛 [Debug] Extracted likes from content: {extracted_likes}")
                    break

        # Clean up the content - remove metadata mixed in by the scraper
        # The scraper often includes: username, time, "Translate", like counts at the end
        if text_content:
            lines = text_content.split('\n')
            cleaned_lines = []
            skip_patterns = ['Translate', 'Reply', 'Share', 'More', 'Like', 'likes', 'View replies']

            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Skip first line if it looks like username (matches author)
                if i == 0 and fallback_username and fallback_username in line_stripped:
                    continue
                # Skip time patterns like "17h", "2d", "1w"
                if re.match(r'^\d+[hdwm]$', line_stripped):
                    continue
                # Skip UI elements
                if line_stripped in skip_patterns:
                    continue
                # Skip pure numbers (like counts, reply counts)
                if line_stripped.isdigit():
                    continue
                # Skip patterns like "110 likes" or "5 replies"
                if re.match(r'^\d+\s*(likes?|replies?|comments?)$', line_stripped, re.IGNORECASE):
                    continue
                # Skip empty lines and non-breaking spaces
                if not line_stripped or line_stripped == '\xa0\xa0':
                    continue
                # Skip if it's just the app name (like "OpenClaw") - only on line 1
                if i == 1 and len(line_stripped) < 20 and not any(c in line_stripped for c in '。，！？'):
                    continue

                cleaned_lines.append(line)

            text_content = '\n'.join(cleaned_lines).strip()

        # Extract author - check multiple possible field names
        author = None
        if "user" in item and isinstance(item["user"], dict):
            author = item["user"].get("username") or item["user"].get("name")
        if not author:
            author = (
                item.get("authorName") or
                item.get("authorId", "").replace("/@", "") or
                item.get("username") or
                item.get("author") or
                fallback_username
            )

        # Extract engagement metrics
        likes = (
            item.get("like_count") or
            item.get("likeCount") or
            item.get("likes") or
            extracted_likes  # Fallback to likes extracted from content
        )
        replies = (
            item.get("reply_count") or
            item.get("replyCount") or
            item.get("replies") or
            item.get("comments")
        )
        print(f"🐛 [Debug] Engagement metrics - Likes: {likes}, Replies: {replies}")

        # Check if we actually got content
        if not text_content:
            print(f"⚠️ [Apify] Threads post has no text content. Full item: {item}")
            return SocialScrapeResult(
                platform=SocialPlatform.THREADS,
                url=url,
                author=author,
                text_content="",
                likes=likes,
                comments=replies,
                success=False,
                error_message="Post has no text content (may be image/video only)"
            )

        print(f"✅ [Apify] Successfully scraped Threads post. Text length: {len(str(text_content))}")

        return SocialScrapeResult(
            platform=SocialPlatform.THREADS,
            url=url,
            author=author,
            text_content=str(text_content),
            likes=likes,
            comments=replies,
            success=True
        )
