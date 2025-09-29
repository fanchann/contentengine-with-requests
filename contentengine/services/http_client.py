"""HTTP client service implementation."""

import time
from typing import Dict
import httpx

from contentengine.core.interfaces import IHttpClient
from contentengine.models.config import CrawlerConfig


class HttpClientService(IHttpClient):
    """HTTP client service using httpx."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.client: httpx.AsyncClient = None
        
    async def initialize(self):
        """Initialize the HTTP client."""
        timeout = httpx.Timeout(
            self.config.timeout_total,
            connect=self.config.timeout_connect,
            read=self.config.timeout_read
        )
        
        limits = httpx.Limits(
            max_connections=self.config.concurrency,
            max_keepalive_connections=self.config.concurrency
        )
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True
        )
    
    async def get(self, url: str, headers: Dict[str, str]) -> httpx.Response:
        """Perform HTTP GET request with enhanced headers."""
        if not self.client:
            await self.initialize()
            
        # Rotate user agent
        enhanced_headers = self._get_enhanced_headers()
        enhanced_headers.update(headers)
        enhanced_headers["User-Agent"] = self._get_rotated_user_agent()
        
        return await self.client.get(url, headers=enhanced_headers)
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
    
    def _get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced headers for better compatibility."""
        base_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        
        # Add custom headers from config
        base_headers.update(self.config.custom_headers)
        return base_headers
    
    def _get_rotated_user_agent(self) -> str:
        """Get rotated user agent based on time."""
        return self.config.user_agents[int(time.time()) % len(self.config.user_agents)]