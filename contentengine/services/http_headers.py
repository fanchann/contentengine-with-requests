from typing import Dict, Optional

class HttpHeaderParser:
    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers

    def get_header(self, name: str) -> Optional[str]:
        """Get a specific header by name (case-insensitive)"""
        return self.headers.get(name.lower())

    def get_all_headers(self) -> Dict[str, str]:
        """Get all headers"""
        return self.headers

    def has_header(self, name: str) -> bool:
        """Check if a header exists"""
        return name.lower() in self.headers

    def get_content_type(self) -> Optional[str]:
        """Get Content-Type header"""
        return self.get_header('content-type')

    def get_content_length(self) -> Optional[str]:
        """Get Content-Length header"""
        return self.get_header('content-length')

    def get_server(self) -> Optional[str]:
        """Get Server header"""
        return self.get_header('server')

    def get_user_agent(self) -> Optional[str]:
        """Get User-Agent header (if in request)"""
        return self.get_header('user-agent')
