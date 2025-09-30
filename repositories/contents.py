from typing import List, Optional
from sqlalchemy.orm import Session

from entities.contents import Content, ContentBacklink, ContentMeta
from master.repositories.repository import Repository
from datetime import datetime


class ContentRepository(Repository[Content]):

    def __init__(self, db: Session):
        super().__init__(db, Content)

    def get_by_url(self, url: str) -> Optional[Content]:
        """
        Get content by URL.
        """
        return self.db.query(Content).filter(Content.url == url).first()

    def get_by_domain(self, domain: str) -> List[Content]:
        """
        Get all contents for a domain.
        """
        return self.db.query(Content).filter(Content.domain == domain).all()

    def get_by_crawler(self, crawler_id: str) -> List[Content]:
        """
        Get all contents crawled by a specific crawler.
        """
        return self.db.query(Content).filter(Content.crawlerId == crawler_id).all()

    def get_recent_content(self, limit: int = 50) -> List[Content]:
        """
        Get recently crawled content.
        """
        return self.db.query(Content).order_by(Content.crawledAt.desc()).limit(limit).all()

    def get_expired_content(self) -> List[Content]:
        """
        Get expired content.
        """
        return self.db.query(Content).filter(Content.expiredAt <= datetime.utcnow()).all()


class ContentBacklinkRepository(Repository[ContentBacklink]):
    def __init__(self, db: Session):
        super().__init__(db, ContentBacklink)

    def get_backlinks(self, content_id: str) -> List[ContentBacklink]:
        """
        Get all backlinks for a content.
        """
        return self.db.query(ContentBacklink).filter(
            ContentBacklink.outlinkId == content_id
        ).all()

    def get_outlinks(self, content_id: str) -> List[ContentBacklink]:
        """
        Get all outlinks from a content.
        """
        return self.db.query(ContentBacklink).filter(
            ContentBacklink.backlinkId == content_id
        ).all()

    def create_backlink(self, backlink_id: str, outlink_id: str) -> ContentBacklink:
        """
        Create a backlink relationship.
        """
        return self.create({
            "backlinkId": backlink_id,
            "outlinkId": outlink_id
        })


class ContentMetaRepository(Repository[ContentMeta]):
    """
    Repository for ContentMeta entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ContentMeta)

    def get_content_meta(self, content_id: str) -> List[ContentMeta]:
        """
        Get all metadata for a content.
        """
        return self.db.query(ContentMeta).filter(
            ContentMeta.contentId == content_id
        ).all()

    def get_meta_value(self, content_id: str, key: str) -> Optional[str]:
        """
        Get metadata value by key for a content.
        """
        meta = self.db.query(ContentMeta).filter(
            ContentMeta.contentId == content_id,
            ContentMeta.key == key
        ).first()
        return meta.value if meta else None

    def set_meta_value(self, content_id: str, key: str, value: str) -> ContentMeta:
        """
        Set metadata value for a content.
        """
        # Try to update existing
        existing = self.db.query(ContentMeta).filter(
            ContentMeta.contentId == content_id,
            ContentMeta.key == key
        ).first()

        if existing:
            self.update(existing.id, {"value": value})
            return existing
        else:
            return self.create({
                "contentId": content_id,
                "key": key,
                "value": value
            })