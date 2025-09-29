"""Output writer service implementation."""

import csv
import json
import os
import re
from typing import Dict, List
from urllib.parse import urlparse

from contentengine.core.interfaces import IOutputWriter, IAssetDownloader
from contentengine.models.content import ContentOutput
from contentengine.utils.file_utils import FileUtils


class OutputWriterService(IOutputWriter):
    """Service for writing crawler outputs."""
    
    def __init__(self, asset_downloader: IAssetDownloader):
        self.asset_downloader = asset_downloader
    
    def save_csv(self, csv_data: List[Dict[str, str]]):
        """Write results to csv/{domain}.csv (one file per domain)."""
        FileUtils.ensure_directory("csv")
        
        # Group by domain
        domains: Dict[str, List[Dict[str, str]]] = {}
        for row in csv_data:
            domains.setdefault(row["domain"], []).append(row)

        fieldnames = ["title", "url", "domain", "root_domain", "priority", "crawled_at"]
        
        for domain, rows in domains.items():
            safe_domain = self._sanitize_domain_name(domain)
            csv_path = os.path.join("csv", f"{safe_domain}.csv")

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            print(f"Saved CSV: {csv_path}")
    
    def save_json(self, content_outputs: List[ContentOutput]):
        """Write ContentOutput per domain into json/{domain}.json (array)."""
        FileUtils.ensure_directory("json")

        # Group by domain
        groups: Dict[str, List[dict]] = {}
        for content_output in content_outputs:
            domain = urlparse(str(content_output.url)).netloc.lower()
            safe_domain = self._sanitize_domain_name(domain)
            groups.setdefault(safe_domain, []).append(content_output.model_dump(mode="json"))

        for domain, items in groups.items():
            json_path = os.path.join("json", f"{domain}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            print(f"Saved JSON: {json_path}")
    
    async def save_html(self, url: str, html: str, styles: List[str], scripts: List[str]):
        """Save HTML page with fixed asset URLs."""
        from ..utils.url_utils import UrlUtils
        
        domain, _ = self._get_domain_info(url)
        tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
        
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        # For root path, save directly as index.html in domain directory
        if not path:
            if parsed.query:
                # Use base64 encoding of full URL for directory name
                url_b64 = UrlUtils.generate_url_base64(url)
                base_dir = f"results/{tld}/{tld}.{domain_name}/index-{url_b64}"
                FileUtils.ensure_directory(base_dir)
                html_path = os.path.join(base_dir, "index.html")
            else:
                base_dir = f"results/{tld}/{tld}.{domain_name}"
                FileUtils.ensure_directory(base_dir)
                html_path = os.path.join(base_dir, "index.html")
        else:
            # For non-root paths, create directory structure
            safe_path = re.sub(r"[^\w\-./]", "_", path)
            if parsed.query:
                # Use base64 encoding of full URL for directory name
                url_b64 = UrlUtils.generate_url_base64(url)
                base_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}-{url_b64}"
            else:
                base_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}"
            
            FileUtils.ensure_directory(base_dir)
            html_path = os.path.join(base_dir, "index.html")
        
        FileUtils.ensure_directory(base_dir)

        # Fix asset URLs in HTML to point to local files
        fixed_html = self.asset_downloader.fix_asset_urls_in_html(html, url, styles, scripts, base_dir)
        
        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(fixed_html)
    
    def _sanitize_domain_name(self, domain: str) -> str:
        """Sanitize domain name for use as filename."""
        return re.sub(r"[^\w\-.]", "_", domain)
    
    def _get_domain_info(self, url: str) -> tuple:
        """Extract domain information from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Simple base domain extraction
        base_domain = domain[4:] if domain.startswith("www.") else domain
        return domain, base_domain