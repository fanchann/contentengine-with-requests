from datetime import datetime
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
import uuid

from entities.base import Base


class Proxy(Base):
    __tablename__ = "Proxy"
    
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expiredAt = Column(DateTime(timezone=True))