from abc import ABC, abstractmethod
from typing import Sequence, Protocol, TypeVar, Generic, Optional

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, obj: T) -> T: ...
    @abstractmethod
    async def get(self, id: int) -> Optional[T]: ...
    @abstractmethod
    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[T]: ...
    @abstractmethod
    async def delete(self, id: int) -> None: ...
