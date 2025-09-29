import asyncio
from typing import Dict, List, Set
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from contentengine.core.interfaces import (
    IHttpClient, IContentExtractor, IAssetDownloader, 
    IUrlNormalizer, IOutputWriter, ITaskQueue
)
from contentengine.models.task import CrawlTask
from contentengine.models.content import ContentOutput
from contentengine.models.config import CrawlerConfig


class PriorityCrawler:
    """Main crawler class implementing dependency injection and SOLID principles."""
    
    def __init__(
        self,
        config: CrawlerConfig,
        http_client: IHttpClient,
        url_normalizer: IUrlNormalizer,
        content_extractor: IContentExtractor,
        asset_downloader: IAssetDownloader,
        output_writer: IOutputWriter,
        task_queue: ITaskQueue
    ):
        # Dependencies (injected)
        self.config = config
        self.http_client = http_client
        self.url_normalizer = url_normalizer
        self.content_extractor = content_extractor
        self.asset_downloader = asset_downloader
        self.output_writer = output_writer
        self.task_queue = task_queue
        
        # State
        self.visited: Set[str] = set()
        self.csv_data: List[Dict[str, str]] = []
        self.content_outputs: List[ContentOutput] = []
        self.lock = asyncio.Lock()
    
    async def crawl_async(self, start_url: str) -> List[ContentOutput]:
        """Main crawling method."""
        # Create seed task
        seed_task = self._create_seed_task(start_url)
        await self.task_queue.add_task(seed_task)
        
        # Initialize HTTP client
        if hasattr(self.http_client, 'initialize'):
            await self.http_client.initialize()
        
        try:
            # Start workers
            workers = [
                asyncio.create_task(self._worker()) 
                for _ in range(self.config.concurrency)
            ]
            
            # Wait for all tasks to complete
            await self.task_queue.join()
            
            # Cancel workers
            for worker in workers:
                worker.cancel()
            
            # Ensure cancellation
            await asyncio.gather(*workers, return_exceptions=True)
            
            # Save outputs
            await self._save_outputs()
            
            print(f"\\nCrawling completed! Visited {len(self.visited)} pages.")
            return self.content_outputs
            
        finally:
            await self.http_client.close()
    
    async def _worker(self):
        """Worker coroutine for processing tasks."""
        while True:
            try:
                task = await self.task_queue.get_task()
                await self._crawl_page(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker error: {e}")
            finally:
                self.task_queue.task_done()
    
    async def _crawl_page(self, task: CrawlTask):
        """Crawl a single page."""
        # Check depth and visited status
        async with self.lock:
            if task.url in self.visited or task.depth > self.config.max_depth:
                return
            self.visited.add(task.url)
        
        try:
            print(f"Crawling: {task.url} (Priority: {task.priority}, Depth: {task.depth})")
            
            # Fetch page
            response = await self.http_client.get(task.url, {})
            response.raise_for_status()
            
            # Validate content type
            if not self._is_html_content(response, task.url):
                return
            
            # Parse HTML
            html = response.text
            soup = self._parse_html(html, task.url)
            if not soup:
                return
            
            # Extract and download assets
            styles, scripts = await self.asset_downloader.extract_and_download_assets(
                soup, task.url, task
            )
            
            # Save HTML page
            await self.output_writer.save_html(task.url, html, styles, scripts)
            
            # Extract content
            content_output = self.content_extractor.extract_content(
                task.url, soup, styles, scripts, response
            )
            self.content_outputs.append(content_output)
            
            # Add to CSV data
            self._add_csv_row(task, content_output)
            
            # Extract and queue new URLs
            await self._process_discovered_links(soup, task)
            
            # Apply delay if configured
            if self.config.delay > 0:
                await asyncio.sleep(self.config.delay)
                
        except Exception as e:
            print(f"Error crawling {task.url}: {str(e)}")
    
    def _create_seed_task(self, start_url: str) -> CrawlTask:
        """Create the initial seed task."""
        domain, base_domain = self.url_normalizer.get_domain_info(start_url)
        
        return CrawlTask(
            url=start_url,
            priority="high",
            depth=0,
            root_domain=None,  # Keep empty for seed
            parent_domain=domain,
            root_base_domain=base_domain,
        )
    
    def _is_html_content(self, response, url: str) -> bool:
        """Check if response contains HTML content."""
        content_type = response.headers.get("Content-Type", "").lower()
        
        # Check for HTML content more broadly
        is_html = (
            "text/html" in content_type or 
            "application/xhtml+xml" in content_type or
            "application/xml" in content_type or
            # Sometimes servers don't set proper content-type
            (not content_type and response.text.strip().startswith("<")) or
            # Handle cases where content-type is missing but URL suggests HTML
            (not content_type and any(url.endswith(ext) for ext in [".html", ".htm", ".php", ".asp", ".jsp"]))
        )
        
        if not is_html:
            print(f"Skipping non-HTML content: {content_type} for {url}")
            return False
        
        return True
    
    def _parse_html(self, html: str, url: str) -> BeautifulSoup:
        """Parse HTML with error handling."""
        if not html or not html.strip():
            print(f"Empty content for {url}")
            return None
            
        try:
            soup = BeautifulSoup(html, "html.parser")
            if not soup or not soup.find():
                print(f"Failed to parse HTML for {url}")
                return None
            return soup
        except Exception as e:
            print(f"HTML parsing error for {url}: {e}")
            return None
    
    def _add_csv_row(self, task: CrawlTask, content_output: ContentOutput):
        """Add row to CSV data."""
        domain, _ = self.url_normalizer.get_domain_info(task.url)
        
        self.csv_data.append({
            "title": content_output.title,
            "url": task.url,
            "domain": domain,
            "root_domain": task.root_domain or "",
            "priority": task.priority,
            "crawled_at": datetime.now().isoformat(),
        })
    
    async def _process_discovered_links(self, soup: BeautifulSoup, task: CrawlTask):
        """Process discovered links and add new tasks."""
        if task.depth >= self.config.max_depth:
            return
        
        links = self.content_extractor.extract_links(soup)
        current_domain, current_base = self.url_normalizer.get_domain_info(task.url)
        
        for link in links:
            absolute_url = self.url_normalizer.normalize_url(task.url, link)
            if not absolute_url:
                continue
            
            # Validate URL
            parsed = urlparse(absolute_url)
            if parsed.scheme not in ["http", "https"] or not parsed.netloc:
                continue
            
            # Categorize URL and determine priority
            priority, _ = self.url_normalizer.categorize_url(absolute_url, task.root_base_domain)
            if not priority:
                continue
            
            # Create child task
            child_task = CrawlTask(
                url=absolute_url,
                priority=priority,
                depth=task.depth + 1,
                root_domain=task.root_domain or f"{urlparse(task.url).scheme}://{urlparse(task.url).netloc}",
                parent_domain=current_domain,
                root_base_domain=task.root_base_domain,
            )
            
            await self.task_queue.add_task(child_task)
    
    async def _save_outputs(self):
        """Save all outputs."""
        self.output_writer.save_csv(self.csv_data)
        self.output_writer.save_json(self.content_outputs)