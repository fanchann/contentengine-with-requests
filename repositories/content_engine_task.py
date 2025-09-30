from typing import Sequence, Optional
from uuid import UUID as PyUUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from entities.content_engine import ContentEngineDomainTask

class DomainTaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj: ContentEngineDomainTask) -> ContentEngineDomainTask:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get(self, id: PyUUID) -> Optional[ContentEngineDomainTask]:
        result = await self.session.execute(
            select(ContentEngineDomainTask).where(ContentEngineDomainTask.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[ContentEngineDomainTask]:
        result = await self.session.execute(
            select(ContentEngineDomainTask).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, id: PyUUID) -> None:
        await self.session.execute(
            delete(ContentEngineDomainTask).where(ContentEngineDomainTask.id == id)
        )
        await self.session.commit()
