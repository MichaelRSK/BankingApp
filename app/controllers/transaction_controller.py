from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.account import SavingsAccount, CheckingAccount

# Import the service functions that contain the actual logic.
from app.services.transaction_service import record_transfer, filter_transactions


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


# Hardcoded accounts that I'm using for now until we implement a database
accounts = {
    1: SavingsAccount("Alice", 500.00),
    2: CheckingAccount("Bob", 300.00),
    3: SavingsAccount("Charlie", 1000.00),
    4: CheckingAccount("Diana", 750.00),
}


# Transfers money from one account to another
@router.post("/transfer")
def transfer_money(transfer: TransferRequest):

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

    # Get the accounts using the IDs provided in the request
    source_account = accounts.get(transfer.from_account_id)
    destination_account = accounts.get(transfer.to_account_id)

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

    # Make sure the source account has enough money
    if source_account.get_balance() < transfer.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )

    # Remove the money from the source account and add it to the destination
    source_account.withdraw(transfer.amount)
    destination_account.deposit(transfer.amount)

    # Record the completed transfer so it shows up in the history endpoint
    record_transfer(transfer.from_account_id, transfer.to_account_id, transfer.amount)

    # Return the transfer information and updated balances
    return {
        "message": "Transfer successful",
        "from_account_id": transfer.from_account_id,
        "to_account_id": transfer.to_account_id,
        "amount": transfer.amount,
        "source_balance": source_account.get_balance(),
        "destination_balance": destination_account.get_balance()
    }


# Turns a Transaction object into a plain dictionary for the JSON response.
def transaction_to_response(transaction):
    return {
        "id": transaction.transaction_id,
        "type": transaction.transaction_type,
        "amount": transaction.amount,
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "timestamp": transaction.timestamp.isoformat(),
    }


# GET /api/v1/transactions?start_date=2026-01-01&type=TRANSFER
# Returns the transactions of that type that happened on or after start_date.
# start_date and type are query parameters, FastAPI reads them from the URL
# because they are not part of the path and not a request body.
@router.get("")
def get_filtered_transactions(start_date: str, type: str):
    # Call the service layer to do the actual filtering.
    matching_transactions = filter_transactions(start_date, type)

    # The service returns None when start_date was not a real date.
    if matching_transactions is None:
        raise HTTPException(
            status_code=400,
            detail="start_date must be in YYYY-MM-DD format"
        )

    # Shape each transaction for the response.
    return [transaction_to_response(t) for t in matching_transactions]