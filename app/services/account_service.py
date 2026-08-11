# Import the account classes from their new location in app/models.
from app.models.account import SavingsAccount, CheckingAccount

# ReturnDocument lets us ask for a document as it looks after an update.
from pymongo import ReturnDocument

# The accounts collection is where account documents actually live now, and
# next_id hands out the sequential id numbers we used to track by hand.
from app.database import accounts_collection, next_id

# Every query below passes this as its projection. A projection tells
# MongoDB which fields to include in the result, and "_id": 0 means "leave
# out the _id field". MongoDB adds an _id of its own to every document, and
# it is an ObjectId, which FastAPI cannot turn into JSON. Hiding it keeps
# the dictionaries we return exactly the same shape as before.
WITHOUT_MONGO_ID = {"_id": 0}


# Function that creates a new account and stores it in the accounts
# collection.
# owner is the account holder's name.
# account_type is either "Savings" or "Checking".
# balance is the starting balance, defaults to 0.
# branch_id is the branch this account belongs to. It defaults to None so
# accounts can still be opened without one, but an account needs a branch
# before it can show up in filter_accounts() below.
def create_account(owner: str, account_type: str, balance: float = 0, branch_id: int = None):
    # Pick which class to instantiate based on the requested account_type.
    if account_type.lower() == "savings":
        new_account = SavingsAccount(owner, balance)
    elif account_type.lower() == "checking":
        new_account = CheckingAccount(owner, balance)
    else:
        # Return None so the controller knows the request was invalid.
        return None

    # Build the record we will store and return. The id now comes from the
    # counter kept in MongoDB rather than a variable in this file.
    account_record = {
        "id": next_id("accounts"),
        "owner": new_account.owner,
        "balance": new_account.get_balance(),
        "account_type": new_account.account_type(),
        "branch_id": branch_id,
    }

    # insert_one writes the document to the database. It also quietly adds
    # an "_id" key to the dictionary we passed in, so we make a copy of our
    # own data to return instead of handing back the mutated original.
    accounts_collection.insert_one(dict(account_record))

    return account_record


# Returns every account that belongs to the given branch AND holds at least
# min_balance. Both conditions have to be true for an account to be included.
# branch_id is the branch we are filtering on.
# min_balance is the smallest balance an account can have and still match.
def filter_accounts(branch_id: int, min_balance: float):
    # We used to loop through a list and skip anything that did not match.
    # MongoDB does that filtering for us, so we describe what we want and it
    # only sends back the matching documents.
    #
    # $gte means "greater than or equal to". Both conditions sitting in the
    # same dictionary means MongoDB requires both to be true, which is the
    # same AND behaviour the old loop had.
    query = {
        "branch_id": branch_id,
        "balance": {"$gte": min_balance},
    }

    # find() returns a cursor, which is something we can loop over rather
    # than a list. Wrapping it in list() pulls all the results out so the
    # controller gets a plain list like it did before.
    return list(accounts_collection.find(query, WITHOUT_MONGO_ID))


# Finds a single account by its id.
# Returns None when there is no account with that id, so callers can decide
# how to report it.
def get_account(account_id: int):
    return accounts_collection.find_one({"id": account_id}, WITHOUT_MONGO_ID)


# Adds amount to an account's balance and returns the updated account.
# amount can be negative, which is how a withdrawal is done.
# Returns None if there is no account with that id.
#
# Using $inc rather than reading the balance, adding to it in Python, and
# writing it back matters here. MongoDB applies the increment in one
# operation, so two transfers touching the same account at the same moment
# cannot overwrite each other's change and lose money.
def adjust_balance(account_id: int, amount: float):
    return accounts_collection.find_one_and_update(
        {"id": account_id},
        {"$inc": {"balance": amount}},
        projection=WITHOUT_MONGO_ID,
        # Hand back the account as it looks after the change, so the caller
        # can show the new balance.
        return_document=ReturnDocument.AFTER,
    )