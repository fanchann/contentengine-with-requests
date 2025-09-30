from typing import List, Optional
from sqlalchemy.orm import Session

from entities.workspaces import Workspace, WorkspaceMember
from entities.enums import WorkspaceMemberRole
from master.repositories.repository import Repository


class WorkspaceRepository(Repository[Workspace]):
    """
    Repository for Workspace entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Workspace)

    def get_active_workspaces(self) -> List[Workspace]:
        """
        Get all active workspaces.
        """
        return self.db.query(Workspace).filter(Workspace.deletedAt.is_(None)).all()

    def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """
        Get workspaces where user is a member.
        """
        return self.db.query(Workspace).join(WorkspaceMember).filter(
            WorkspaceMember.userId == user_id,
            Workspace.deletedAt.is_(None)
        ).all()


class WorkspaceMemberRepository(Repository[WorkspaceMember]):
    """
    Repository for WorkspaceMember entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, WorkspaceMember)

    def get_workspace_members(self, workspace_id: str) -> List[WorkspaceMember]:
        """
        Get all members of a workspace.
        """
        return self.db.query(WorkspaceMember).filter(
            WorkspaceMember.workspaceId == workspace_id
        ).all()

    def get_user_memberships(self, user_id: str) -> List[WorkspaceMember]:
        """
        Get all workspace memberships for a user.
        """
        return self.db.query(WorkspaceMember).filter(
            WorkspaceMember.userId == user_id
        ).all()

    def get_member_role(self, workspace_id: str, user_id: str) -> Optional[WorkspaceMemberRole]:
        """
        Get user's role in a workspace.
        """
        member = self.db.query(WorkspaceMember).filter(
            WorkspaceMember.workspaceId == workspace_id,
            WorkspaceMember.userId == user_id
        ).first()
        return member.role if member else None