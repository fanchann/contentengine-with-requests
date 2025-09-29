from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from httpx import URL
from typing import Any
from contentengine.core.interfaces import IContentExtractor
from contentengine.models.content import ContentOutput, MetaTag
from contentengine.utils.file_utils import FileUtils

def uri_fixer(src: str, base_url: URL) -> str:
    if src.startswith("data:"):
        return src
    if src.startswith(("http://", "https://")):
        return src
    else:
        return str(base_url.join(src))

class ContentExtractorService(IContentExtractor):
    """Service for extracting content from web pages."""
    
    def extract_content(self, url: str, soup: BeautifulSoup, styles: List[str], scripts: List[str], response: Optional[object] = None) -> ContentOutput:
        """Extract content from parsed HTML."""
        title = self.get_title(soup)
        metatags = self.get_metatags(soup)
        images = self.get_images(soup, url)
        links = self.get_links(soup, url)
        stylesheets = self.get_stylesheets(soup, url)
        scripts = self.get_scripts(soup, url)

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
            scripts=scripts if scripts else None,
            stylesheets=stylesheets if stylesheets else None,
            screenshot_path=screenshot_path,
        )
    
    def extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract links from HTML."""
        return self.get_links(soup, None)  # URL will be handled in get_links
    
    def get_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML."""
        tag = soup.find("title")
        return tag.get_text().strip() if tag else ""

    def get_metatags(self, soup: BeautifulSoup) -> List[MetaTag]:
        """Extract meta tags from HTML."""
        metatags = []
        for tag in soup.find_all("meta"):
            meta_name = tag.get("name")
            meta_content = tag.get("content")
            if meta_name and meta_content:
                metatags.append(MetaTag(name=meta_name, content=meta_content))
        return metatags

    def get_images(self, soup: BeautifulSoup, url: str) -> List[str]:
        """Get all image urls

        References:

        - https://www.w3schools.com/html/html_images.asp

        Returns:
            list[str]: List of image urls
        """
        base_url = URL(url)
        images = set()
        
        for tag in soup.find_all("img"):
            src = tag.get("src")
            if src:
                fixed_src = uri_fixer(src, base_url)
                images.add(fixed_src)

        for tag in soup.find_all("source"):
            src = tag.get("srcset")
            if src:
                fixed_src = uri_fixer(src, base_url)
                images.add(fixed_src)

        return list(images)

    def get_links(self, soup: BeautifulSoup, url: Optional[str]) -> List[str]:
        """Extract links from HTML."""
        links = set()
        base_url = URL(url) if url else None
        
        for tag in soup.find_all("a"):
            href = tag.get("href")
            if href:
                if href.startswith(("http://", "https://")):
                    links.add(href)
                elif base_url:
                    href = str(base_url.join(href))
                    links.add(href)
        return list(links)

    def get_text_body(self, soup: BeautifulSoup) -> str:
        """Extract text content from body."""
        body_tag = soup.find("body")
        if body_tag is None:
            return ""

        # Remove script and style tags
        for tag in body_tag.find_all("script"):
            tag.decompose()
        for tag in body_tag.find_all("style"):
            tag.decompose()
        return body_tag.get_text(strip=True)

    def get_scripts(self, soup: BeautifulSoup, url: str) -> List[str]:
        """Extract script URLs from HTML."""
        base_url = URL(url)
        scripts = set()
        
        for tag in soup.find_all("script"):
            src = tag.get("src")
            if src:
                fixed_src = uri_fixer(src, base_url)
                scripts.add(fixed_src)
        return list(scripts)

    def get_stylesheets(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract stylesheet information from HTML."""
        base_url = URL(url)
        stylesheets = []
        
        for tag in soup.find_all("link"):
            href = tag.get("href")
            if href:
                if not href.startswith(("http://", "https://")):
                    href = str(base_url.join(href))

                attrs = dict(tag.attrs)
                attrs["href"] = href
                stylesheets.append(attrs)
        return stylesheets
    
    def _extract_http_headers(self, response: object) -> Optional[Dict[str, str]]:
        """Extract HTTP headers from response object."""
        if hasattr(response, 'headers'):
            return dict(response.headers)
        return None
