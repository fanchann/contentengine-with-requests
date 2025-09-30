from typing import List, Optional
from sqlalchemy.orm import Session

from entities.object_storage import ObjectStorage
from master.repositories.repository import Repository


class ObjectStorageRepository(Repository[ObjectStorage]):
    """
    Repository for ObjectStorage entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ObjectStorage)

    def get_by_hash(self, hash_value: str) -> Optional[ObjectStorage]:
        """
        Get object by hash.
        """
        return self.db.query(ObjectStorage).filter(ObjectStorage.hash == hash_value).first()

    def get_by_path(self, path: str) -> Optional[ObjectStorage]:
        """
        Get object by path.
        """
        return self.db.query(ObjectStorage).filter(ObjectStorage.path == path).first()

    def get_recent_uploads(self, limit: int = 50) -> List[ObjectStorage]:
        """
        Get recently uploaded objects.
        """
        return self.db.query(ObjectStorage).order_by(ObjectStorage.storedAt.desc()).limit(limit).all()