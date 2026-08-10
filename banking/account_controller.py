# APIRouter lets us define routes separately and plug them into backend.py's app.
from fastapi import APIRouter, HTTPException
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel

# Import the service function that contains the actual logic.
from banking.account_service import create_account

# Create a router for account related endpoints.
router = APIRouter()


# Defines what the request body must look like when opening an account.
# FastAPI uses this to validate incoming JSON automatically.
class AccountCreateRequest(BaseModel):
    owner: str
    account_type: str  # expected to be "Savings" or "Checking"
    balance: float = 0  # optional, defaults to 0 if not provided


# POST /api/v1/accounts
# Opens a new account using the data sent in the request body.
@router.post("/api/v1/accounts")
def open_account(request: AccountCreateRequest):
    # Call the service layer to do the actual work of creating the account.
    account_record = create_account(request.owner, request.account_type, request.balance)

    # If the service returned None, the account_type was invalid.
    if account_record is None:
        raise HTTPException(status_code=400, detail="account_type must be 'Savings' or 'Checking'")

    # Return the created account, FastAPI will convert this to a 200 JSON response.
    return account_record
