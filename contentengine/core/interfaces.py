from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from contentengine.models.content import ContentOutput
from contentengine.models.task import CrawlTask


class IHttpClient(ABC):
    """Interface for HTTP client operations."""
    
    @abstractmethod
    async def get(self, url: str, headers: Dict[str, str]) -> httpx.Response:
        """Perform HTTP GET request."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the HTTP client."""
        pass


class IContentExtractor(ABC):
    """Interface for content extraction from web pages."""
    
    @abstractmethod
    def extract_content(self, url: str, soup: BeautifulSoup, styles: List[str], scripts: List[str]) -> ContentOutput:
        """Extract content from parsed HTML."""
        pass
    
    @abstractmethod
    def extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract links from HTML."""
        pass


class IAssetDownloader(ABC):
    """Interface for downloading and managing web assets."""
    
    @abstractmethod
    async def extract_and_download_assets(self, soup: BeautifulSoup, page_url: str, task: CrawlTask) -> Tuple[List[str], List[str]]:
        """Extract and download internal assets."""
        pass
    
    @abstractmethod
    def fix_asset_urls_in_html(self, html: str, page_url: str, styles: List[str], scripts: List[str], base_dir: str) -> str:
        """Fix asset URLs in HTML to point to local files."""
        pass


class IUrlNormalizer(ABC):
    """Interface for URL normalization and categorization."""
    
    @abstractmethod
    def normalize_url(self, base: str, href: str) -> Optional[str]:
        """Normalize URL."""
        pass
    
    @abstractmethod
    def categorize_url(self, url: str, root_base_domain: str) -> Tuple[Optional[str], Optional[str]]:
        """Categorize URL priority."""
        pass
    
    @abstractmethod
    def get_domain_info(self, url: str) -> Tuple[str, str]:
        """Get domain information."""
        pass


class IOutputWriter(ABC):
    """Interface for writing crawler outputs."""
    
    @abstractmethod
    def save_csv(self, csv_data: List[Dict[str, str]]):
        """Save CSV output."""
        pass
    
    @abstractmethod
    def save_json(self, content_outputs: List[ContentOutput]):
        """Save JSON output."""
        pass
    
    @abstractmethod
    async def save_html(self, url: str, html: str, styles: List[str], scripts: List[str]):
        """Save HTML page."""
        pass


class ITaskQueue(ABC):
    """Interface for task queue management."""
    
    @abstractmethod
    async def add_task(self, task: CrawlTask):
        """Add task to queue."""
        pass
    
    @abstractmethod
    async def get_task(self) -> CrawlTask:
        """Get next task from queue."""
        pass
    
    @abstractmethod
    async def join(self):
        """Wait for all tasks to complete."""
        pass
    
    @abstractmethod
    def task_done(self):
        """Mark task as done."""
        pass