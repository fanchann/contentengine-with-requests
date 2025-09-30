# worker.py
import asyncio
import time
import sys
import os
import logging
import random
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from contextlib import asynccontextmanager
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.domain_job import DomainJobRepository
from models.models import UrlPriority
from sqlalchemy.orm import sessionmaker
from config.postgresql import PostgresqlDBConnection
from dotenv import load_dotenv

PRIORITY_ORDER = [UrlPriority.high, UrlPriority.medium, UrlPriority.low]
WORKER_ID = "worker-1"
MAX_PER_SECOND = 20
CONCURRENCY = 20  # berapa task paralel di process()

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler('worker.log')
    ]
)
logger = logging.getLogger('CrawlerWorker')

class AsyncConnection:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set. Please set it in your .env file or environment.")
        self.db_config = PostgresqlDBConnection(database_url)
        self.async_session = sessionmaker(
            self.db_config.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def __aenter__(self):
        self.session = self.async_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

class TokenBucket:
    def __init__(self, rate_per_sec: int, capacity: int):
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.perf_counter()
        self.lock = asyncio.Lock()

    async def take(self, n: int = 1):
        async with self.lock:
            while self.tokens < n:
                now = time.perf_counter()
                elapsed = now - self.last
                if elapsed > 0:
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                    self.last = now
                # hitung kekurangan dan tidur seperlunya
                need = n - self.tokens
                sleep_for = max(need / self.rate, 0.001)
                await asyncio.sleep(sleep_for)
            self.tokens -= n

async def handle_job(job) -> None:
    """Simulasi proses crawling dan screenshot dengan Playwright"""
    try:
        logger.info(f"[Job {job.id}] Starting crawling process for: {job.url}")
        
        # Simulasi inisialisasi Playwright
        logger.info(f"[Job {job.id}] Initializing Playwright browser...")
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Browser startup time
        
        # Simulasi navigasi ke URL
        logger.info(f"[Job {job.id}] Navigating to {job.url}")
        await asyncio.sleep(random.uniform(1.0, 3.0))  # Page load time
        
        
        # upload assets, html to s3
        logger.info(f"[Job {job.id}] Uploading assets to S3...")
        await asyncio.sleep(random.uniform(0.5, 1.0)) 
        
        # Simulasi screenshot kemudian upload ke S3
        logger.info(f"[Job {job.id}] Taking screenshot...")
        await asyncio.sleep(random.uniform(0.8, 1.5))  # Screenshot time
        
        # Simulasi extract metadata dan link dari halaman kemudian insert ke db
        logger.info(f"[Job {job.id}] Extracting metadata and links...")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Simulasi cleanup
        logger.info(f"[Job {job.id}] Cleaning up browser resources...")
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Success log
        total_time = random.uniform(3.0, 7.0)
        logger.info(f"[Job {job.id}] Successfully completed crawling {job.url} in {total_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[Job {job.id}] Error processing {job.url}: {str(e)}")
        raise

@asynccontextmanager
async def get_repo():
    async with AsyncConnection() as session:
        yield DomainJobRepository(session)

async def claim_up_to_20() -> list:
    claimed = []
    remaining = MAX_PER_SECOND
    async with AsyncConnection() as session:
        repo = DomainJobRepository(session)
        for prio in PRIORITY_ORDER:
            if remaining <= 0:
                break
            got = await repo.claim_jobs(priority=prio, limit=remaining, worker_id=WORKER_ID)
            if got:
                logger.info(f"Claimed {len(got)} jobs with {prio.value} priority")
            claimed.extend(got)
            remaining = MAX_PER_SECOND - len(claimed)
            # kalau habis di level ini, otomatis turun ke berikutnya
            if remaining <= 0:
                break
    
    if claimed:
        logger.info(f"Total claimed: {len(claimed)} jobs for processing")
    else:
        logger.info("No jobs available, waiting...")
    
    return claimed

async def run_worker():
    logger.info(f"Worker '{WORKER_ID}' starting up...")
    logger.info(f"Configuration: Rate={MAX_PER_SECOND}/s, Concurrency={CONCURRENCY}")
    logger.info(f"Priority order: {[p.value for p in PRIORITY_ORDER]}")
    
    bucket = TokenBucket(rate_per_sec=MAX_PER_SECOND, capacity=MAX_PER_SECOND)
    sem = asyncio.Semaphore(CONCURRENCY)
    cycle_count = 0

    while True:
        cycle_count += 1
        cycle_start = time.perf_counter()
        logger.info(f"\n=== CYCLE {cycle_count} STARTED ===")
        
        jobs = await claim_up_to_20()

        if not jobs:
            # nothing to do; kecilkan polling
            await asyncio.sleep(0.25)
            continue

        async def run_one(job):
            # rate-limit 20/detik
            await bucket.take(1)
            async with sem:
                job_start = time.perf_counter()
                try:
                    await handle_job(job)
                    async with AsyncConnection() as session:
                        await DomainJobRepository(session).mark_done(job.id)
                    
                    job_duration = time.perf_counter() - job_start
                    logger.info(f"[Job {job.id}] Marked as COMPLETED ({job_duration:.2f}s) - Priority: {job.domain_priority.value}")
                    
                except Exception as e:
                    async with AsyncConnection() as session:
                        await DomainJobRepository(session).mark_failed(job.id)
                    
                    job_duration = time.perf_counter() - job_start
                    logger.error(f"[Job {job.id}] Marked as FAILED ({job_duration:.2f}s) - Priority: {job.domain_priority.value} - Error: {str(e)}")

        if jobs:
            logger.info(f"Processing {len(jobs)} jobs in parallel...")
            await asyncio.gather(*(run_one(j) for j in jobs))
        
        # jaga ritme supaya satu "gelombang" kira-kira per detik (opsional)
        cycle_duration = time.perf_counter() - cycle_start
        logger.info(f"CYCLE {cycle_count} COMPLETED in {cycle_duration:.2f}s - Processed: {len(jobs)} jobs")
        
        if cycle_duration < 1.0:
            sleep_time = 1.0 - cycle_duration
            logger.info(f"Sleeping for {sleep_time:.2f}s to maintain cycle rhythm")
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(run_worker())
