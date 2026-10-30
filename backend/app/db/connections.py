"""DB 연결 객체를 앱 수명 동안 하나씩만 만들어 재사용한다."""

from neo4j import AsyncDriver, AsyncGraphDatabase
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings


class Connections:
    def __init__(self, settings: Settings):
        self.postgres: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.neo4j: AsyncDriver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self.redis: Redis = Redis.from_url(settings.redis_url)

    async def close(self) -> None:
        await self.postgres.dispose()
        await self.neo4j.close()
        await self.redis.aclose()

    async def check_postgres(self) -> None:
        async with self.postgres.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def check_neo4j(self) -> None:
        await self.neo4j.verify_connectivity()

    async def check_redis(self) -> None:
        await self.redis.ping()
