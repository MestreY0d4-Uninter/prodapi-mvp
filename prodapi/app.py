from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from prodapi.database import AsyncSessionLocal
from prodapi.routers import api_keys, automations, health, runs, schedules
from prodapi.services.scheduler import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    scheduler_service.start()

    async with AsyncSessionLocal() as session:
        await scheduler_service.restore_schedules(session)

    yield

    scheduler_service.shutdown()


app = FastAPI(
    title="ProdAPI",
    description="API de produtividade para automações",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(api_keys.router)
app.include_router(automations.router)
app.include_router(runs.runs_router)
app.include_router(runs.router)
app.include_router(schedules.router)
