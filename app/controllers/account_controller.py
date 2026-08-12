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
from app.services.customer_service import get_customer
from app.services.branch_service import get_branch


# get_current_user verifies the JWT and identifies who's calling.
# require_role builds on it to restrict a route to specific roles.
# CurrentUser is the object both return, holding user_id, email, and roles.
from app.core.dependencies import get_current_user, require_role, CurrentUser


# record_deposit and record_withdrawal write a history row for a single
# account move, the same way record_transfer does for a two-account move.
from app.services.transaction_service import record_deposit, record_withdrawal

# Loads an account and locks its row for the rest of the transaction, so two
# tellers working on the same account cannot both read the old balance and
# overwrite each other's change.
from app.services.account_service import get_account_for_update


# Create a router for account related endpoints.
router = APIRouter()


# Defines what the request body must look like when opening an account.
# FastAPI uses this to validate incoming JSON automatically.
class AccountCreateRequest(BaseModel):
    owner: str
    owner_id: int  # links this account to a Customer's ID, required
    account_type: str  # expected to be "Savings" or "Checking"
    balance: float = 0  # optional, defaults to 0 if not provided
    branch_code: int = None  # optional, the branch the account belongs to


# Turns an Account object into a plain dictionary for the JSON response.
#
# The services used to return dictionaries already. They return ORM objects
# now, so this does the shaping instead, matching how customer_controller
# has always worked.
def account_to_response(account):
    return {
        "account_number": account.account_number,
        "owner": account.owner,
        "owner_id": account.owner_id,
        # get_balance() returns a Decimal because money is stored exactly.
        # float() keeps the JSON looking the way it always has.
        "balance": float(account.get_balance()),
        # POLYMORPHISM: the object knows its own type, we do not check it.
        "account_type": account.account_type(),
        "branch_code": account.branch_code,
    }



# POST /api/v1/accounts
# Opens a new account using the data sent in the request body.

# Only TELLER, BRANCH_MANAGER, or ADMIN can open accounts, this is staff
# work done on a customer's behalf, not something a customer does themself.
@router.post("/api/v1/accounts")
def open_account(request: AccountCreateRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role("TELLER", "BRANCH_MANAGER", "ADMIN"))):
    
     
    # owner_id and branch_code are foreign keys now, so PostgreSQL rejects the
    # insert outright if they name rows that do not exist. Checking here
    # turns what would surface as a 500 into a clear 404.
    if get_customer(db, request.owner_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found for owner_id")

    if request.branch_code is not None and get_branch(db, request.branch_code) is None:
        raise HTTPException(status_code=404, detail="Branch not found for branch_code")

    # Call the service layer to do the actual work of creating the account.
    account = create_account(
        db,
        request.owner,
        request.owner_id,
        request.account_type,
        request.balance,
        request.branch_code,
    )

    # If the service returned None, the account_type was invalid.
    if account is None:
        raise HTTPException(status_code=400, detail="account_type must be 'Savings' or 'Checking'")

    # Return the created account, FastAPI will convert this to a 200 JSON response.
    return account_to_response(account)



# GET /api/v1/accounts?branch_code=12345&min_balance=1000
# Returns the accounts at a branch that hold at least min_balance.
# branch_code and min_balance are query parameters, FastAPI reads them from
# the URL because they are not part of the path and not a request body.

# Any authenticated user can call this, but a CUSTOMER only ever sees their
# own accounts, staff roles see everyone's.
@router.get("/api/v1/accounts")
def get_filtered_accounts(branch_code: int, min_balance: float, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
  
    # A balance cannot be negative, so neither can the minimum we filter on.
    if min_balance < 0:
        raise HTTPException(status_code=400, detail="min_balance cannot be negative")

    # Call the service layer to do the actual filtering.
    matching_accounts = filter_accounts(db, branch_code, min_balance)


    # A CUSTOMER gets filtered down to only the accounts they own. Staff
    # roles (TELLER, BRANCH_MANAGER, ADMIN) skip this and see everything.
    if current_user.has_role("CUSTOMER"):
        matching_accounts = [a for a in matching_accounts if a.owner_id == current_user.user_id]


    # An empty list is a valid answer here, it just means nothing matched.
    return [account_to_response(account) for account in matching_accounts]



# record_deposit and record_withdrawal write a history row for a single
# account move, the same way record_transfer does for a two-account move.
class DepositWithdrawRequest(BaseModel):
    amount: float


# POST /api/v1/accounts/{account_number}/deposit
# A teller (or manager/admin) deposits cash directly into one account.
# No second account is involved, unlike a transfer.
@router.post("/api/v1/accounts/{account_number}/deposit")
def deposit_to_account(
    account_number: int,
    request: DepositWithdrawRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("TELLER", "BRANCH_MANAGER", "ADMIN")),
):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")

    account = get_account_for_update(db, account_number)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    account.deposit(request.amount)
    record_deposit(db, account_number, request.amount)
    db.commit()

    return account_to_response(account)


# POST /api/v1/accounts/{account_number}/withdraw
# A teller (or manager/admin) withdraws cash directly from one account.
@router.post("/api/v1/accounts/{account_number}/withdraw")
def withdraw_from_account(
    account_number: int,
    request: DepositWithdrawRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("TELLER", "BRANCH_MANAGER", "ADMIN")),
):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be greater than zero")

    account = get_account_for_update(db, account_number)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.get_balance() < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    account.withdraw(request.amount)
    record_withdrawal(db, account_number, request.amount)
    db.commit()

    return account_to_response(account)