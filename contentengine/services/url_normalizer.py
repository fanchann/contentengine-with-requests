from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin

from contentengine.core.interfaces import IUrlNormalizer
from contentengine.utils.url_utils import UrlUtils


class UrlNormalizerService(IUrlNormalizer):
    """Service for URL normalization and categorization."""
    
    def normalize_url(self, base: str, href: str) -> Optional[str]:
        """Normalize URL by cleaning up and standardizing format."""
        abs_url = urljoin(base, href)
        p = urlparse(abs_url)

        if p.scheme not in ("http", "https") or not p.netloc:
            return None

        # Drop fragment
        p = p._replace(fragment="")

        # Drop common tracking queries
        if p.query:
            q = [
                (k, v)
                for k, v in parse_qsl(p.query, keep_blank_values=True)
                if not k.lower().startswith(("utm_", "fbclid", "gclid"))
            ]
            p = p._replace(query=urlencode(q))

        # Normalize netloc default ports
        netloc = UrlUtils.normalize_netloc(p.netloc.lower(), p.scheme)
        p = p._replace(netloc=netloc)

        # Collapse multiple slashes; remove trailing slash except root
        path = UrlUtils.collapse_path(p.path)
        p = p._replace(path=path)

        return urlunparse(p)
    
    def categorize_url(self, url: str, root_base_domain: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Categorize URL relative to the TARGET ROOT base domain.
        Rules:
        - external clean host (no path/query) -> high
        - external with path/query -> low
        - subdomain clean -> medium
        - subdomain with path/query -> low
        - same base-domain (same_url) -> low
        """
        parsed = urlparse(url)
        target_domain = parsed.netloc.lower()
        if not target_domain:
            return None, None

        target_base = UrlUtils.base_domain(target_domain)
        clean = UrlUtils.is_clean_url(parsed)

        if target_base == root_base_domain:
            return "low", "same_url"
        elif target_base.endswith(f".{root_base_domain}"):
            return ("medium" if clean else "low"), (
                "subdomain_clean" if clean else "subdomain_path"
            )
        else:
            return ("high" if clean else "low"), (
                "external_clean" if clean else "external_path"
            )
    
    def get_domain_info(self, url: str) -> Tuple[str, str]:
        """Extract domain and base-domain (strip www.)."""
        return UrlUtils.get_domain_info(url)