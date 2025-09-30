from typing import List, Optional
from sqlalchemy.orm import Session

from entities.crawler import WorkspaceCrawler
from master.repositories.repository import Repository
from datetime import datetime


class WorkspaceCrawlerRepository(Repository[WorkspaceCrawler]):
    """
    Repository for WorkspaceCrawler entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceCrawler)

    def get_workspace_crawlers(self, workspace_id: str) -> List[WorkspaceCrawler]:
        """
        Get all crawlers for a workspace.
        """
        return self.db.query(WorkspaceCrawler).filter(
            WorkspaceCrawler.workspaceId == workspace_id
        ).order_by(WorkspaceCrawler.priority.desc()).all()

    def get_by_workspace(self, workspace_id: str) -> List[WorkspaceCrawler]:
        """
        Alias for get_workspace_crawlers for compatibility.
        """
        return self.get_workspace_crawlers(workspace_id)

    def get_active_crawlers(self, workspace_id: str) -> List[WorkspaceCrawler]:
        """
        Get active (not paused or exited) crawlers for a workspace.
        """
        return self.db.query(WorkspaceCrawler).filter(
            WorkspaceCrawler.workspaceId == workspace_id,
            WorkspaceCrawler.pausedAt.is_(None),
            WorkspaceCrawler.exitedAt.is_(None)
        ).order_by(WorkspaceCrawler.priority.desc()).all()

    def pause_crawler(self, crawler_id: str) -> bool:
        """
        Pause a crawler.
        """
        return self.update(crawler_id, {"pausedAt": datetime.utcnow()}) is not None

    def resume_crawler(self, crawler_id: str) -> bool:
        """
        Resume a paused crawler.
        """
        return self.update(crawler_id, {"pausedAt": None}) is not None