from typing import List, Optional
from pydantic import AnyHttpUrl, BaseModel, Field
from typing import Any


class MetaTag(BaseModel):
    """Meta tag information."""
    name: str = Field(..., description="Name of meta tag")
    content: str = Field(..., description="Content of meta tag")

class Checksum(BaseModel):
    raw_html: str = Field(..., description="Checksum of raw html (sha256)")
    parsed_html: Optional[str] = Field(None, description="Checksum of parsed html (sha256)")

class ContentOutput(BaseModel):
    """Complete content output for a crawled page."""
    url: AnyHttpUrl = Field(..., description="Original url of page")
    title: str = Field(..., description="Title of page")
    http_headers: Optional[dict] = Field(
        None, description="HTTP headers from response"
    )
    metatags: Optional[List[MetaTag]] = Field(
        None, description="List of meta tags in page"
    )
    images: Optional[List[str]] = Field(
        None, description="List of image urls found in page"
    )
    links: Optional[List[str]] = Field(
        None, description="List of link urls found in page"
    )
    scripts: Optional[List[str]] = Field(
        None, description="List of script urls found in page"
    )
    stylesheets: Optional[list[dict[str, Any]]] = Field(
        None, description="List of <link> tags found in page"
    )
    checksums: Optional[Checksum] = Field(
        None, description="Checksums of raw and parsed html"
    )
    screenshot_path: Optional[str] = Field(
        None, description="Path to screenshot image file"
    )
    html_path: Optional[str] = Field(
        None, description="Path to html file"
    )
    icon_path: Optional[str] = Field(
        None, description="Path to favicon file"
    )
    canonical_url: Optional[AnyHttpUrl] = Field(
        None, description="Canonical URL if specified in page"
    )