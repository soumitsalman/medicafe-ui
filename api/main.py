from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import CasesDB
from middleware import ApiKeyMiddleware
from routers import cases_router
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = CasesDB(os.getenv("CASES_DB_PATH"))
    yield
    app.state.db.close()

app = FastAPI(
    title="Medicafe API",
    description="Schedule and billable cases API for Medicafe.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["X-API-KEY", "Content-Type"],
)
app.add_middleware(ApiKeyMiddleware)
app.include_router(cases_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
