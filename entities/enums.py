from enum import Enum, IntEnum

class UserRole(Enum):
    GUEST = 0
    USER = 1
    AUDITOR = 2
    ADMIN = 3
    SUPER = 4

class WorkspaceMemberRole(Enum):
    OWNER = 0
    AUDITOR = 1
    EDITOR = 2
    VIEW = 3

class CategoryStatus(Enum):
    DRAFT = 0
    PROPOSED = 1
    IN_REVIEW = 2
    PUBLIC = 3

class ReportStatus(Enum):
    SCHEDULED = 0
    CRAWLING = 1
    DRAFT = 2
    COMPLETED = 3
    ERROR = 4
    
class PriorityLevel(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2

class JobStatus(IntEnum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
