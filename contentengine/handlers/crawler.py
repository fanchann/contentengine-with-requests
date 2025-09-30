import asyncio
import time
from typing import Dict, List, Set, Optional
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
        task_queue: ITaskQueue,
        s3_service=None
    ):
        # Dependencies (injected)
        self.config = config
        self.http_client = http_client
        self.url_normalizer = url_normalizer
        self.content_extractor = content_extractor
        self.asset_downloader = asset_downloader
        self.output_writer = output_writer
        self.task_queue = task_queue
        self.s3_service = s3_service
        
        # State
        self.visited: Set[str] = set()
        self.csv_data: List[Dict[str, str]] = []
        self.content_outputs: List[ContentOutput] = []
        self.lock = asyncio.Lock()
        self.start_time: Optional[float] = None
    
    async def crawl_async(self, start_url: str) -> List[ContentOutput]:
        """Main crawling method."""
        # Initialize start time for timeout tracking
        self.start_time = time.time()
        
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
        # Check timeout and visited status
        async with self.lock:
            # Check if timeout has been exceeded
            if self.start_time and (time.time() - self.start_time) * 1000 > self.config.timeout_ms:
                print(f"Crawling timeout reached ({self.config.timeout_ms}ms), stopping")
                return
            
            if task.url in self.visited:
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
            
            # Upload HTML to S3 if available
            if self.s3_service:
                await self._upload_html_to_s3(task.url)
            
            # Extract content
            content_output = self.content_extractor.extract_content(
                task.url, soup, styles, scripts, response
            )
            self.content_outputs.append(content_output)
            
            # Upload screenshot to S3 if available
            if self.s3_service and content_output.screenshot_path:
                s3_url = await self._upload_screenshot_to_s3(content_output.screenshot_path, task.url)
                if s3_url:
                    content_output.screenshot_path = s3_url
            
            # Upload assets to S3 if available
            if self.s3_service:
                await self._upload_assets_to_s3(task.url)
            
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
        # Check if timeout has been exceeded before processing more links
        if self.start_time and (time.time() - self.start_time) * 1000 > self.config.timeout_ms:
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
            
            # Create child task (depth is no longer used for limiting, just for tracking)
            child_task = CrawlTask(
                url=absolute_url,
                priority=priority,
                depth=task.depth + 1,  # Still track depth for informational purposes
                root_domain=task.root_domain or f"{urlparse(task.url).scheme}://{urlparse(task.url).netloc}",
                parent_domain=current_domain,
                root_base_domain=task.root_base_domain,
            )
            
            await self.task_queue.add_task(child_task)
    
    async def _save_outputs(self):
        """Save all outputs."""
        self.output_writer.save_csv(self.csv_data)
        self.output_writer.save_json(self.content_outputs)
    
    async def _upload_screenshot_to_s3(self, screenshot_path: str, url: str) -> Optional[str]:
        """Upload screenshot to S3 and return the public URL."""
        try:
            if screenshot_path and self.s3_service:
                public_url = self.s3_service.upload_screenshot(screenshot_path, url)
                if public_url:
                    print(f"Screenshot uploaded to S3: {public_url}")
                    return public_url
        except Exception as e:
            print(f"Failed to upload screenshot to S3: {e}")
        return None
    
    async def _upload_html_to_s3(self, url: str):
        """Upload HTML file to S3."""
        try:
            if not self.s3_service:
                return
                
            # Get HTML file path based on URL structure
            from contentengine.utils.url_utils import UrlUtils
            from urllib.parse import urlparse
            import os
            
            domain, _ = UrlUtils.get_domain_info(url)
            tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
            
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            
            # Determine HTML file path
            if not path:
                if parsed.query:
                    url_b64 = UrlUtils.generate_url_base64(url)
                    html_path = f"results/{tld}/{tld}.{domain_name}/index-{url_b64}.html"
                else:
                    html_path = f"results/{tld}/{tld}.{domain_name}/index.html"
            else:
                import re
                safe_path = re.sub(r"[^\w\-./]", "_", path)
                if parsed.query:
                    url_b64 = UrlUtils.generate_url_base64(url)
                    html_path = f"results/{tld}/{tld}.{domain_name}/{safe_path}-{url_b64}.html"
                else:
                    html_path = f"results/{tld}/{tld}.{domain_name}/{safe_path}.html"
            
            # Upload HTML file
            if os.path.exists(html_path):
                public_url = self.s3_service.upload_html(html_path, url)
                if public_url:
                    print(f"HTML uploaded to S3: {os.path.basename(html_path)}")
            
        except Exception as e:
            print(f"Failed to upload HTML to S3: {e}")
    
    async def _upload_assets_to_s3(self, url: str):
        """Upload assets to S3."""
        try:
            if not self.s3_service:
                return
                
            # Get asset directory based on URL structure
            from contentengine.utils.url_utils import UrlUtils
            from urllib.parse import urlparse
            import os
            
            domain, _ = UrlUtils.get_domain_info(url)
            tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
            
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            
            # Determine asset directory path
            if not path:
                if parsed.query:
                    url_b64 = UrlUtils.generate_url_base64(url)
                    asset_dir = f"results/{tld}/{tld}.{domain_name}/index-{url_b64}/assets"
                else:
                    asset_dir = f"results/{tld}/{tld}.{domain_name}/assets"
            else:
                import re
                safe_path = re.sub(r"[^\w\-./]", "_", path)
                if parsed.query:
                    url_b64 = UrlUtils.generate_url_base64(url)
                    asset_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}-{url_b64}/assets"
                else:
                    asset_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}/assets"
            
            # Upload all assets in directory
            if os.path.exists(asset_dir):
                for root, dirs, files in os.walk(asset_dir):
                    for file in files:
                        asset_path = os.path.join(root, file)
                        public_url = self.s3_service.upload_asset(asset_path, url, url)
                        if public_url:
                            print(f"Asset uploaded to S3: {file}")
                            
        except Exception as e:
            print(f"Failed to upload assets to S3: {e}")