from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base
from entities.enums import CategoryStatus


class Category(Base):
    __tablename__ = "Category"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    parentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Category.id", ondelete="CASCADE", onupdate="CASCADE"))
    status = Column(SQLEnum(CategoryStatus), nullable=False, default=CategoryStatus.DRAFT)
    addedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Self-referencing relationship
    subcategories = relationship("Category", backref="parent", remote_side=[id])
    
    # Relationships
    content_categories = relationship("ContentCategory", back_populates="category", cascade="all, delete-orphan")
    category_datasets = relationship("ContentCategoryDataset", back_populates="category", cascade="all, delete-orphan")
    workspace_categories = relationship("WorkspaceCategory", back_populates="category", cascade="all, delete-orphan")


class ContentCategory(Base):
    __tablename__ = "ContentCategory"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoryId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Category.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="content_categories")
    content = relationship("Content", back_populates="categories")


class ContentCategoryDataset(Base):
    __tablename__ = "ContentCategoryDataset"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoryId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Category.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    reason = Column(Text)
    anotatedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    approvedAt = Column(DateTime(timezone=True))
    
    # Relationships
    category = relationship("Category", back_populates="category_datasets")
    content = relationship("Content", back_populates="category_datasets")
    user = relationship("User", back_populates="content_category_datasets")
