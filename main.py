import asyncio
from contentengine.models.config import CrawlerConfig
from contentengine.config.container import CrawlerContainer
import os

# Load environment variables
from dotenv import load_dotenv, find_dotenv

# Load .env file with explicit path checking
env_file = find_dotenv()
if env_file:
    print(f"Loading environment variables from: {env_file}")
    load_dotenv(env_file)
else:
    print("No .env file found, using default values")


async def main():
    # Configure crawler with environment variables
    config = CrawlerConfig(
        timeout_ms=int(os.getenv("CRAWLER_TIMEOUT_MS", 30000)),
        delay=float(os.getenv("CRAWLER_DELAY", 1.0)),
        concurrency=int(os.getenv("CRAWLER_CONCURRENCY", 5)),
        timeout_total=float(os.getenv("CRAWLER_TIMEOUT_TOTAL", 30.0)),
        timeout_connect=float(os.getenv("CRAWLER_TIMEOUT_CONNECT", 10.0)),
        timeout_read=float(os.getenv("CRAWLER_TIMEOUT_READ", 25.0)),
        
        # Screenshot configuration
        enable_screenshots=os.getenv("CRAWLER_ENABLE_SCREENSHOTS", "false").lower() == "true",
        screenshot_quality=int(os.getenv("CRAWLER_SCREENSHOT_QUALITY", 90)),
        screenshot_format=os.getenv("CRAWLER_SCREENSHOT_FORMAT", "png"),
        
        # S3 configuration
        s3_endpoint=os.getenv("MINIO_PRIVATE_ENDPOINT"),
        s3_access_key=os.getenv("MINIO_ROOT_USER"),
        s3_secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
        s3_bucket_name=os.getenv("MINIO_BUCKET_NAME", "crawler-assets"),
    )
    
    print(f"Crawler config: timeout={config.timeout_ms}ms, delay={config.delay}s, concurrency={config.concurrency}")
    print(f"Screenshots: {'enabled' if config.enable_screenshots else 'disabled'}")
    print(f"S3 uploads: {'enabled' if config.s3_endpoint else 'disabled'}")
    print()
    
    # Create container and get crawler
    container = CrawlerContainer(config)
    crawler = container.get_crawler()
    
    # Get start URL from environment or use default
    start_url = os.getenv("CRAWLER_START_URL", "")
    if not start_url:
        print("No start URL provided. Please set the CRAWLER_START_URL environment variable.")
        return
    print(f"Starting crawl from: {start_url}")
    
    try:
        results = await crawler.crawl_async(start_url)
        
        # Print summary
        total_pages = len(results)
        total_links = sum(len(co.links or []) for co in results)
        total_images = sum(len(co.images or []) for co in results)
        
        print(f"\n Summary:")
        print(f"Total pages crawled: {total_pages}")
        print(f"Total links found: {total_links}")
        print(f"Total images found: {total_images}")
        
    except Exception as e:
        print(f"Crawling failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())