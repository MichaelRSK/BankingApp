# Import the account classes that already exist in this package.
from banking.Account import SavingsAccount, CheckingAccount

# In-memory list acting as our accounts "database" for now.
# Each entry will be a dictionary holding the account info plus an id.
accounts_db = []

# Keeps track of the next id to assign, starts at 1.
next_account_id = 1


# Function that creates a new account and stores it in accounts_db.
# owner is the account holder's name.
# account_type is either "Savings" or "Checking".
# balance is the starting balance, defaults to 0.
def create_account(owner: str, account_type: str, balance: float = 0):
    global next_account_id  # needed since we are reassigning it below

    # Pick which class to instantiate based on the requested account_type.
    if account_type.lower() == "savings":
        new_account = SavingsAccount(owner, balance)
    elif account_type.lower() == "checking":
        new_account = CheckingAccount(owner, balance)
    else:
        # Return None so the controller knows the request was invalid.
        return None

    # Build the record we will store and return, using the running id.
    account_record = {
        "id": next_account_id,
        "owner": new_account.owner,
        "balance": new_account.get_balance(),
        "account_type": new_account.account_type(),
    }

    # Save the record and bump the id counter for the next account.
    accounts_db.append(account_record)
    next_account_id += 1

    return account_record
