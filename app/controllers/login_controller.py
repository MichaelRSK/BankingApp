# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
# BaseModel is used to define the shape of the incoming request body.
# field_validator lets a field accept more than one spelling of the same
# value, which is how branch_code below takes "BR001" as well as 1.
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Import the service functions that contain the actual logic.
from app.services.login_service import attempt_login, register_user

# Branch codes are stored as integers but shown as "BR001". This turns the
# displayed form back into the number the database stores.
from app.core.branch_ref import parse_branch_ref

# Create a router for login related endpoints.
#
# The prefix is the whole path up to the routes below, so they resolve to
# POST /api/v1/login and POST /api/v1/registration.
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


# Defines what the request body must look like when registering.
#
# Separate from LoginRequest on purpose. Logging in needs two fields, and
# putting all five on one model would make roles and sub look optional at
# login and required here, when the opposite is true.
#
# sub, name and branch_code are all optional here because two different
# callers use this endpoint. A CUSTOMER signing up through the app sends
# name and branch_code, and never sub, since register_user derives a real
# sub from the customers row it creates. A staff account created by hand
# (e.g. through Postman) has no customers row, so it sends sub directly
# and leaves name/branch_code out.
class RegistrationRequest(BaseModel):
    username: str
    password: str
    roles: str
    sub: str
    email: str
    sub: str = None
    name: str = None
    branch_code: int = None

    # Accepts "BR001" as well as 1, so someone signing up can type the branch
    # code exactly as it appears on the branch's paperwork. See
    # CustomerCreateRequest for why mode="before" is needed.
    @field_validator("branch_code", mode="before")
    @classmethod
    def _accept_branch_ref(cls, value):
        return parse_branch_ref(value)

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


# POST /api/v1/registration
# Creates a new user. 201 because a new resource now exists.
@router.post("/registration", status_code=201)
def try_registration(info: RegistrationRequest, db: Session = Depends(get_db)):
    
    # A CUSTOMER needs a matching customers row created alongside the login,
    # and that row needs a name and branch_code. Checked here, before
    # touching the database, same as the name/email check in
    # customer_controller.py's add_customer.
    if info.roles == "CUSTOMER" and (not info.name or not info.branch_code):
        raise HTTPException(
            status_code=400,
            detail="name and branch_code are required to register as a customer",
        )

    new_user = register_user(
        db,
        username=info.username,
        password=info.password,
        roles=info.roles,
        email=info.email,
        sub=info.sub,
        name=info.name,
        branch_code=info.branch_code,
    )

    # The service returns None when the username, sub or email is already
    # taken. 409 says the request was fine but conflicts with what is stored.
    if new_user is None:
        raise HTTPException(
            status_code=409,
            detail="username, sub or email is already registered",
        )

    # Shaped by hand rather than returning the User object. Returning the ORM
    # object directly would put the password hash in the response body, which
    # should never leave the database.
    return {
        "username": new_user.username,
        "sub": new_user.sub,
        "email": new_user.email,
        "roles": new_user.roles,
    }