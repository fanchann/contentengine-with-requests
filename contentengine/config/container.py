from contentengine.models.config import CrawlerConfig
from contentengine.services.http_client import HttpClientService
from contentengine.services.url_normalizer import UrlNormalizerService
from contentengine.services.content_extractor import ContentExtractorService
from contentengine.services.asset_downloader import AssetDownloaderService
from contentengine.services.output_writer import OutputWriterService
from contentengine.services.task_queue import TaskQueueService
from contentengine.handlers.crawler import PriorityCrawler


class CrawlerContainer:
    """Dependency injection container implementing the Dependency Inversion Principle."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self._services = {}
    
    def get_crawler(self) -> PriorityCrawler:
        """Get fully configured crawler instance."""
        return PriorityCrawler(
            config=self.config,
            http_client=self.get_http_client(),
            url_normalizer=self.get_url_normalizer(),
            content_extractor=self.get_content_extractor(),
            asset_downloader=self.get_asset_downloader(),
            output_writer=self.get_output_writer(),
            task_queue=self.get_task_queue()
        )
    
    def get_http_client(self) -> HttpClientService:
        """Get HTTP client service."""
        if 'http_client' not in self._services:
            self._services['http_client'] = HttpClientService(self.config)
        return self._services['http_client']
    
    def get_url_normalizer(self) -> UrlNormalizerService:
        """Get URL normalizer service."""
        if 'url_normalizer' not in self._services:
            self._services['url_normalizer'] = UrlNormalizerService()
        return self._services['url_normalizer']
    
    def get_content_extractor(self) -> ContentExtractorService:
        """Get content extractor service."""
        if 'content_extractor' not in self._services:
            self._services['content_extractor'] = ContentExtractorService()
        return self._services['content_extractor']
    
    def get_asset_downloader(self) -> AssetDownloaderService:
        """Get asset downloader service."""
        if 'asset_downloader' not in self._services:
            self._services['asset_downloader'] = AssetDownloaderService(
                http_client=self.get_http_client(),
                url_normalizer=self.get_url_normalizer()
            )
        return self._services['asset_downloader']
    
    def get_output_writer(self) -> OutputWriterService:
        """Get output writer service."""
        if 'output_writer' not in self._services:
            self._services['output_writer'] = OutputWriterService(
                asset_downloader=self.get_asset_downloader()
            )
        return self._services['output_writer']
    
    def get_task_queue(self) -> TaskQueueService:
        """Get task queue service."""
        if 'task_queue' not in self._services:
            self._services['task_queue'] = TaskQueueService()
        return self._services['task_queue']