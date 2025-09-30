from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class WorkspaceEngine(Base):
    __tablename__ = "WorkspaceEngine"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(255), nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="engines")


class WorkspaceLanguage(Base):
    __tablename__ = "WorkspaceLanguage"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(255), nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="languages")


class WorkspaceCategory(Base):
    __tablename__ = "WorkspaceCategory"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoryId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Category.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    category = relationship("Category", back_populates="workspace_categories")
    workspace = relationship("Workspace", back_populates="categories")


class WorkspaceRSS(Base):
    __tablename__ = "WorkspaceRSS"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="rss_feeds")


class WorkspaceSeed(Base):
    __tablename__ = "WorkspaceSeed"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="seeds")


class WorkspaceSitemap(Base):
    __tablename__ = "WorkspaceSitemap"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="sitemaps")


class WorkspaceContent(Base):
    __tablename__ = "WorkspaceContent"
    
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    addedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="contents")
    content = relationship("Content", back_populates="workspaces")