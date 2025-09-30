from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class Domain(Base):
    __tablename__ = "Domain"
    
    name = Column(String(255), primary_key=True)
    provider = Column(String(255), nullable=False)
    root = Column(String(255), ForeignKey("Domain.name", ondelete="CASCADE", onupdate="CASCADE"))
    registeredAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    discoveredAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updatedAt = Column(DateTime(timezone=True))
    modifiedAt = Column(DateTime(timezone=True))
    expiredAt = Column(DateTime(timezone=True))
    
    # Self-referencing relationship
    subdomains = relationship("Domain", backref="parent_domain", remote_side=[name])
    
    # Relationships
    dns_records = relationship("DNS", back_populates="domain", cascade="all, delete-orphan")
    contents = relationship("Content", back_populates="domain_obj", cascade="all, delete-orphan")


class DNS(Base):
    __tablename__ = "DNS"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), ForeignKey("Domain.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    priority = Column(Integer)
    discoveredAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    lastSeen = Column(DateTime(timezone=True))
    
    # Relationships
    domain = relationship("Domain", back_populates="dns_records")