import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.connections import Connections

HEALTH_TIMEOUT_SEC = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    conns = Connections(get_settings())
    app.state.connections = conns
    yield
    # 테스트가 app.state.connections를 가짜로 바꿔도 실제 연결은 닫는다.
    await conns.close()


app = FastAPI(title="Roundy API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _check(probe) -> str:
    try:
        await asyncio.wait_for(probe(), timeout=HEALTH_TIMEOUT_SEC)
        return "ok"
    except Exception as e:
        return f"error: {type(e).__name__}"


@app.get("/health")
async def health(request: Request) -> dict:
    conns: Connections = request.app.state.connections
    postgres, neo4j, redis = await asyncio.gather(
        _check(conns.check_postgres), _check(conns.check_neo4j), _check(conns.check_redis)
    )
    services = {"postgres": postgres, "neo4j": neo4j, "redis": redis}
    status = "ok" if all(v == "ok" for v in services.values()) else "degraded"
    return {"status": status, "services": services}
