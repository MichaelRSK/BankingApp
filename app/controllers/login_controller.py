# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Import the service functions that contain the actual logic.
from app.services.account_service import create_account, filter_accounts

# Used to check that the customer and branch an account points at actually
# exist, so we can answer with a clear 404 instead of letting the database
# raise a foreign key error.
from app.services.login_service import attempt_login

# Create a router for account related endpoints.
router = APIRouter(
    prefix="/api/v1/login",
    tags=["Login"],
)


class LoginRequest:
    username: str
    password: str


@router.post("/login")
def try_login(credentials: LoginRequest, db: Session = Depends(get_db)):


    if attempt_login(
        credentials.username,
        credentials.password
    ):
        pass