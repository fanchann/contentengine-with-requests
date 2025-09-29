from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from contentengine.core.interfaces import IContentExtractor
from contentengine.models.content import ContentOutput, MetaTag
from contentengine.utils.file_utils import FileUtils


class ContentExtractorService(IContentExtractor):
    """Service for extracting content from web pages."""
    
    def extract_content(self, url: str, soup: BeautifulSoup, styles: List[str], scripts: List[str], response: Optional[object] = None) -> ContentOutput:
        """Extract content from parsed HTML."""
        title = self._extract_title(soup)
        metatags = self._extract_metatags(soup)
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)
        
        # Extract HTTP headers if response is provided
        http_headers = None
        screenshot_path = None
        if response:
            http_headers = self._extract_http_headers(response)
            # Get screenshot path if available
            if hasattr(response, 'screenshot_path'):
                screenshot_path = response.screenshot_path
        
        return ContentOutput(
            url=url,
            title=title,
            http_headers=http_headers,
            metatags=metatags if metatags else None,
            images=images if images else None,
            links=links if links else None,
            scripts=FileUtils.uniq_list(scripts)[:1000] if scripts else None,
            stylesheets=FileUtils.uniq_list(styles)[:1000] if styles else None,
            screenshot_path=screenshot_path,
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
    
    def _extract_http_headers(self, response: object) -> Dict[str, str]:
        """Extract HTTP headers from response."""
        # Convert headers to dictionary, keeping important headers
        headers_dict = {}
        
        # Handle both httpx.Response and PlaywrightResponse
        if hasattr(response, 'headers'):
            # Handle headers - could be dict or Headers object
            if hasattr(response.headers, 'items'):
                for header_name, header_value in response.headers.items():
                    headers_dict[header_name.lower()] = header_value
            else:
                # Assume it's already a dict
                for header_name, header_value in response.headers.items():
                    headers_dict[header_name.lower()] = header_value
        
        # Add status code and HTTP version
        if hasattr(response, 'status_code'):
            headers_dict['_status_code'] = str(response.status_code)
        
        if hasattr(response, 'http_version'):
            headers_dict['_http_version'] = response.http_version
        
        if hasattr(response, 'url'):
            headers_dict['_url'] = str(response.url)
        
        # Add redirect history if any
        if hasattr(response, 'history') and response.history:
            if isinstance(response.history, list):
                headers_dict['_redirect_history'] = [str(url) for url in response.history]
            else:
                redirect_urls = [str(r.url) for r in response.history]
                headers_dict['_redirect_history'] = redirect_urls
        
        return headers_dict