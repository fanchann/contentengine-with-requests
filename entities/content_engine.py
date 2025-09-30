from uuid import uuid4, UUID as PyUUID
from sqlalchemy import declarative_base
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer, SmallInteger, func
from sqlalchemy.dialects.postgresql import UUID
from entities.enums import PriorityLevel, JobStatus

Base = declarative_base()

# Tabel: "ContentEngineDomainTask"
class ContentEngineDomainTask(Base):
    __tablename__ = "ContentEngineDomainTask"

    id = Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain = Column("domain", String(255), ForeignKey('Domain.name'), nullable=False)
    created_at = Column("createdAt", TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    started_at = Column("startedAt", TIMESTAMP(timezone=True))
    completed_at = Column("completedAt", TIMESTAMP(timezone=True))


# Tabel: "ContentEngineDomainTaskJob"
class ContentEngineDomainTaskJob(Base):
    __tablename__ = "ContentEngineDomainTaskJob"

    id = Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column("taskId", UUID(as_uuid=True), ForeignKey('ContentEngineDomainTask.id'), nullable=False)
    domain = Column("domain", String(255), nullable=False)
    root_domain = Column("rootDomain", String(255))
    priority = Column("priority", Integer, nullable=False, default=PriorityLevel.LOW.value)
    status = Column("status", SmallInteger, nullable=False, default=JobStatus.PENDING.value)

    created_at = Column("createdAt", TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    started_at = Column("startedAt", TIMESTAMP(timezone=True))
    completed_at = Column("completedAt", TIMESTAMP(timezone=True))
