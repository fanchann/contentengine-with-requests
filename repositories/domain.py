from typing import List, Optional
from sqlalchemy.orm import Session

from entities.domain import Domain, DNS
from master.repositories.repository import Repository
from datetime import datetime, timedelta


class DomainRepository(Repository[Domain]):
    """
    Repository for Domain entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Domain)

    def get_by_name(self, name: str) -> Optional[Domain]:
        """
        Get domain by name.
        """
        return self.db.query(Domain).filter(Domain.name == name).first()

    def get_root_domains(self) -> List[Domain]:
        """
        Get all root domains (no parent).
        """
        return self.db.query(Domain).filter(Domain.root.is_(None)).all()

    def get_subdomains(self, root_domain: str) -> List[Domain]:
        """
        Get subdomains for a root domain.
        """
        return self.db.query(Domain).filter(Domain.root == root_domain).all()

    def get_expired_domains(self) -> List[Domain]:
        """
        Get expired domains.
        """
        return self.db.query(Domain).filter(Domain.expiredAt <= datetime.utcnow()).all()

    def get_recently_discovered(self, limit: int = 50) -> List[Domain]:
        """
        Get recently discovered domains.
        """
        return self.db.query(Domain).order_by(Domain.discoveredAt.desc()).limit(limit).all()


class DNSRepository(Repository[DNS]):
    """
    Repository for DNS entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, DNS)

    def get_domain_dns(self, domain_name: str) -> List[DNS]:
        """
        Get all DNS records for a domain.
        """
        return self.db.query(DNS).filter(DNS.name == domain_name).all()

    def get_dns_by_type(self, domain_name: str, dns_type: str) -> List[DNS]:
        """
        Get DNS records of specific type for a domain.
        """
        return self.db.query(DNS).filter(
            DNS.name == domain_name,
            DNS.type == dns_type
        ).all()

    def get_stale_records(self) -> List[DNS]:
        """
        Get DNS records that haven't been seen recently.
        """
        cutoff = datetime.utcnow() - timedelta(days=30)
        return self.db.query(DNS).filter(
            (DNS.lastSeen.is_(None)) | (DNS.lastSeen <= cutoff)
        ).all()