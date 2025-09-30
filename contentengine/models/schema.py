from pydantic import AnyHttpUrl, Field
from typing import Optional
from master.schema import RequestSchema

class ContentSchema(RequestSchema):
    url: AnyHttpUrl = Field(
        ..., examples=["https://example.com"], description="Target URL"
    )
    enable_shadow_dom_extraction: bool = Field(
        True, description="Enable shadow dom extraction"
    )
