# datetime is used to turn the start_date string into something we can
# actually compare against a transaction's timestamp.
from datetime import datetime, time

from sqlalchemy.orm import Session

# or_ lets us combine two SQLAlchemy filter conditions where matching
# either one is enough, used below to check an account against both the
# from_account_id and to_account_id columns in one query.
from sqlalchemy import or_

# Import the Transaction class from its location in app/models.
from app.models.transaction import Transaction

# Needed to look up which accounts belong to a given customer, so a
# CUSTOMER's transaction history can be filtered down to just their own.
from app.models.account import Account


# Records a completed transfer so it shows up in the transaction history.
# The transfer endpoint calls this after the money has actually moved.
#
# This deliberately does NOT commit. The transfer endpoint changes two
# account balances and writes this row, and all three have to succeed or
# fail together. Committing here would save the history row even if the
# balance changes were later rolled back. The caller commits once, at the
# end, which is what makes the whole transfer atomic.
def record_transfer(db: Session, from_account_id: int, to_account_id: int, amount: float):
    new_transaction = Transaction(
        transaction_type="TRANSFER",
        amount=amount,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )

    db.add(new_transaction)

    return new_transaction


# Records a deposit into a single account. Unlike a transfer, there is no
# source account, so from_account_id stays empty and only to_account_id
# is set.
def record_deposit(db: Session, to_account_id: int, amount: float):
    new_transaction = Transaction(
        transaction_type="DEPOSIT",
        amount=amount,
        to_account_id=to_account_id,
    )

    db.add(new_transaction)

    return new_transaction


# Records a withdrawal from a single account. Unlike a transfer, there is no
# destination account, so to_account_id stays empty and only
# from_account_id is set.
def record_withdrawal(db: Session, from_account_id: int, amount: float):
    new_transaction = Transaction(
        transaction_type="WITHDRAWAL",
        amount=amount,
        from_account_id=from_account_id,
    )

    db.add(new_transaction)

    return new_transaction


# Returns every transaction that happened on or after start_date AND matches
# the given type. Both conditions have to be true for a transaction to be
# included.
# start_date is a string in YYYY-MM-DD form, for example "2026-01-01".
# type is a label such as "TRANSFER", matched without caring about casing.

# owner_id is optional. When given, only transactions touching an account
# that customer actually owns are returned, this is what lets a CUSTOMER
# see their own history without seeing anyone else's.

# Returns None if start_date is not a real date, so the controller can
# answer with its own 400 instead of letting the error escape.
def filter_transactions(db: Session, start_date: str, type: str, owner_id: int = None):
    # Turn the incoming string into a date we can compare with. If the
    # string is malformed, strptime raises and we report that back.
    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    # timestamp is a full date AND time, while the old code compared only the
    # calendar date. Combining the start date with midnight keeps the
    # original meaning of "on or after this day", including transactions that
    # happened later on the start date itself.
    start_of_day = datetime.combine(parsed_start_date, time.min)

    # func.upper would work here too, but comparing against an upper-cased
    # Python string is enough: "transfer" and "TRANSFER" both match because
    # we store the type already upper-cased.
    #
    # Built up rather than returned straight away, because the ownership
    # filter below still has to be applied before the query runs.
    query = (
        db.query(Transaction)
        .filter(Transaction.timestamp >= start_of_day)
        .filter(Transaction.transaction_type == type.upper())
    )

    # When an owner_id is given, first find every account number that owner
    # holds, then keep only transactions where that account was either the
    # source or the destination. A transfer a customer received into their
    # account should show up in their history just as much as one they sent.
    if owner_id is not None:
        owned_account_numbers = (
            db.query(Account.account_number)
            .filter(Account.owner_id == owner_id)
            .subquery()
        )
        query = query.filter(
            or_(
                Transaction.from_account_id.in_(owned_account_numbers),
                Transaction.to_account_id.in_(owned_account_numbers),
            )
        )

    return query.all()