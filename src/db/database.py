import os
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import AsyncIterator, AsyncGenerator, Annotated
from typing import Union
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, async_scoped_session





DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:admin@localhost:5432/test")



class DatabaseSessionManager:
    def init(self):
        self.engine: Union[AsyncEngine, None] = None
        self.session_maker = None
        self.session = None

    def init_db(self):
        # Database connection parameters...

        # Creating an asynchronous engine
        self.engine = create_async_engine(
            DATABASE_URL, pool_size=20, max_overflow=0, pool_pre_ping=False
        )

        # Creating an asynchronous session class
        self.session_maker = async_sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Creating a scoped session
        self.session = async_scoped_session(self.session_maker, scopefunc=current_task)

    async def close(self):
        # Closing the database session...
        if self.engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self.engine.dispose()


sessionmanager = DatabaseSessionManager()

async_engine = create_async_engine(str(DATABASE_URL), pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@asynccontextmanager
async def get_db_for_websockets() -> AsyncIterator[AsyncSession]:
    session = sessionmanager.session()
    if session is None:
        raise Exception("DatabaseSessionManager is not initialized")
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

CurrentAsyncSession = Annotated[AsyncSession, Depends(get_db)]
