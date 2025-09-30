import re
from abc import ABC, abstractmethod
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from typing import Optional


class DatabaseConnection(ABC):
    @abstractmethod
    async def connect(self) -> AsyncConnection:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def execute_query(self, query: str):
        pass

class PostgresqlDBConnection(DatabaseConnection):
    def __init__(self, database_url: str):
        # Convert postgresql:// to postgresql+asyncpg:// and remove query parameters
        async_url = re.sub(r'^postgresql:', 'postgresql+asyncpg:', database_url)
        async_url = re.sub(r'\?.*$', '', async_url)
        
        self.database_url = async_url
        self.engine: AsyncEngine = create_async_engine(self.database_url, echo=False)
        self.connection: Optional[AsyncConnection] = None

    async def connect(self) -> AsyncConnection:
        if not self.connection:
            self.connection = await self.engine.connect()
        return self.connection
    
    async def disconnect(self) -> None:
        if self.connection:
            await self.connection.close()
            self.connection = None
        await self.engine.dispose()

    async def session(self) -> AsyncConnection:
        if not self.connection:
            await self.connect()
        return self.connection
    
    async def execute_query(self, query: str):
        if not self.connection:
            await self.connect()
        result = await self.connection.execute(text(query))
        return result.fetchall()