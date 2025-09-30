from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class Format(Base):
    __tablename__ = "Format"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    addedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    content_formats = relationship("ContentFormat", back_populates="format", cascade="all, delete-orphan")


class ContentFormat(Base):
    __tablename__ = "ContentFormat"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    formatId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Format.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # Relationships
    format = relationship("Format", back_populates="content_formats")
    content = relationship("Content", back_populates="formats")