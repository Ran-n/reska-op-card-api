from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from optcg_api.database import get_session
from optcg_api.models import Set

router = APIRouter(prefix="/sets", tags=["sets"])


@router.get("/", response_model=list[Set])
def list_sets(session: Session = Depends(get_session)):
    return session.exec(select(Set)).all()


@router.get("/{set_id}", response_model=Set)
def get_set(set_id: int, session: Session = Depends(get_session)):
    s = session.get(Set, set_id)
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    return s
