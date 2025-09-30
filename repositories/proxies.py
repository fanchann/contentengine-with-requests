from typing import List, Optional
from sqlalchemy.orm import Session

from entities.proxies import Proxy
from master.repositories.repository import Repository
from datetime import datetime


class ProxyRepository(Repository[Proxy]):
    """
    Repository for Proxy entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Proxy)

    def get_active_proxies(self) -> List[Proxy]:
        """
        Get active (not expired) proxies.
        """
        return self.db.query(Proxy).filter(
            (Proxy.expiredAt.is_(None)) | (Proxy.expiredAt > datetime.utcnow())
        ).all()

    def get_expired_proxies(self) -> List[Proxy]:
        """
        Get expired proxies.
        """
        return self.db.query(Proxy).filter(Proxy.expiredAt <= datetime.utcnow()).all()