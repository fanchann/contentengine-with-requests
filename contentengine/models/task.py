from dataclasses import dataclass
from typing import Optional


@dataclass
class CrawlTask:
    """Task definition for crawling a URL."""
    url: str
    priority: str  # high, medium, low
    depth: int
    root_domain: Optional[str]  # for CSV column; keep None on seed to match sample
    parent_domain: str
    root_base_domain: str  # base domain of the start target (e.g., gorm.io)