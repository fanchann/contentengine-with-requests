from datetime import datetime
from sqlalchemy import Column, Text, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class ObjectStorage(Base):
    __tablename__ = "ObjectStorage"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path = Column(Text, nullable=False)
    filename = Column(Text, nullable=False)
    hash = Column(String(255), nullable=False)
    storedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    content_headers = relationship("Content", foreign_keys="Content.headerPath", back_populates="header_storage")
    content_bodies = relationship("Content", foreign_keys="Content.bodyPath", back_populates="body_storage")
    content_icons = relationship("Content", foreign_keys="Content.iconPath", back_populates="icon_storage")
    content_snapshots = relationship("Content", foreign_keys="Content.snapshotPath", back_populates="snapshot_storage")
