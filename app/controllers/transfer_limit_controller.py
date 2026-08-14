# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Import the service functions that contain the actual logic.
from app.services.transfer_limit_service import (
    create_limit,
    get_limits,
    get_limit,
    update_limit,
)

# A limit's user_id is a foreign key to customers.id, so the customer has to
# exist before one can be created. Looking it up here turns a missing record
# into a clear message instead of a foreign key violation surfacing as a 500.
from app.services.customer_service import get_customer

# get_current_user verifies the JWT and identifies who's calling.
# CurrentUser is the object it returns, holding user_id, email, and roles.
#
# require_role is deliberately not used here. Every route below acts only on
# the caller's own limits, so there is nothing a role could usefully gate:
# any authenticated user is allowed to manage their own caps and nobody's
# else's, which the user_id from the token already guarantees.
from app.core.dependencies import get_current_user, CurrentUser


# Create a router for transfer limit related endpoints.
#
# The prefix is the whole path up to the routes below, so they resolve to
# POST /api/v1/limits, GET /api/v1/limits and PUT /api/v1/limits/{limit_id}.
router = APIRouter(
    prefix="/api/v1/limits",
    tags=["Transfer Limits"],
)


# Defines what the request body must look like when creating a limit.
#
# Both fields default to None so we can return our own 400 when they are
# left out, instead of FastAPI's automatic validation error.
class LimitCreateRequest(BaseModel):
    # One of PER_TRANSACTION, DAILY or MONTHLY. Validated in the service
    # against the LimitType enum rather than here, so the list of kinds is
    # defined in exactly one place.
    limit_type: str = None
    max_amount: float = None


# Defines what the request body must look like when updating a limit.
#
# Only max_amount can change. The kind of limit and who owns it are what the
# row IS, and changing either would be creating a different limit rather
# than editing this one.
class LimitUpdateRequest(BaseModel):
    max_amount: float = None


# Turns a TransferLimit object into a plain dictionary for the JSON response.
#
# current_period_used is included on purpose, so the frontend can show
# "used X of Y" without a second request. The Decimals are converted to
# floats because that is what the other controllers return for money and
# what the JSON encoder accepts.
def limit_to_response(limit):
    return {
        "id": limit.limit_id,
        "user_id": limit.user_id,
        "limit_type": limit.limit_type,
        "max_amount": float(limit.max_amount),
        "current_period_used": float(limit.current_period_used),
        "period_start": limit.period_start.isoformat(),
    }



# POST /api/v1/limits
# Creates a new limit for the authenticated user.

# The limit is always attached to the caller's own user_id, taken from the
# token. There is no field for it in the request body, which is what stops
# anyone from setting a limit on somebody else's account.
@router.post("", status_code=201)
def add_limit(request: LimitCreateRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    # Both fields are required to create a limit.
    if request.limit_type is None or request.max_amount is None:
        raise HTTPException(status_code=400, detail="limit_type and max_amount are required")

    # A ceiling of zero would block every transfer, and a negative one is
    # meaningless. Either is a mistake rather than a limit.
    if request.max_amount <= 0:
        raise HTTPException(status_code=400, detail="max_amount must be greater than zero")

    # user_id is a foreign key to customers.id. A staff user whose token
    # subject is not a customer id would otherwise fail on the constraint
    # itself, which reaches the client as an unexplained 500.
    if get_customer(db, current_user.user_id) is None:
        raise HTTPException(
            status_code=400,
            detail="Limits can only be set on a customer record, and no customer matches this login",
        )

    new_limit = create_limit(db, current_user.user_id, request.limit_type, request.max_amount)

    # The service returns None when limit_type is not one of the three kinds.
    if new_limit is None:
        raise HTTPException(
            status_code=400,
            detail="limit_type must be one of PER_TRANSACTION, DAILY, MONTHLY",
        )

    return limit_to_response(new_limit)



# GET /api/v1/limits
# Returns the authenticated user's own limits, and nothing else.

# There is no route to list anybody else's. The user_id filter comes from
# the token rather than a query parameter, so there is no value a caller
# could send to widen it.
@router.get("")
def get_my_limits(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    limits = get_limits(db, current_user.user_id)

    # Shape each limit for the response.
    return [limit_to_response(limit) for limit in limits]



# PUT /api/v1/limits/{limit_id}
# Updates an existing limit's max_amount.

# 404 when no limit has that id, 403 when one does but belongs to somebody
# else. Telling the two apart is why the limit is looked up first: a lookup
# filtered by owner could only ever answer 404, which would quietly hide a
# genuine permission problem behind a "not found".
@router.put("/{limit_id}")
def edit_limit(limit_id: int, request: LimitUpdateRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    if request.max_amount is None:
        raise HTTPException(status_code=400, detail="max_amount is required")

    if request.max_amount <= 0:
        raise HTTPException(status_code=400, detail="max_amount must be greater than zero")

    existing_limit = get_limit(db, limit_id)

    if existing_limit is None:
        raise HTTPException(status_code=404, detail="Limit not found")

    if existing_limit.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's limit")

    # The service filters on user_id as well, so it cannot write to another
    # customer's row even though the check above has already run.
    updated_limit = update_limit(db, limit_id, current_user.user_id, request.max_amount)

    return limit_to_response(updated_limit)