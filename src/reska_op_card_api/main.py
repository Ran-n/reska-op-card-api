#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/12 16:56:47.000000
Revised: 2026/06/29 08:02:37.111137
"""

import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from reska_op_card_api.database import engine, init_db
from reska_op_card_api.models import ApiKeyLog
from reska_op_card_api.routers import admin, cards, lookups, naips, sets

load_dotenv()

_log = logging.getLogger(__name__)


class _RedactApiKey(logging.Filter):
    _re = re.compile(r"((api_key|new_key)=)[^&\s\"]+")

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.args = tuple(self._re.sub(r"\1[REDACTED]", a) if isinstance(a, str) else a for a in record.args)
        return True


logging.getLogger("uvicorn.access").addFilter(_RedactApiKey())

IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="reska-op-card-api", lifespan=lifespan, redirect_slashes=False)


@app.middleware("http")
async def _log_api_key_access(request: Request, call_next):
    response = await call_next(request)
    key_id = getattr(request.state, "api_key_id", None)
    if key_id is not None:
        try:
            with Session(engine) as session:
                session.add(
                    ApiKeyLog(
                        api_key_fk=key_id,
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                    )
                )
                session.commit()
        except Exception:
            _log.exception("Failed to write access log for api_key_id=%s", key_id)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(cards.router)
app.include_router(naips.router)
app.include_router(sets.router)
app.include_router(lookups.router)

app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root():
    return {"message": "One Piece TCG API"}
