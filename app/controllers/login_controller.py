# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Used to check that the customer and branch an account points at actually
# exist, so we can answer with a clear 404 instead of letting the database
# raise a foreign key error.
from app.services.login_service import attempt_login, register_user

# Create a router for account related endpoints.
router = APIRouter(
    prefix="/api/v1",
    tags=["Login"],
)


class UserInfo:
    username: str
    password: str
    roles: str
    sub: str
    email: str


@router.post("/login")
def try_login(credentials: UserInfo, db: Session = Depends(get_db)):


    return attempt_login(db, credentials.username, credentials.password)


@router.post("/registration")
def try_login(info: UserInfo, db: Session = Depends(get_db)):


    return register_user(db, info.username, info.password, info.roles, info.email, info.sub)