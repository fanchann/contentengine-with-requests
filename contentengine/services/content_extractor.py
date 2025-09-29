from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from contentengine.core.interfaces import IContentExtractor
from contentengine.models.content import ContentOutput, MetaTag
from contentengine.utils.file_utils import FileUtils


class ContentExtractorService(IContentExtractor):
    """Service for extracting content from web pages."""
    
    def extract_content(self, url: str, soup: BeautifulSoup, styles: List[str], scripts: List[str]) -> ContentOutput:
        """Extract content from parsed HTML."""
        title = self._extract_title(soup)
        metatags = self._extract_metatags(soup)
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)
        
        return ContentOutput(
            url=url,
            title=title,
            metatags=metatags if metatags else None,
            images=images if images else None,
            links=links if links else None,
            scripts=FileUtils.uniq_list(scripts)[:1000] if scripts else None,
            styles=FileUtils.uniq_list(styles)[:1000] if styles else None,
        )
    
    def extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all links from HTML."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href:
                links.append(href)
        return links
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find("title")
        return title_tag.get_text(strip=True) if title_tag else ""
    
    def _extract_metatags(self, soup: BeautifulSoup) -> List[MetaTag]:
        """Extract meta tags."""
        metatags = []
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or ""
            content = meta.get("content") or ""
            if name and content:
                metatags.append(MetaTag(name=name, content=content))
        return metatags
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs."""
        images = []
        for img in soup.find_all("img"):
            contentengine = img.get("contentengine")
            if contentengine:
                absolute_url = urljoin(base_url, contentengine)
                images.append(absolute_url)
        return FileUtils.uniq_list(images)[:500]
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract link URLs."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href:
                absolute_url = urljoin(base_url, href)
                links.append(absolute_url)
        return FileUtils.uniq_list(links)[:5000]