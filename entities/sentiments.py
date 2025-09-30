from datetime import datetime
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class ContentSentiment(Base):
    __tablename__ = "ContentSentiment"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    score = Column(Float, nullable=False)
    anotatedAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    approvedAt = Column(DateTime(timezone=True))
    contentId = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("Content.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # Relationships
    content = relationship("Content", back_populates="sentiments")