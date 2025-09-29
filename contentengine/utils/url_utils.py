import re
import hashlib
import base64
import tldextract
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional, Tuple


class UrlUtils:
    """Utility class for URL operations."""
    
    @staticmethod
    def base_domain(netloc: str) -> str:
        """Extract base domain by removing www prefix."""
        netloc = (netloc or "").lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    
    @staticmethod
    def is_clean_url(parsed) -> bool:
        """Check if URL is clean (no path/query)."""
        path_empty = parsed.path in ("", "/")
        no_query = parsed.query == ""
        return path_empty and no_query
    
    @staticmethod
    def get_domain_info(url: str) -> Tuple[str, str]:
        """Extract domain and base-domain (strip www.)."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        base_domain = UrlUtils.base_domain(domain)
        return domain, base_domain
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize path for filesystem."""
        return re.sub(r"[^\w\-./]", "_", path)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem."""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    @staticmethod
    def generate_path_hash(query: str) -> str:
        """Generate hash for query parameters."""
        return hashlib.sha256((query or "").encode()).hexdigest()[:8]
    
    @staticmethod
    def generate_url_base64(url: str) -> str:
        """Generate base64 encoded string from full URL that can be decoded back to original URL."""
        url_bytes = url.encode('utf-8')
        base64_bytes = base64.urlsafe_b64encode(url_bytes)
        base64_string = base64_bytes.decode('utf-8')
        # Remove padding to make it cleaner for directory names
        return base64_string.rstrip('=')
    
    @staticmethod
    def decode_url_base64(base64_string: str) -> str:
        """Decode base64 string back to original URL."""
        # Add padding back if needed
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        
        base64_bytes = base64_string.encode('utf-8')
        url_bytes = base64.urlsafe_b64decode(base64_bytes)
        return url_bytes.decode('utf-8')
    
    @staticmethod
    def normalize_netloc(netloc: str, scheme: str) -> str:
        """Normalize netloc by removing default ports."""
        if netloc.endswith(":80") and scheme == "http":
            return netloc[:-3]
        if netloc.endswith(":443") and scheme == "https":
            return netloc[:-4]
        return netloc
    
    @staticmethod
    def collapse_path(path: str) -> str:
        """Collapse multiple slashes and remove trailing slash."""
        path = re.sub(r"/+", "/", path or "/")
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return path
    
    @staticmethod
    def get_tld_and_domain_name(domain: str) -> Tuple[str, str]:
        """Extract TLD and domain name using tldextract library.
        
        Examples:
        - 'github.com' -> ('com', 'github')
        - 'httpbin.org' -> ('org', 'httpbin')
        - 'example.co.uk' -> ('co.uk', 'example')
        - 'subdomain.example.com' -> ('com', 'example')
        """
        if not domain:
            return '', ''
        
        # Use tldextract for accurate TLD parsing
        extracted = tldextract.extract(domain)
        
        # Get the suffix (TLD) and domain
        tld = extracted.suffix or ''
        domain_name = extracted.domain or ''
        
        return tld, domain_name