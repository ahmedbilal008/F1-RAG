"""Wikipedia scraper for F1 content using trafilatura with BS4 fallback."""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

import requests
import trafilatura

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("wikipedia_scraper")

WIKIPEDIA_SOURCES: List[Dict[str, Any]] = [
    # Current & upcoming seasons
    {"url": "https://en.wikipedia.org/wiki/2025_Formula_One_World_Championship", "title": "2025 F1 Season", "category": "season", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/2026_Formula_One_World_Championship", "title": "2026 F1 Season", "category": "season", "priority": 1},
    # Teams — includes new 2026 entrants
    {"url": "https://en.wikipedia.org/wiki/Red_Bull_Racing", "title": "Red Bull Racing", "category": "team", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/Scuderia_Ferrari", "title": "Ferrari", "category": "team", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/McLaren", "title": "McLaren", "category": "team", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One", "title": "Mercedes F1", "category": "team", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/Cadillac_in_Formula_One", "title": "Cadillac F1 (2026 Entry)", "category": "team", "priority": 1},
    {"url": "https://en.wikipedia.org/wiki/Audi_in_Formula_One", "title": "Audi F1 (Sauber Takeover)", "category": "team", "priority": 1},
    # 2026 regulations — major rule overhaul (active aero, new PU, no DRS)
    {"url": "https://en.wikipedia.org/wiki/2026_Formula_One_regulations", "title": "2026 F1 Regulations", "category": "regulations", "priority": 1},
]


@dataclass
class ScrapedDocument:
    """Raw scraped document before chunking."""
    content: str
    title: str
    url: str
    category: str
    priority: int
    scraped_at: str
    content_length: int


class WikipediaScraper:
    """Scrapes F1 content from Wikipedia using trafilatura."""

    def __init__(self):
        settings = get_settings()
        self._delay = settings.SCRAPE_DELAY
        self._timeout = settings.SCRAPE_TIMEOUT
        self._retries = settings.SCRAPE_RETRIES
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def _fetch_and_extract(self, url: str) -> Optional[str]:
        """Fetch a URL and extract main content using trafilatura."""
        for attempt in range(self._retries):
            try:
                response = requests.get(
                    url, headers=self._headers, timeout=self._timeout
                )
                response.raise_for_status()

                # trafilatura extracts clean article text
                content = trafilatura.extract(
                    response.text,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                    favor_recall=True,
                )

                if content and len(content) > 100:
                    return content

                # Fallback: basic extraction
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.content, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                main = (
                    soup.find("div", {"id": "mw-content-text"})
                    or soup.find("main")
                    or soup.find("article")
                    or soup.body
                )
                if main:
                    text = main.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return text

                logger.warning(f"No content extracted from {url}")
                return None

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self._retries - 1:
                    time.sleep(2 ** attempt)

        logger.error(f"All {self._retries} attempts failed for {url}")
        return None

    def scrape_all(
        self, force_refresh: bool = False, scraped_urls: Optional[set] = None
    ) -> tuple[List[ScrapedDocument], Dict[str, Any]]:
        """Scrape all configured Wikipedia sources."""
        scraped = scraped_urls or set()
        documents: List[ScrapedDocument] = []
        stats = {"total": len(WIKIPEDIA_SOURCES), "success": 0, "failed": 0, "skipped": 0, "errors": []}

        # Sort by priority
        sources = sorted(WIKIPEDIA_SOURCES, key=lambda s: s["priority"])

        for i, source in enumerate(sources):
            url = source["url"]

            if not force_refresh and url in scraped:
                stats["skipped"] += 1
                continue

            content = self._fetch_and_extract(url)

            if content:
                doc = ScrapedDocument(
                    content=content,
                    title=source["title"],
                    url=url,
                    category=source["category"],
                    priority=source["priority"],
                    scraped_at=datetime.utcnow().isoformat(),
                    content_length=len(content),
                )
                documents.append(doc)
                stats["success"] += 1
                logger.info(f"Scraped {source['title']}: {len(content)} chars")
            else:
                stats["failed"] += 1
                stats["errors"].append(f"Failed: {source['title']} ({url})")

            # Rate limiting
            if i < len(sources) - 1:
                time.sleep(self._delay)

        logger.info(
            f"Wikipedia scraping complete: {stats['success']} ok, "
            f"{stats['failed']} failed, {stats['skipped']} skipped"
        )
        return documents, stats
