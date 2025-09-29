"""Core interfaces package."""

from .interfaces import (
    IHttpClient,
    IContentExtractor,
    IAssetDownloader,
    IUrlNormalizer,
    IOutputWriter,
    ITaskQueue
)

__all__ = [
    "IHttpClient",
    "IContentExtractor", 
    "IAssetDownloader",
    "IUrlNormalizer",
    "IOutputWriter",
    "ITaskQueue"
]