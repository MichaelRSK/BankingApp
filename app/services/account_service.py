# Import the account classes from their new location in app/models.
from app.models.account import SavingsAccount, CheckingAccount

# In-memory list acting as our accounts "database" for now.
# Each entry will be a dictionary holding the account info plus an id.
accounts_db = []

# Keeps track of the next id to assign, starts at 1.
next_account_id = 1


# Function that creates a new account and stores it in accounts_db.
# owner is the account holder's name.
# account_type is either "Savings" or "Checking".
# balance is the starting balance, defaults to 0.
# branch_id is the branch this account belongs to. It defaults to None so
# accounts can still be opened without one, but an account needs a branch
# before it can show up in filter_accounts() below.
def create_account(owner: str, owner_id: int, account_type: str, balance: float = 0, branch_id: int = None):
    global next_account_id  # needed since we are reassigning it below

    # Pick which class to instantiate based on the requested account_type.
    if account_type.lower() == "savings":
        new_account = SavingsAccount(owner, owner_id, balance)
    elif account_type.lower() == "checking":
        new_account = CheckingAccount(owner, owner_id, balance)
    else:
        # Return None so the controller knows the request was invalid.
        return None

    # Build the record we will store and return, using the running id.
    account_record = {
        "id": next_account_id,
        "owner": new_account.owner,
        "owner_id": new_account.owner_id,
        "account_number": new_account.account_number,
        "balance": new_account.get_balance(),
        "account_type": new_account.account_type(),
        "branch_id": branch_id,
    }

    # Save the record and bump the id counter for the next account.
    accounts_db.append(account_record)
    next_account_id += 1

    return account_record


# Returns every account that belongs to the given branch AND holds at least
# min_balance. Both conditions have to be true for an account to be included.
# branch_id is the branch we are filtering on.
# min_balance is the smallest balance an account can have and still match.
def filter_accounts(branch_id: int, min_balance: float):
    matching_accounts = []

    for account in accounts_db:
        # Skip accounts that belong to a different branch. Accounts opened
        # without a branch have None here, so they never match.
        if account["branch_id"] != branch_id:
            continue

        # Skip accounts that do not hold enough money.
        if account["balance"] < min_balance:
            continue

        matching_accounts.append(account)

    return matching_accounts