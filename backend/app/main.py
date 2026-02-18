"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.extract.router import router as extract_router
from app.cv.router import router as cv_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CareerOS API",
    description="Backend proxy for CareerOS mobile app",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(extract_router, prefix="/extract", tags=["extract"])
app.include_router(cv_router, prefix="/cv", tags=["cv"])


@app.get("/health")
async def health():
    return {"status": "ok"}
