from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.security.rbac import require_roles

from app.db.session import get_db

# Import the service functions that contain the actual logic.
from app.services.transaction_service import record_transfer, filter_transactions

# Accounts come out of PostgreSQL now. get_account_for_update also locks the
# row it reads, which is what keeps two simultaneous transfers from stepping
# on each other.
from app.services.account_service import get_account_for_update


# Router for transaction-related API endpoints
router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["Transactions"],
)


# Defines the information required to make a transfer
class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float


# Transfers money from one account to another
@router.post("/transfer")
def transfer_money(
    transfer: TransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("CUSTOMER"))
):

    # A transfer cannot be zero or negative
    if transfer.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transfer amount must be greater than zero"
        )

    # Prevent transferring money back into the same account
    if transfer.from_account_id == transfer.to_account_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot transfer to the same account"
        )

    # Load and lock both accounts, always in ascending id order.
    #
    # The order matters. If one transfer locked account 1 then account 2,
    # while another locked 2 then 1, each would sit waiting for the row the
    # other holds and neither would ever finish. That is a deadlock, and
    # always taking the locks in the same order makes it impossible.
    locked_accounts = {}

    for account_id in sorted([
        transfer.from_account_id,
        transfer.to_account_id
    ]):
        locked_accounts[account_id] = get_account_for_update(
            db,
            account_id
        )

    source_account = locked_accounts[transfer.from_account_id]
    destination_account = locked_accounts[transfer.to_account_id]

    # Make sure both accounts exist before attempting the transfer
    if source_account is None:
        raise HTTPException(
            status_code=404,
            detail="Source account not found"
        )

    if destination_account is None:
        raise HTTPException(
            status_code=404,
            detail="Destination account not found"
        )

    # Make sure the customer owns the account they are transferring from
    current_customer_id = int(current_user["sub"])

    if source_account.owner_id != current_customer_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot transfer money from this account"
        )

    # Make sure the source account has enough money
    if source_account.get_balance() < transfer.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )

    # Remove the money from the source account and add it to the destination.
    # These are the same withdraw() and deposit() methods from Module 1.
    # SQLAlchemy notices the balances changed and writes them out on commit.
    source_account.withdraw(transfer.amount)
    destination_account.deposit(transfer.amount)

    # Record the completed transfer so it shows up in the history endpoint
    record_transfer(
        db,
        transfer.from_account_id,
        transfer.to_account_id,
        transfer.amount
    )

    # One commit saves all three changes together. If anything above had
    # raised, the session would be closed without committing and PostgreSQL
    # would roll the whole thing back, so money can never go missing
    # halfway through.
    db.commit()

    # Return the transfer information and updated balances
    return {
        "message": "Transfer successful",
        "from_account_id": transfer.from_account_id,
        "to_account_id": transfer.to_account_id,
        "amount": transfer.amount,
        "source_balance": float(source_account.get_balance()),
        "destination_balance": float(destination_account.get_balance())
    }


# Turns a Transaction object into a plain dictionary for the JSON response.
def transaction_to_response(transaction):
    return {
        "id": transaction.transaction_id,
        "type": transaction.transaction_type,
        "amount": float(transaction.amount),
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "timestamp": transaction.timestamp.isoformat(),
    }


# GET /api/v1/transactions?start_date=2026-01-01&type=TRANSFER
# Returns the transactions of that type that happened on or after start_date.
# start_date and type are query parameters, FastAPI reads them from the URL
# because they are not part of the path and not a request body.
@router.get("")
def get_filtered_transactions(
    start_date: str,
    type: str,
    db: Session = Depends(get_db)
):

    # Call the service layer to do the actual filtering.
    matching_transactions = filter_transactions(
        db,
        start_date,
        type
    )

    # The service returns None when start_date was not a real date.
    if matching_transactions is None:
        raise HTTPException(
            status_code=400,
            detail="start_date must be in YYYY-MM-DD format"
        )

    # Shape each transaction for the response.
    return [
        transaction_to_response(t)
        for t in matching_transactions
    ]