from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class Content(Base):
    __tablename__ = "Content"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    domain = Column(String(255), ForeignKey("Domain.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    title = Column(Text)
    description = Column(Text)
    headerPath = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("ObjectStorage.id", ondelete="SET NULL", onupdate="CASCADE"))
    bodyPath = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("ObjectStorage.id", ondelete="SET NULL", onupdate="CASCADE"))
    status = Column(Integer, nullable=False, default=100)
    iconPath = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("ObjectStorage.id", ondelete="SET NULL", onupdate="CASCADE"))
    snapshotPath = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("ObjectStorage.id", ondelete="SET NULL", onupdate="CASCADE"))
    crawlerId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("WorkspaceCrawler.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sourceId = Column(String(255), nullable=False)
    crawledAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expiredAt = Column(DateTime(timezone=True))
    
    # Relationships
    domain_obj = relationship("Domain", back_populates="contents")
    crawler = relationship("WorkspaceCrawler", back_populates="contents")
    header_storage = relationship("ObjectStorage", foreign_keys=[headerPath], back_populates="content_headers")
    body_storage = relationship("ObjectStorage", foreign_keys=[bodyPath], back_populates="content_bodies")
    icon_storage = relationship("ObjectStorage", foreign_keys=[iconPath], back_populates="content_icons")
    snapshot_storage = relationship("ObjectStorage", foreign_keys=[snapshotPath], back_populates="content_snapshots")
    
    # Many-to-many relationships
    backlinks = relationship("Content", 
                           secondary="ContentBacklink",
                           primaryjoin="Content.id == ContentBacklink.backlinkId",
                           secondaryjoin="Content.id == ContentBacklink.outlinkId",
                           back_populates="outlinks")
    outlinks = relationship("Content",
                          secondary="ContentBacklink", 
                          primaryjoin="Content.id == ContentBacklink.outlinkId",
                          secondaryjoin="Content.id == ContentBacklink.backlinkId",
                          back_populates="backlinks")
    
    # Other relationships
    meta_data = relationship("ContentMeta", back_populates="content", cascade="all, delete-orphan")
    categories = relationship("ContentCategory", back_populates="content", cascade="all, delete-orphan")
    formats = relationship("ContentFormat", back_populates="content", cascade="all, delete-orphan")
    sentiments = relationship("ContentSentiment", back_populates="content", cascade="all, delete-orphan")
    category_datasets = relationship("ContentCategoryDataset", back_populates="content", cascade="all, delete-orphan")
    reports = relationship("ReportContent", back_populates="content", cascade="all, delete-orphan")
    workspaces = relationship("WorkspaceContent", back_populates="content", cascade="all, delete-orphan")


class ContentBacklink(Base):
    __tablename__ = "ContentBacklink"
    
    backlinkId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    outlinkId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)


class ContentMeta(Base):
    __tablename__ = "ContentMeta"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # Relationships
    content = relationship("Content", back_populates="meta_data")
