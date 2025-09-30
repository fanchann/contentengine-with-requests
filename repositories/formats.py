from typing import List, Optional
from sqlalchemy.orm import Session

from entities.formats import Format, ContentFormat
from master.repositories.repository import Repository


class FormatRepository(Repository[Format]):
    """
    Repository for Format entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Format)

    def get_by_name(self, name: str) -> Optional[Format]:
        """
        Get format by name.
        """
        return self.db.query(Format).filter(Format.name == name).first()


class ContentFormatRepository(Repository[ContentFormat]):
    """
    Repository for ContentFormat entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ContentFormat)

    def get_content_formats(self, content_id: str) -> List[ContentFormat]:
        """
        Get all formats for a content.
        """
        return self.db.query(ContentFormat).filter(
            ContentFormat.contentId == content_id
        ).all()

    def get_format_contents(self, format_id: str) -> List[ContentFormat]:
        """
        Get all contents for a format.
        """
        return self.db.query(ContentFormat).filter(
            ContentFormat.formatId == format_id
        ).all()