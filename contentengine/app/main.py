import os
from typing import Optional
from loguru import logger
from faststream import Context

from master.app import broker,app
from master.subject import SubjectBuilder
from master.schema import ResponseSchema
from master.integration import playwright

from contentengine.services.playwright_http_client import PlaywrightHttpClientService

from contentengine.models.schema import ContentSchema
from contentengine.models.content import ContentOutput
from contentengine.models.config import CrawlerConfig
from contentengine.handlers.crawler import PriorityCrawler
from master.integration import playwright


playwright.setup(app)


### Define metadata
QUEUE = "contentengine"
detail_subject = SubjectBuilder("detail", prefix=QUEUE, queue=QUEUE)
DETAIL_RESPONSE_MODEL = ResponseSchema[ContentOutput]


@broker.subscriber(
    str(detail_subject), queue=QUEUE, max_workers=5, retry=True, idle_heartbeat=1.5
)
async def detail(
    msg: ContentSchema, browser_manager: PlaywrightHttpClientService
) -> DETAIL_RESPONSE_MODEL:
    """Get content details with optional priority-based processing"""

    return await contentengine(msg, browser_manager)


async def contentengine(
    msg: ContentSchema,
    browser_manager: PlaywrightHttpClientService
) -> DETAIL_RESPONSE_MODEL:
    config = CrawlerConfig(
            timeout_ms=int(os.getenv("CRAWLER_TIMEOUT_MS", 300000)),
            enable_screenshots=True
    )

    logger.info(f"Screenshots enabled: {config.enable_screenshots}")
    logger.info(f"Timeout: {config.timeout_ms}ms")

    crawler = PriorityCrawler(config)
    return await crawler.crawl(msg, browser_manager)


@broker.subscriber(detail_subject.ping())
async def ping() -> str:
    return "pong"