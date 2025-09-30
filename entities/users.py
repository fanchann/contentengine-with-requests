from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base
from entities.enums import UserRole


class User(Base):
    __tablename__ = "User"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    securityCode = Column(Text)
    recoveryCode = Column(Text)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.GUEST)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    whitelists = relationship("Whitelist", back_populates="user", cascade="all, delete-orphan")
    workspace_members = relationship("WorkspaceMember", foreign_keys="WorkspaceMember.userId", back_populates="user", cascade="all, delete-orphan")
    assigned_members = relationship("WorkspaceMember", foreign_keys="WorkspaceMember.assigneeId", back_populates="assignee")
    content_category_datasets = relationship("ContentCategoryDataset", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "Profile"
    
    id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    fullName = Column(String(255))
    title = Column(String(255))
    department = Column(String(255))
    photo = Column(Text)
    googleLink = Column(Text)
    facebookLink = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class Session(Base):
    __tablename__ = "Session"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), unique=True, nullable=False)
    userId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    userAgent = Column(Text)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    signedAt = Column(DateTime(timezone=True))
    expiredAt = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=5))
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Activity(Base):
    __tablename__ = "Activity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"))
    service = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    actionRef = Column(Text)
    ip = Column(String(255))
    endpoint = Column(Text)
    loggedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities")


class Whitelist(Base):
    __tablename__ = "Whitelist"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), unique=True, nullable=False)
    userId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    registeredAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="whitelists")

