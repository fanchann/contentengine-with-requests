from typing import List, Optional
from sqlalchemy.orm import Session

from entities.sentiments import ContentSentiment
from master.repositories.repository import Repository


class ContentSentimentRepository(Repository[ContentSentiment]):
    """
    Repository for ContentSentiment entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ContentSentiment)

    def get_content_sentiments(self, content_id: str) -> List[ContentSentiment]:
        """
        Get all sentiments for a content.
        """
        return self.db.query(ContentSentiment).filter(
            ContentSentiment.contentId == content_id
        ).order_by(ContentSentiment.anotatedAt.desc()).all()

    def get_approved_sentiments(self, content_id: str) -> List[ContentSentiment]:
        """
        Get approved sentiments for a content.
        """
        return self.db.query(ContentSentiment).filter(
            ContentSentiment.contentId == content_id,
            ContentSentiment.approvedAt.is_not(None)
        ).order_by(ContentSentiment.approvedAt.desc()).all()

    def get_pending_sentiments(self) -> List[ContentSentiment]:
        """
        Get sentiments pending approval.
        """
        return self.db.query(ContentSentiment).filter(
            ContentSentiment.approvedAt.is_(None)
        ).all()