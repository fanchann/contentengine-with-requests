from datetime import datetime
from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class WorkspaceCrawler(Base):
    __tablename__ = "WorkspaceCrawler"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    pausedAt = Column(DateTime(timezone=True))
    exitedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="crawlers")
    contents = relationship("Content", back_populates="crawler", cascade="all, delete-orphan")