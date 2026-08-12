# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Import the service function that contains the actual logic.
from app.services.login_service import attempt_login

# Create a router for login related endpoints.
#
# The prefix is the whole path up to the route below, so this resolves to
# POST /api/v1/login.
router = APIRouter(
    prefix="/api/v1",
    tags=["Login"],
)


# Defines what the request body must look like when logging in.
#
# This has to inherit from BaseModel. A plain class with annotations on it
# looks similar but FastAPI cannot read a body into one, and the route fails
# as the application starts rather than when it is called.
class LoginRequest(BaseModel):
    username: str
    password: str


# POST /api/v1/login
# Exchanges a username and password for a signed access token.
@router.post("/login")
def try_login(credentials: LoginRequest, db: Session = Depends(get_db)):
    token = attempt_login(
        db,
        credentials.username,
        credentials.password,
    )

    # The service returns None when the username was unknown or the password
    # did not match. Both are 401: the caller has not proved who they are.
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            # A 401 is supposed to say how to authenticate, and some clients
            # rely on this header to know they should retry with a token.
            headers={"WWW-Authenticate": "Bearer"},
        )

    # access_token and token_type are the conventional field names, and they
    # are what the Postman collection reads to store the token for every
    # following request.
    return {
        "access_token": token,
        "token_type": "bearer",
    }