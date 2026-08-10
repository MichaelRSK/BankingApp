from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .Account import SavingsAccount, CheckingAccount


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

    # Return the transfer information and updated balances
    return {
        "message": "Transfer successful",
        "from_account_id": transfer.from_account_id,
        "to_account_id": transfer.to_account_id,
        "amount": transfer.amount,
        "source_balance": source_account.get_balance(),
        "destination_balance": destination_account.get_balance()
    }