from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from optcg_api.database import init_db
from fastapi.middleware.cors import CORSMiddleware

from optcg_api.routers import cards, lookups, sets

IMAGES_DIR = Path(__file__).parent.parent.parent / "card_images"
IMAGES_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="optcg-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(sets.router)
app.include_router(lookups.router)

app.mount("/card_images", StaticFiles(directory=str(IMAGES_DIR)), name="card_images")


@app.get("/")
def root():
    return {"message": "One Piece TCG API"}
