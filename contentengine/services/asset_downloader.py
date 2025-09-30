import asyncio
import os
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from contentengine.core.interfaces import IAssetDownloader, IHttpClient
from contentengine.models.task import CrawlTask
from contentengine.utils.url_utils import UrlUtils
from contentengine.utils.file_utils import FileUtils
from contentengine.services.s3_service import S3Service


class AssetDownloaderService(IAssetDownloader):
    """Service for downloading and managing web assets."""
    
    def __init__(self, http_client: IHttpClient, url_normalizer, s3_service: Optional[S3Service] = None):
        self.http_client = http_client
        self.url_normalizer = url_normalizer
        self.s3_service = s3_service
    
    async def extract_and_download_assets(self, soup: BeautifulSoup, page_url: str, task: CrawlTask) -> Tuple[List[str], List[str]]:
        """Extract and download internal assets (CSS/JS only from same domain/subdomain)."""
        styles, scripts = self._extract_asset_urls(soup, page_url)
        
        # Filter only internal assets
        styles = self._filter_internal_assets(styles, task.root_base_domain)
        scripts = self._filter_internal_assets(scripts, task.root_base_domain)
        
        print(f"After filtering: {len(styles)} internal CSS files and {len(scripts)} internal JS files")
        
        if not styles and not scripts:
            return styles, scripts
        
        # Setup download directory
        download_dir = self._setup_download_directory(page_url)
        
        # Download assets in parallel
        await self._download_assets_parallel(styles, scripts, page_url, download_dir)
        
        return styles, scripts
    
    async def download_favicon(self, soup: BeautifulSoup, page_url: str) -> Optional[str]:
        """Download favicon and return path to saved file."""
        from contentengine.services.content_extractor import ContentExtractorService
        
        # Use ContentExtractorService to get favicon URL
        extractor = ContentExtractorService()
        favicon_url = extractor.get_favicon_url(soup, page_url)
        
        if not favicon_url:
            return None
        
        try:
            # Setup download directory structure same as page
            base_dir = self._setup_download_directory(page_url)
            
            # Create favicon directory
            favicon_dir = os.path.join(base_dir, "favicon")
            FileUtils.ensure_directory(favicon_dir)
            
            # Determine file extension
            parsed_favicon = urlparse(favicon_url)
            filename = os.path.basename(parsed_favicon.path) or "favicon.ico"
            if not os.path.splitext(filename)[1]:
                filename += ".ico"  # Default extension for favicons
            
            favicon_path = os.path.join(favicon_dir, filename)
            
            # Skip if already exists and not empty
            if os.path.exists(favicon_path) and os.path.getsize(favicon_path) > 0:
                return favicon_path
            
            # Download favicon
            headers = {
                "Accept": "image/*,*/*;q=0.8",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            response = await self.http_client.get(favicon_url, headers)
            response.raise_for_status()
            
            # Validate and save content
            if len(response.content) > 0:
                with open(favicon_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded favicon: {favicon_path}")
                return favicon_path
            else:
                print(f"Empty favicon content for {favicon_url}")
                
        except Exception as e:
            print(f"Failed to download favicon {favicon_url}: {e}")
        
        return None
    
    def fix_asset_urls_in_html(self, html: str, page_url: str, styles: List[str], scripts: List[str], base_dir: str) -> str:
        """Fix asset URLs in HTML to point to downloaded local files."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Create mapping of original URLs to local paths
            url_to_local = self._create_url_mapping(styles, scripts, page_url, base_dir)
            
            # Replace CSS links
            self._replace_css_links(soup, page_url, url_to_local)
            
            # Replace script sources
            self._replace_script_sources(soup, page_url, url_to_local)
            
            # Fix inline CSS @import statements
            self._fix_inline_css(soup, url_to_local)
            
            return str(soup)
        except Exception as e:
            print(f"Error fixing asset URLs: {e}")
            return html
    
    def _extract_asset_urls(self, soup: BeautifulSoup, page_url: str) -> Tuple[List[str], List[str]]:
        """Extract CSS and JS URLs from HTML."""
        styles = []
        scripts = []
        
        # Check for base tag
        base_tag = soup.find("base", href=True)
        base_url = urljoin(page_url, base_tag["href"]) if base_tag else page_url
        
        # Extract CSS links
        for link in soup.find_all("link", href=True):
            if self._is_stylesheet_link(link):
                href = link.get("href")
                if self._is_valid_asset_url(href):
                    absolute_url = urljoin(base_url, href)
                    styles.append(absolute_url)
        
        # Extract JavaScript files
        for script in soup.find_all("script", contentengine=True):
            contentengine = script.get("contentengine")
            if self._is_valid_asset_url(contentengine):
                absolute_url = urljoin(base_url, contentengine)
                scripts.append(absolute_url)
        
        return FileUtils.uniq_list(styles), FileUtils.uniq_list(scripts)
    
    def _is_stylesheet_link(self, link) -> bool:
        """Check if link tag is a stylesheet."""
        rel = link.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]
        return any("stylesheet" in r.lower() for r in rel)
    
    def _is_valid_asset_url(self, url: str) -> bool:
        """Check if URL is valid for asset download."""
        return url and not url.startswith("data:") and not url.startswith("mailto:")
    
    def _filter_internal_assets(self, assets: List[str], root_base_domain: str) -> List[str]:
        """Filter to keep only internal assets."""
        def is_internal(url: str) -> bool:
            host = urlparse(url).netloc.lower()
            # Remove 'www.' prefix if present
            if host.startswith("www."):
                host = host[4:]
            
            # Check if it's exact match or subdomain
            exact_match = host == root_base_domain
            subdomain_match = host.endswith(f".{root_base_domain}")
            
            # Special case for GitHub CDN assets
            github_cdn_match = (root_base_domain == "github.com" and 
                              host == "github.githubassets.com")
            
            return exact_match or subdomain_match or github_cdn_match
        
        return [url for url in assets if is_internal(url)]
    
    def _setup_download_directory(self, page_url: str) -> str:
        """Setup directory structure for asset downloads using {tld}/{tld}.{domain_name}/ format."""
        domain, _ = self.url_normalizer.get_domain_info(page_url)
        tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
        
        parsed = urlparse(page_url)
        page_path = parsed.path.strip("/")
        
        # For root path, use domain directory directly
        if not page_path:
            if parsed.query:
                # Use base64 encoding of full URL for directory name
                url_b64 = UrlUtils.generate_url_base64(page_url)
                page_base_dir = f"results/{tld}/{tld}.{domain_name}/index-{url_b64}"
            else:
                page_base_dir = f"results/{tld}/{tld}.{domain_name}"
        else:
            # For non-root paths, create directory structure
            safe_path = UrlUtils.sanitize_path(page_path)
            if parsed.query:
                # Use base64 encoding of full URL for directory name
                url_b64 = UrlUtils.generate_url_base64(page_url)
                page_base_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}-{url_b64}"
            else:
                page_base_dir = f"results/{tld}/{tld}.{domain_name}/{safe_path}"
        
        assets_base_dir = os.path.join(page_base_dir, "assets")
        FileUtils.ensure_directory(assets_base_dir)
        
        return assets_base_dir
    
    async def _download_assets_parallel(self, styles: List[str], scripts: List[str], page_url: str, assets_base_dir: str):
        """Download assets in parallel."""
        tasks = []
        
        for style_url in styles:
            tasks.append(self._download_single_asset(style_url, ".css", page_url, assets_base_dir))
        
        for script_url in scripts:
            tasks.append(self._download_single_asset(script_url, ".js", page_url, assets_base_dir))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _download_single_asset(self, url: str, ext_hint: str, page_url: str, assets_base_dir: str):
        """Download a single asset file."""
        try:
            parsed_asset = urlparse(url)
            parsed_page = urlparse(page_url)
            
            if not parsed_asset.netloc:
                return
            
            # Create destination path
            dest_path = self._create_asset_path(parsed_asset, parsed_page, assets_base_dir, ext_hint)
            
            # Skip if already exists and not empty
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                return
            
            # Download asset
            headers = self._get_asset_headers(ext_hint, parsed_asset.netloc, parsed_page.netloc)
            response = await self.http_client.get(url, headers)
            response.raise_for_status()
            
            # Validate and save content
            if len(response.content) > 0:
                with open(dest_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded asset: {os.path.basename(dest_path)}")
                
                # Upload to S3 if service is available
                if self.s3_service:
                    await self._upload_asset_to_s3(dest_path, url)
            else:
                print(f"Empty asset content for {url}")
                
        except Exception as e:
            print(f"Failed to download asset {url}: {e}")
    
    def _create_asset_path(self, parsed_asset, parsed_page, assets_base_dir: str, ext_hint: str) -> str:
        """Create local path for asset."""
        asset_host = parsed_asset.netloc.lower()
        page_host = parsed_page.netloc.lower()
        
        # Determine prefix
        rel_prefix = "" if asset_host == page_host else asset_host
        asset_dir, asset_name = os.path.split(parsed_asset.path or "/")
        
        # Create directory structure
        if rel_prefix:
            dest_dir = os.path.join(assets_base_dir, rel_prefix, asset_dir.lstrip("/"))
        else:
            dest_dir = os.path.join(assets_base_dir, asset_dir.lstrip("/"))
        
        FileUtils.ensure_directory(dest_dir)
        
        # Create filename
        qhash = UrlUtils.generate_path_hash(parsed_asset.query)
        name, ext = os.path.splitext(asset_name or ("file" + ext_hint))
        if not ext:
            ext = ext_hint
        
        safe_name = UrlUtils.sanitize_filename(name)
        filename = f"{safe_name}{('-' + qhash) if parsed_asset.query else ''}{ext}"
        
        return os.path.join(dest_dir, filename)
    
    def _get_asset_headers(self, ext_hint: str, asset_host: str, page_host: str) -> dict:
        """Get headers for asset download."""
        return {
            "Accept": "*/*",
            "Sec-Fetch-Dest": "script" if ext_hint == ".js" else "style",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin" if asset_host == page_host else "cross-site"
        }
    
    def _create_url_mapping(self, styles: List[str], scripts: List[str], page_url: str, base_dir: str) -> dict:
        """Create mapping from original URLs to local paths."""
        url_to_local = {}
        
        for css_url in styles:
            local_path = self._get_local_asset_path(css_url, page_url, ".css")
            if local_path:
                url_to_local[css_url] = local_path
        
        for js_url in scripts:
            local_path = self._get_local_asset_path(js_url, page_url, ".js")
            if local_path:
                url_to_local[js_url] = local_path
        
        return url_to_local
    
    def _get_local_asset_path(self, asset_url: str, page_url: str, ext_hint: str) -> Optional[str]:
        """Get relative path to local asset file."""
        try:
            parsed_page = urlparse(page_url)
            parsed_asset = urlparse(asset_url)
            
            if not parsed_asset.netloc:
                return None
            
            asset_host = parsed_asset.netloc.lower()
            page_host = parsed_page.netloc.lower()
            
            # Create relative path structure
            rel_prefix = "" if asset_host == page_host else asset_host
            asset_dir, asset_name = os.path.split(parsed_asset.path or "/")
            
            if rel_prefix:
                asset_local_dir = os.path.join(rel_prefix, asset_dir.lstrip("/"))
            else:
                asset_local_dir = asset_dir.lstrip("/")
            
            # Generate filename
            qhash = UrlUtils.generate_path_hash(parsed_asset.query)
            name, ext = os.path.splitext(asset_name or ("file" + ext_hint))
            if not ext:
                ext = ext_hint
            
            filename = f"{name}{('-' + qhash) if parsed_asset.query else ''}{ext}"
            
            # Create relative path
            if asset_local_dir:
                local_asset_path = f"assets/{asset_local_dir}/{filename}"
            else:
                local_asset_path = f"assets/{filename}"
            
            return local_asset_path.replace("\\", "/")
        except Exception as e:
            print(f"Error generating local asset path for {asset_url}: {e}")
            return None
    
    def _replace_css_links(self, soup: BeautifulSoup, page_url: str, url_to_local: dict):
        """Replace CSS link URLs with local paths."""
        for link in soup.find_all("link", href=True):
            if self._is_stylesheet_link(link):
                href = link.get("href")
                if href:
                    original_url = urljoin(page_url, href)
                    if original_url in url_to_local:
                        link["href"] = url_to_local[original_url]
    
    def _replace_script_sources(self, soup: BeautifulSoup, page_url: str, url_to_local: dict):
        """Replace script source URLs with local paths."""
        for script in soup.find_all("script", contentengine=True):
            contentengine = script.get("contentengine")
            if contentengine:
                original_url = urljoin(page_url, contentengine)
                if original_url in url_to_local:
                    script["contentengine"] = url_to_local[original_url]
    
    def _fix_inline_css(self, soup: BeautifulSoup, url_to_local: dict):
        """Fix CSS @import statements in inline styles."""
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                css_content = style_tag.string
                for original_url, local_path in url_to_local.items():
                    css_content = css_content.replace(f"url('{original_url}')", f"url('{local_path}')")
                    css_content = css_content.replace(f'url("{original_url}")', f'url("{local_path}")')
                    css_content = css_content.replace(f"url({original_url})", f"url({local_path})")
                style_tag.string = css_content
    
    async def _upload_asset_to_s3(self, local_path: str, original_url: str):
        """Upload asset file to S3 with proper folder structure and metadata."""
        try:
            # Extract domain info for metadata
            parsed_url = urlparse(original_url)
            domain = parsed_url.netloc.lower()
            
            # Upload using S3Service with new structure: tld/tld.domain/assets/...
            result = self.s3_service.upload_asset(local_path, original_url, domain)
            if result:
                print(f"Uploaded asset to S3: {os.path.basename(local_path)}")
            
        except Exception as e:
            print(f"Failed to upload asset {local_path} to S3: {e}")