"""
Web scraping functionality for F1 content
"""

import json
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from langchain.schema import Document

from src.utils.logger import app_logger
from src.utils.config import config


class F1ContentScraper:
    """Scraper for Formula 1 content from various sources"""
    
    def __init__(self):
        self.sources_file = "src/data/sources.json"
        self.metadata_file = "src/data/metadata.json"
        self.sources = self._load_sources()
        self.metadata = self._load_metadata()
    
    def _load_sources(self) -> Dict:
        """Load source configuration from JSON file"""
        try:
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            app_logger.error(f"Sources file not found: {self.sources_file}")
            return {}
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parsing sources JSON: {e}")
            return {}
    
    def _load_metadata(self) -> Dict:
        """Load metadata from JSON file"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            app_logger.info("No metadata file found, creating new one")
            return {"scraped_urls": {}, "last_updated": None}
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parsing metadata JSON: {e}")
            return {"scraped_urls": {}, "last_updated": None}
    
    def _save_metadata(self):
        """Save metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error saving metadata: {e}")
    
    def _extract_content_from_soup(self, soup: BeautifulSoup, url: str) -> str:
        """Extract clean text content from BeautifulSoup object"""
        config_extraction = self.sources.get("content_extraction", {})
        remove_elements = config_extraction.get("remove_elements", [])
        target_elements = config_extraction.get("target_elements", ["p", "h1", "h2", "h3", "h4", "li"])
        min_text_length = config_extraction.get("min_text_length", 50)
        
        # Remove unwanted elements
        for element_type in remove_elements:
            for element in soup.find_all(element_type):
                element.decompose()
        
        content_parts = []
        
        # Try to find main content area first
        main_content = (
            soup.find('div', {'id': 'mw-content-text'}) or  # Wikipedia
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', {'class': 'content'}) or
            soup.body
        )
        
        if not main_content:
            app_logger.warning(f"Could not find main content area for {url}")
            return ""
        
        # Extract text from target elements
        for element in main_content.find_all(target_elements):
            text = element.get_text().strip()
            if len(text) >= min_text_length:
                # Clean up the text
                text = ' '.join(text.split())  # Normalize whitespace
                content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def _scrape_single_url(self, url_info: Dict) -> Optional[Document]:
        """Scrape content from a single URL"""
        url = url_info["url"]
        title = url_info.get("title", "")
        category = url_info.get("category", "general")
        
        app_logger.info(f"Scraping: {title} ({url})")
        
        scraping_config = self.sources.get("scraping_config", {})
        headers = scraping_config.get("headers", {})
        timeout = scraping_config.get("timeout", 10)
        retry_count = scraping_config.get("retry_count", 3)
        
        for attempt in range(retry_count):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                content = self._extract_content_from_soup(soup, url)
                
                if not content:
                    app_logger.warning(f"No content extracted from {url}")
                    return None
                
                # Create document with metadata
                document = Document(
                    page_content=content,
                    metadata={
                        'source': url,
                        'title': title,
                        'category': category,
                        'scraped_at': datetime.now().isoformat(),
                        'content_length': len(content),
                        'priority': url_info.get("priority", 3)
                    }
                )
                
                # Update metadata
                self.metadata["scraped_urls"][url] = {
                    'title': title,
                    'category': category,
                    'scraped_at': datetime.now().isoformat(),
                    'content_length': len(content),
                    'status': 'success'
                }
                
                app_logger.success(f"Successfully scraped {title}: {len(content)} characters")
                return document
                
            except requests.RequestException as e:
                app_logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Update metadata with failure
                    self.metadata["scraped_urls"][url] = {
                        'title': title,
                        'category': category,
                        'scraped_at': datetime.now().isoformat(),
                        'status': 'failed',
                        'error': str(e)
                    }
                    app_logger.error(f"Failed to scrape {url} after {retry_count} attempts: {e}")
        
        return None
    
    def scrape_all_sources(self, force_refresh: bool = False) -> Tuple[List[Document], Dict]:
        """Scrape all configured sources"""
        app_logger.info("Starting F1 content scraping...")
        
        documents = []
        scraping_stats = {
            'total_urls': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'failed_urls': []
        }
        
        # Get all URLs from sources
        all_urls = []
        for source_type, source_config in self.sources.get("f1_sources", {}).items():
            urls = source_config.get("urls", [])
            all_urls.extend(urls)
        
        scraping_stats['total_urls'] = len(all_urls)
        
        # Sort by priority
        all_urls.sort(key=lambda x: x.get("priority", 3))
        
        scraping_config = self.sources.get("scraping_config", {})
        delay = scraping_config.get("delay_between_requests", 1)
        
        for i, url_info in enumerate(all_urls):
            url = url_info["url"]
            
            # Check if already scraped and not forcing refresh
            if not force_refresh and url in self.metadata.get("scraped_urls", {}):
                existing_data = self.metadata["scraped_urls"][url]
                if existing_data.get("status") == "success":
                    app_logger.info(f"Skipping {url} (already scraped)")
                    scraping_stats['skipped'] += 1
                    continue
            
            # Scrape the URL
            document = self._scrape_single_url(url_info)
            
            if document:
                documents.append(document)
                scraping_stats['successful'] += 1
            else:
                scraping_stats['failed'] += 1
                scraping_stats['failed_urls'].append({
                    'url': url,
                    'title': url_info.get('title', ''),
                    'error': 'Failed to extract content'
                })
            
            # Delay between requests to be respectful
            if i < len(all_urls) - 1:
                time.sleep(delay)
        
        # Update metadata
        self.metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata()
        
        app_logger.info(f"Scraping completed: {scraping_stats['successful']} successful, {scraping_stats['failed']} failed, {scraping_stats['skipped']} skipped")
        
        return documents, scraping_stats
    
    def get_scraping_status(self) -> Dict:
        """Get current scraping status and metadata"""
        return {
            'last_updated': self.metadata.get('last_updated'),
            'total_scraped': len(self.metadata.get('scraped_urls', {})),
            'scraped_urls': self.metadata.get('scraped_urls', {}),
            'available_sources': len([
                url for source in self.sources.get('f1_sources', {}).values() 
                for url in source.get('urls', [])
            ])
        }
    
    def clear_metadata(self):
        """Clear all scraping metadata"""
        self.metadata = {"scraped_urls": {}, "last_updated": None}
        self._save_metadata()
        app_logger.info("Cleared all scraping metadata")