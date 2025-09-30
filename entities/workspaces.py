from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base
from entities.enums import WorkspaceMemberRole


class Workspace(Base):
    __tablename__ = "Workspace"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    displayName = Column(String(255), nullable=False)
    description = Column(Text)
    query = Column(Text, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    crawlers = relationship("WorkspaceCrawler", back_populates="workspace", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="workspace", cascade="all, delete-orphan")
    engines = relationship("WorkspaceEngine", back_populates="workspace", cascade="all, delete-orphan")
    languages = relationship("WorkspaceLanguage", back_populates="workspace", cascade="all, delete-orphan")
    categories = relationship("WorkspaceCategory", back_populates="workspace", cascade="all, delete-orphan")
    rss_feeds = relationship("WorkspaceRSS", back_populates="workspace", cascade="all, delete-orphan")
    seeds = relationship("WorkspaceSeed", back_populates="workspace", cascade="all, delete-orphan")
    sitemaps = relationship("WorkspaceSitemap", back_populates="workspace", cascade="all, delete-orphan")
    contents = relationship("WorkspaceContent", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "WorkspaceMember"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    assigneeId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="SET NULL", onupdate="CASCADE"))
    role = Column(SQLEnum(WorkspaceMemberRole), nullable=False, default=WorkspaceMemberRole.VIEW)
    assignedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[userId], back_populates="workspace_members")
    workspace = relationship("Workspace", back_populates="members")
    assignee = relationship("User", foreign_keys=[assigneeId], back_populates="assigned_members")