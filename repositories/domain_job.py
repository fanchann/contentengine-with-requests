from typing import Sequence, Optional
from uuid import UUID as PyUUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from entities.content_engine import ContentEngineDomainTaskJob
from enums import PriorityLevel, JobStatus

class ContentEngineDomainTaskJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj: ContentEngineDomainTaskJob) -> ContentEngineDomainTaskJob:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get(self, id: PyUUID) -> Optional[ContentEngineDomainTaskJob]:
        result = await self.session.execute(
            select(ContentEngineDomainTaskJob).where(ContentEngineDomainTaskJob.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[ContentEngineDomainTaskJob]:
        result = await self.session.execute(
            select(ContentEngineDomainTaskJob).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, id: PyUUID) -> None:
        await self.session.execute(
            delete(ContentEngineDomainTaskJob).where(ContentEngineDomainTaskJob.id == id)
        )
        await self.session.commit()

    async def claim_jobs(
        self,
        *,
        priority: PriorityLevel,
        limit: int,
        worker_id: str | None = None,   # optional; saat ini belum disimpan ke kolom manapun
        task_id: Optional[PyUUID] = None,
    ) -> Sequence[ContentEngineDomainTaskJob]:
        """
        Ambil 'limit' job yang masih pending & sesuai priority (+opsional task_id),
        lock row dengan SKIP LOCKED, set status=IN_PROGRESS dan started_at=NOW(), lalu kembalikan barisnya.
        """

        filters = [
            ContentEngineDomainTaskJob.status == JobStatus.PENDING.value,
            ContentEngineDomainTaskJob.priority == int(priority),
        ]
        if task_id is not None:
            filters.append(ContentEngineDomainTaskJob.task_id == task_id)

        # kandidat id dengan for update skip locked
        subq = (
            select(ContentEngineDomainTaskJob.id)
            .where(*filters)
            .order_by(ContentEngineDomainTaskJob.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
            .cte("candidates")
        )

        upd = (
            update(ContentEngineDomainTaskJob)
            .where(ContentEngineDomainTaskJob.id.in_(select(subq.c.id)))
            .values(
                status=JobStatus.IN_PROGRESS.value,
                started_at=func.now(),
            )
            .returning(ContentEngineDomainTaskJob)
        )

        res = await self.session.execute(upd)
        jobs = res.scalars().all()
        await self.session.commit()
        return jobs

    async def mark_done(self, job_id: PyUUID) -> None:
        await self.session.execute(
            update(ContentEngineDomainTaskJob)
            .where(ContentEngineDomainTaskJob.id == job_id)
            .values(
                status=JobStatus.COMPLETED.value,
                completed_at=func.now(),
            )
        )
        await self.session.commit()

    async def mark_failed(self, job_id: PyUUID, reason: Optional[str] = None) -> None:
        # NOTE: kalau ingin menyimpan reason, tambahkan kolom mis. "failReason" di model & set di values(...)
        await self.session.execute(
            update(ContentEngineDomainTaskJob)
            .where(ContentEngineDomainTaskJob.id == job_id)
            .values(status=JobStatus.FAILED.value)
        )
        await self.session.commit()

    async def release_stuck(self, older_than_seconds: int = 300) -> int:
        """
        Kembalikan job 'IN_PROGRESS' ke 'PENDING' jika sudah 'stuck' lebih lama dari older_than_seconds.
        Ditentukan dari umur (now - started_at) dalam detik.
        """
        age_seconds = func.extract('epoch', func.now() - ContentEngineDomainTaskJob.started_at)
        res = await self.session.execute(
            update(ContentEngineDomainTaskJob)
            .where(
                ContentEngineDomainTaskJob.status == JobStatus.IN_PROGRESS.value,
                ContentEngineDomainTaskJob.started_at.is_not(None),
                age_seconds > older_than_seconds,
            )
            .values(
                status=JobStatus.PENDING.value,
                started_at=None,  # reset
            )
            .returning(ContentEngineDomainTaskJob.id)
        )
        await self.session.commit()
        return len(res.scalars().all())
