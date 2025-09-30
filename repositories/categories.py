from typing import List, Optional
from sqlalchemy.orm import Session

from entities.categories import Category, ContentCategory, ContentCategoryDataset
from entities.enums import CategoryStatus
from master.repositories.repository import Repository
from datetime import datetime



class CategoryRepository(Repository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)

    def get_root_categories(self) -> List[Category]:
        """
        Get all root categories (no parent).
        """
        return self.db.query(Category).filter(Category.parentId.is_(None)).all()

    def get_subcategories(self, parent_id: str) -> List[Category]:
        """
        Get subcategories for a parent category.
        """
        return self.db.query(Category).filter(Category.parentId == parent_id).all()

    def get_category_tree(self, root_id: str) -> List[Category]:
        """
        Get category tree starting from root.
        """
        return self.db.query(Category).filter(
            (Category.id == root_id) | (Category.parentId == root_id)
        ).all()

    def get_by_status(self, status: CategoryStatus) -> List[Category]:
        """
        Get categories by status.
        """
        return self.db.query(Category).filter(Category.status == status).all()


class ContentCategoryRepository(Repository[ContentCategory]):
    """
    Repository for ContentCategory entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ContentCategory)

    def get_content_categories(self, content_id: str) -> List[ContentCategory]:
        """
        Get all categories for a content.
        """
        return self.db.query(ContentCategory).filter(
            ContentCategory.contentId == content_id
        ).all()

    def get_category_contents(self, category_id: str) -> List[ContentCategory]:
        """
        Get all contents for a category.

        Args:
            category_id: Category ID

        Returns:
            List of content-category relationships
        """
        return self.db.query(ContentCategory).filter(
            ContentCategory.categoryId == category_id
        ).all()


class ContentCategoryDatasetRepository(Repository[ContentCategoryDataset]):
    """
    Repository for ContentCategoryDataset entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, ContentCategoryDataset)

    def get_user_datasets(self, user_id: str) -> List[ContentCategoryDataset]:
        """
        Get all datasets annotated by a user.
        """
        return self.db.query(ContentCategoryDataset).filter(
            ContentCategoryDataset.userId == user_id,
            ContentCategoryDataset.deletedAt.is_(None)
        ).all()

    def get_content_datasets(self, content_id: str) -> List[ContentCategoryDataset]:
        """
        Get all datasets for a content.
        """
        return self.db.query(ContentCategoryDataset).filter(
            ContentCategoryDataset.contentId == content_id,
            ContentCategoryDataset.deletedAt.is_(None)
        ).all()

    def soft_delete(self, dataset_id: str) -> bool:
        """
        Soft delete a dataset.
        """
        return self.update(dataset_id, {"deletedAt": datetime.utcnow()}) is not None
