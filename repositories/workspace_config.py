from typing import List, Optional
from sqlalchemy.orm import Session

from entities.workspace_configs import (
    WorkspaceEngine, WorkspaceLanguage, WorkspaceCategory,
    WorkspaceRSS, WorkspaceSeed, WorkspaceSitemap, WorkspaceContent
)
from master.repositories.repository import Repository
from datetime import datetime


class WorkspaceEngineRepository(Repository[WorkspaceEngine]):
    """
    Repository for WorkspaceEngine entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceEngine)

    def get_workspace_engines(self, workspace_id: str) -> List[WorkspaceEngine]:
        """
        Get all engines for a workspace.
        """
        return self.db.query(WorkspaceEngine).filter(
            WorkspaceEngine.workspaceId == workspace_id,
            WorkspaceEngine.deletedAt.is_(None)
        ).all()

    def soft_delete(self, engine_id: str) -> bool:
        """
        Soft delete an engine.
        """
        return self.update(engine_id, {"deletedAt": datetime.utcnow()}) is not None


class WorkspaceLanguageRepository(Repository[WorkspaceLanguage]):
    """
    Repository for WorkspaceLanguage entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceLanguage)

    def get_workspace_languages(self, workspace_id: str) -> List[WorkspaceLanguage]:
        """
        Get all languages for a workspace.
        """
        return self.db.query(WorkspaceLanguage).filter(
            WorkspaceLanguage.workspaceId == workspace_id,
            WorkspaceLanguage.deletedAt.is_(None)
        ).all()


class WorkspaceCategoryRepository(Repository[WorkspaceCategory]):
    """
    Repository for WorkspaceCategory entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceCategory)

    def get_workspace_categories(self, workspace_id: str) -> List[WorkspaceCategory]:
        """
        Get all categories for a workspace.
        """
        return self.db.query(WorkspaceCategory).filter(
            WorkspaceCategory.workspaceId == workspace_id,
            WorkspaceCategory.deletedAt.is_(None)
        ).all()


class WorkspaceRSSRepository(Repository[WorkspaceRSS]):
    """
    Repository for WorkspaceRSS entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceRSS)

    def get_workspace_rss_feeds(self, workspace_id: str) -> List[WorkspaceRSS]:
        """
        Get all RSS feeds for a workspace.
        """
        return self.db.query(WorkspaceRSS).filter(
            WorkspaceRSS.workspaceId == workspace_id,
            WorkspaceRSS.deletedAt.is_(None)
        ).all()


class WorkspaceSeedRepository(Repository[WorkspaceSeed]):
    """
    Repository for WorkspaceSeed entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceSeed)

    def get_workspace_seeds(self, workspace_id: str) -> List[WorkspaceSeed]:
        """
        Get all seeds for a workspace.
        """
        return self.db.query(WorkspaceSeed).filter(
            WorkspaceSeed.workspaceId == workspace_id,
            WorkspaceSeed.deletedAt.is_(None)
        ).all()


class WorkspaceSitemapRepository(Repository[WorkspaceSitemap]):
    """
    Repository for WorkspaceSitemap entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceSitemap)

    def get_workspace_sitemaps(self, workspace_id: str) -> List[WorkspaceSitemap]:
        """
        Get all sitemaps for a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of workspace sitemaps
        """
        return self.db.query(WorkspaceSitemap).filter(
            WorkspaceSitemap.workspaceId == workspace_id,
            WorkspaceSitemap.deletedAt.is_(None)
        ).all()


class WorkspaceContentRepository(Repository[WorkspaceContent]):
    """
    Repository for WorkspaceContent entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceContent)

    def get_workspace_contents(self, workspace_id: str) -> List[WorkspaceContent]:
        """
        Get all contents for a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of workspace contents
        """
        return self.db.query(WorkspaceContent).filter(
            WorkspaceContent.workspaceId == workspace_id
        ).all()

    def get_content_workspaces(self, content_id: str) -> List[WorkspaceContent]:
        """
        Get all workspaces for a content.

        Args:
            content_id: Content ID

        Returns:
            List of content workspaces
        """
        return self.db.query(WorkspaceContent).filter(
            WorkspaceContent.contentId == content_id
        ).all()