"""Ultra-simplified Playwright HTTP client - ~150 lines."""

import asyncio
import os
import time
from typing import Dict, Optional
from urllib.parse import urlparse
import re

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response, Playwright
import async_timeout

from contentengine.core.interfaces import IHttpClient
from contentengine.models.config import CrawlerConfig
from contentengine.utils.url_utils import UrlUtils


class PlaywrightResponse:
    """Minimal response wrapper."""
    def __init__(self, response: Response, text: str, binary: bytes = None):
        self._text, self._content = text, binary
        self.status_code, self.headers, self.url = response.status, dict(response.headers), response.url
        self.http_version, self.history, self.screenshot_path = "HTTP/1.1", [], None
        
    @property
    def text(self) -> str:
        return self._text
    
    @property  
    def content(self) -> bytes:
        return self._content if self._content else self._text.encode('utf-8')
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code} for {self.url}")


class PlaywrightHttpClientService(IHttpClient):
    """Ultra-simplified Playwright HTTP client."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.playwright, self.browser, self.context = None, None, None
        self._semaphore = asyncio.Semaphore(3)
        
    async def initialize(self):
        """Quick initialization."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            browser_args = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process']
            self.browser = await self.playwright.chromium.launch(
                headless=bool(int(os.environ.get("CRAWLENGINE_HEADLESS", "1"))), 
                args=browser_args, timeout=60000)
            
            user_agent = self.config.user_agents[int(time.time()) % len(self.config.user_agents)]
            headers = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8", **self.config.custom_headers}
            
            self.context = await self.browser.new_context(
                user_agent=user_agent, viewport={'width': 1920, 'height': 1080},
                extra_http_headers=headers, ignore_https_errors=True)
            self.context.set_default_timeout(30000)
            print("Playwright initialized")
    
    async def get(self, url: str, headers: Dict[str, str]) -> PlaywrightResponse:
        """Simple GET with basic optimization."""
        async with self._semaphore:
            if not self.context:
                await self.initialize()
            
            page = None
            try:
                page = await self.context.new_page()
                if headers:
                    await page.set_extra_http_headers(headers)
                
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                if not response:
                    raise Exception(f"Failed to load: {url}")
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    await self._quick_wait(page)
                    content = await page.content()
                    screenshot_path = await self._quick_screenshot(page, url)
                    binary = None
                else:
                    content, binary, screenshot_path = "", await response.body(), None
                
                result = PlaywrightResponse(response, content, binary)
                if screenshot_path:
                    result.screenshot_path = screenshot_path
                if str(response.url) != url:
                    result.history = [url]
                
                return result
                
            except Exception as e:
                print(f"Error: {e}")
                raise
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
    
    async def _quick_wait(self, page: Page):
        """Minimal resource waiting."""
        try:
            # Wait for page ready
            async with async_timeout.timeout(15):
                while await page.evaluate("document.readyState") != "complete":
                    await asyncio.sleep(0.5)
            
            # Quick resource checks
            tasks = [
                page.wait_for_function("() => Array.from(document.querySelectorAll('link[rel=\"stylesheet\"]')).every(l => l.sheet)", timeout=5000),
                page.wait_for_function("document.fonts.ready", timeout=3000)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            print("Page ready with resources")
        except:
            print("Quick wait timeout")
    
    async def _quick_screenshot(self, page: Page, url: str) -> Optional[str]:
        """Minimal screenshot logic."""
        if not self.config.enable_screenshots:
            return None
            
        try:
            # Quick rendering optimization
            await page.evaluate("() => { document.body.style.display='none'; document.body.offsetHeight; document.body.style.display=''; }")
            await page.wait_for_timeout(500)
            
            # Generate path
            domain, _ = UrlUtils.get_domain_info(url)
            tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            
            if path:
                safe_path = re.sub(r"[^\w\-./]", "_", path)
                screenshot_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}"
            else:
                screenshot_dir = f"results/{tld}/{tld}.{domain_name}"
            
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"screenshot.{self.config.screenshot_format}")
            
            await page.screenshot(
                path=screenshot_path,
                quality=self.config.screenshot_quality if self.config.screenshot_format == 'jpeg' else None,
                full_page=True, type=self.config.screenshot_format)
            
            print(f"Screenshot: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    async def close(self):
        """Clean shutdown."""
        for resource in [self.context, self.browser, self.playwright]:
            if resource:
                try:
                    await resource.close() if hasattr(resource, 'close') else await resource.stop()
                except:
                    pass
        print("Playwright closed")