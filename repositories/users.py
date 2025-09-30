from typing import List, Optional
from sqlalchemy.orm import Session

from entities.users import User, Profile, Session as UserSession, Activity, Whitelist
from entities.enums import UserRole
from master.repositories.repository import Repository
from datetime import datetime



class UserRepository(Repository[User]):
    """
    Repository for User entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_active_users(self) -> List[User]:
        """
        Get all active users (not deleted).
        """
        return self.db.query(User).filter(User.deletedAt.is_(None)).all()

    def soft_delete(self, user_id: str) -> bool:
        """
        Soft delete a user by setting deletedAt timestamp.
        """
        return self.update(user_id, {"deletedAt": datetime.utcnow()}) is not None


class ProfileRepository(Repository[Profile]):
    """
    Repository for Profile entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Profile)


class UserSessionRepository(Repository[UserSession]):
    """
    Repository for Session entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, UserSession)

    def get_by_token(self, token: str) -> Optional[UserSession]:
        """
        Get session by token.
        """
        return self.db.query(UserSession).filter(UserSession.token == token).first()

    def get_active_sessions(self, user_id: str) -> List[UserSession]:
        """
        Get active sessions for a user.
        """
        return self.db.query(UserSession).filter(
            UserSession.userId == user_id,
            UserSession.expiredAt > datetime.utcnow()
        ).all()


class ActivityRepository(Repository[Activity]):
    """
    Repository for Activity entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Activity)

    def get_user_activities(self, user_id: str, limit: int = 50) -> List[Activity]:
        """
        Get recent activities for a user.
        """
        return self.db.query(Activity).filter(
            Activity.userId == user_id
        ).order_by(Activity.loggedAt.desc()).limit(limit).all()


class WhitelistRepository(Repository[Whitelist]):
    """
    Repository for Whitelist entity operations.
    """

    def __init__(self, db: Session):
        super().__init__(db, Whitelist)

    def get_by_domain(self, domain: str) -> Optional[Whitelist]:
        """
        Get whitelist entry by domain.
        """
        return self.db.query(Whitelist).filter(Whitelist.domain == domain).first()

    def get_user_whitelist(self, user_id: str) -> List[Whitelist]:
        """
        Get whitelist entries for a user.
        """
        return self.db.query(Whitelist).filter(Whitelist.userId == user_id).all()