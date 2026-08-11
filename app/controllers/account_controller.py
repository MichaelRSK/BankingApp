# APIRouter lets us define routes separately and plug them into main.py's app.
from fastapi import APIRouter, HTTPException
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel

# Import the service functions that contain the actual logic.
from app.services.account_service import create_account, filter_accounts

# Create a router for account related endpoints.
router = APIRouter()


# Defines what the request body must look like when opening an account.
# FastAPI uses this to validate incoming JSON automatically.
class AccountCreateRequest(BaseModel):
    owner: str
    owner_id: int  # links this account to a Customer's ID
    account_type: str  # expected to be "Savings" or "Checking"
    balance: float = 0  # optional, defaults to 0 if not provided
    branch_id: int = None  # optional, the branch the account belongs to


# POST /api/v1/accounts
# Opens a new account using the data sent in the request body.
@router.post("/api/v1/accounts")
def open_account(request: AccountCreateRequest):
    # Call the service layer to do the actual work of creating the account.
    account_record = create_account(
        request.owner, request.owner_id, request.account_type, request.balance, request.branch_id
    )

    # If the service returned None, the account_type was invalid.
    if account_record is None:
        raise HTTPException(status_code=400, detail="account_type must be 'Savings' or 'Checking'")

    # Return the created account, FastAPI will convert this to a 200 JSON response.
    return account_record


# GET /api/v1/accounts?branch_id=123&min_balance=1000
# Returns the accounts at a branch that hold at least min_balance.
# branch_id and min_balance are query parameters, FastAPI reads them from
# the URL because they are not part of the path and not a request body.
@router.get("/api/v1/accounts")
def get_filtered_accounts(branch_id: int, min_balance: float):
    # A balance cannot be negative, so neither can the minimum we filter on.
    if min_balance < 0:
        raise HTTPException(status_code=400, detail="min_balance cannot be negative")

    # Call the service layer to do the actual filtering.
    matching_accounts = filter_accounts(branch_id, min_balance)

    # An empty list is a valid answer here, it just means nothing matched.
    return matching_accounts