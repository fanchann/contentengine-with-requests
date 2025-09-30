from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base
from entities.enums import ReportStatus


class Report(Base):
    __tablename__ = "Report"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255))
    workspaceId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Workspace.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    status = Column(SQLEnum(ReportStatus), nullable=False, default=ReportStatus.SCHEDULED)
    generatedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="reports")
    contents = relationship("ReportContent", back_populates="report", cascade="all, delete-orphan")


class ReportContent(Base):
    __tablename__ = "ReportContent"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reportId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Report.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    generatedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deletedAt = Column(DateTime(timezone=True))
    
    # Relationships
    report = relationship("Report", back_populates="contents")
    content = relationship("Content", back_populates="reports")