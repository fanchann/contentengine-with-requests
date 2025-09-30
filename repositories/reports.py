from typing import List, Optional
from sqlalchemy.orm import Session

from entities.reports import Report, ReportContent
from entities.enums import ReportStatus
from master.repositories.repository import Repository
from datetime import datetime


class ReportRepository(Repository[Report]):
    """
    Repository for Report entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Report)

    def get_workspace_reports(self, workspace_id: str) -> List[Report]:
        """
        Get all reports for a workspace.
        """
        return self.db.query(Report).filter(
            Report.workspaceId == workspace_id,
            Report.deletedAt.is_(None)
        ).all()

    def get_by_status(self, status: ReportStatus) -> List[Report]:
        """
        Get reports by status.
        """
        return self.db.query(Report).filter(Report.status == status).all()

    def soft_delete(self, report_id: str) -> bool:
        """
        Soft delete a report.
        """
        return self.update(report_id, {"deletedAt": datetime.utcnow()}) is not None


class ReportContentRepository(Repository[ReportContent]):
    """
    Repository for ReportContent entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ReportContent)

    def get_report_contents(self, report_id: str) -> List[ReportContent]:
        """
        Get all contents for a report.
        """
        return self.db.query(ReportContent).filter(
            ReportContent.reportId == report_id
        ).all()