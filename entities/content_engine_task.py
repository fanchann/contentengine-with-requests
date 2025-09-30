from sqlalchemy import Column, String, DateTime, Integer, SmallInteger, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from entities.base import Base
import uuid

class ContentEngineDomainTask(Base):
    """Domain task for content engine crawling"""
    __tablename__ = "ContentEngineDomainTask"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), ForeignKey("Domain.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    startedAt = Column(DateTime(timezone=True), nullable=True)
    completedAt = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    jobs = relationship("ContentEngineDomainTaskJob", back_populates="task", cascade="all, delete-orphan")

class ContentEngineDomainTaskJob(Base):
    """Individual crawl job for content engine"""
    __tablename__ = "ContentEngineDomainTaskJob"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    taskId = Column(UUID(as_uuid=True), ForeignKey("ContentEngineDomainTask.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    domain = Column(String(255), nullable=False)
    rootDomain = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False, default=0)  # 0:Low, 1:Medium, 2:High
    status = Column(SmallInteger, nullable=False, default=0)  # 0:Pending, 1:In-Progress, 2:Completed, 3:Failed
    createdAt = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    startedAt = Column(DateTime(timezone=True), nullable=True)
    completedAt = Column(DateTime(timezone=True), nullable=True)
    
    # Content engine specific fields (tidak perlu ubah schema, kita extend usage)
    url = Column(Text, nullable=True)  # Will be populated by content engine
    title = Column(Text, nullable=True)
    rawHtml = Column(Text, nullable=True)
    parsedHtml = Column(Text, nullable=True)
    contentChecksum = Column(String(255), nullable=True)
    assetData = Column(JSON, nullable=True)  # Store extracted assets as JSON
    
    # Relationship
    task = relationship("ContentEngineDomainTask", back_populates="jobs")