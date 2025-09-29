"""S3 service for uploading crawler assets."""

import os
import mimetypes
from typing import Dict, Optional
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from contentengine.models.config import CrawlerConfig
from contentengine.utils.url_utils import UrlUtils


class S3Service:
    """Service for uploading assets to S3/MinIO."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with configuration."""
        if not self.config.s3_endpoint or not self.config.s3_access_key:
            print("S3 configuration missing, uploads disabled")
            return
            
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                region_name=self.config.s3_region
            )
            
            # Test connection and create bucket if it doesn't exist
            self._ensure_bucket_exists()
            print(f"S3 client initialized successfully for bucket: {self.config.s3_bucket_name}")
            
        except Exception as e:
            print(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        if not self.s3_client:
            return
            
        try:
            self.s3_client.head_bucket(Bucket=self.config.s3_bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.config.s3_bucket_name)
                    print(f"Created bucket: {self.config.s3_bucket_name}")
                except Exception as create_error:
                    print(f"Failed to create bucket: {create_error}")
            else:
                print(f"Error checking bucket: {e}")
    
    def upload_file(self, local_path: str, s3_key: str, url: str, file_type: str = None) -> Optional[str]:
        """Upload file to S3 with metadata."""
        if not self.s3_client or not os.path.exists(local_path):
            return None
            
        try:
            # Determine content type
            if file_type:
                content_type = file_type
            else:
                content_type, _ = mimetypes.guess_type(local_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Extract domain from URL
            parsed_url = urlparse(url)
            full_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Prepare metadata
            metadata = {
                'Url': full_domain,
                'OriginalFilename': os.path.basename(local_path),
                'UploadedAt': str(int(__import__('time').time()))
            }
            
            # Upload file
            self.s3_client.upload_file(
                local_path,
                self.config.s3_bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': metadata
                }
            )
            
            # Generate public URL
            public_url = f"{self.config.s3_endpoint}/{self.config.s3_bucket_name}/{s3_key}"
            print(f"Uploaded to S3: {s3_key}")
            return public_url
            
        except Exception as e:
            print(f"Failed to upload {local_path} to S3: {e}")
            return None
    
    def upload_screenshot(self, screenshot_path: str, url: str) -> Optional[str]:
        """Upload screenshot to S3 with proper folder structure."""
        if not os.path.exists(screenshot_path):
            return None
            
        # Generate S3 key following new folder structure: tld/tld.domain/screenshot_{path}.png
        domain, _ = UrlUtils.get_domain_info(url)
        tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
        
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        # Create S3 key path
        if not path:
            if parsed.query:
                url_b64 = UrlUtils.generate_url_base64(url)
                s3_key = f"{tld}/{tld}.{domain_name}/screenshot_index-{url_b64}.{self.config.screenshot_format}"
            else:
                s3_key = f"{tld}/{tld}.{domain_name}/screenshot_index.{self.config.screenshot_format}"
        else:
            safe_path = __import__('re').sub(r"[^\w\-./]", "_", path)
            if parsed.query:
                url_b64 = UrlUtils.generate_url_base64(url)
                s3_key = f"{tld}/{tld}.{domain_name}/screenshot_{safe_path}-{url_b64}.{self.config.screenshot_format}"
            else:
                s3_key = f"{tld}/{tld}.{domain_name}/screenshot_{safe_path}.{self.config.screenshot_format}"
        
        return self.upload_file(
            screenshot_path, 
            s3_key, 
            url, 
            f"image/{self.config.screenshot_format}"
        )
    
    def upload_asset(self, asset_path: str, url: str, asset_url: str) -> Optional[str]:
        """Upload asset to S3 with proper folder structure."""
        if not os.path.exists(asset_path):
            return None
            
        # Generate S3 key following new folder structure: tld/tld.domain/assets/...
        domain, _ = UrlUtils.get_domain_info(url)
        tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
        
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        # Get relative path from local asset path
        # Extract relative path after the domain folder
        try:
            # Parse asset path to get relative structure
            path_parts = asset_path.split(os.sep)
            assets_index = path_parts.index('assets')
            relative_asset_path = '/'.join(path_parts[assets_index:])
        except (ValueError, IndexError):
            relative_asset_path = f"assets/{os.path.basename(asset_path)}"
        
        # Create S3 key path: tld/tld.domain/assets/...
        s3_key = f"{tld}/{tld}.{domain_name}/{relative_asset_path}"
        
        return self.upload_file(asset_path, s3_key, url)
    
    def upload_html(self, html_path: str, url: str) -> Optional[str]:
        """Upload HTML file to S3 with proper folder structure."""
        if not os.path.exists(html_path):
            return None
            
        # Generate S3 key following new folder structure: tld/tld.domain/{path}.html
        domain, _ = UrlUtils.get_domain_info(url)
        tld, domain_name = UrlUtils.get_tld_and_domain_name(domain)
        
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        # Create S3 key path
        if not path:
            if parsed.query:
                url_b64 = UrlUtils.generate_url_base64(url)
                s3_key = f"{tld}/{tld}.{domain_name}/index-{url_b64}.html"
            else:
                s3_key = f"{tld}/{tld}.{domain_name}/index.html"
        else:
            safe_path = __import__('re').sub(r"[^\w\-./]", "_", path)
            if parsed.query:
                url_b64 = UrlUtils.generate_url_base64(url)
                s3_key = f"{tld}/{tld}.{domain_name}/{safe_path}-{url_b64}.html"
            else:
                s3_key = f"{tld}/{tld}.{domain_name}/{safe_path}.html"
        
        return self.upload_file(html_path, s3_key, url, "text/html")