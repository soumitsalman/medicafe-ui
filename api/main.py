from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import CasesDB
from routers import cases_router, DEFAULT_FACILITY_ID
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = CasesDB(os.path.join(os.getenv("CASES_DB_PATH", "."), DEFAULT_FACILITY_ID.hex+".duckdb"))
    yield
    app.state.db.close()

app = FastAPI(
    title="Medicafe API",
    description="Case management system API for anesthesia scheduling and billing.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["X-API-KEY", "Content-Type"],
)
app.include_router(cases_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
