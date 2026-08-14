from sqlalchemy.orm import Session

# func gives access to SQL aggregate functions like count() and sum(),
# used in get_branch_metrics to total up a branch's accounts and balances.
from sqlalchemy import func


# Import the Branch and Staff classes from their location in app/models.
from app.models.branch import Branch, Staff


# Needed to count and sum up a branch's accounts and customers for the
# metrics function below.
from app.models.account import Account
from app.models.customer import Customer

# Branch codes are stored as integers but shown as "BR001". The metrics
# response below carries both.
from app.core.branch_ref import format_branch_ref

# This file was empty until now. Branches only existed as a plain class that
# nothing ever stored, even though accounts and customers both referred to a
# branch_id. These functions give branches somewhere to live, so those
# foreign keys point at rows that actually exist.


# Creates a new branch and saves it to the branches table.
# branch_code must be unique, PostgreSQL rejects a duplicate.
def create_branch(db: Session, branch_code: str, location: str = None, manager_id: str = None):
    new_branch = Branch(
        branch_code=branch_code,
        location=location,
        manager_id=manager_id,
    )

    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)

    return new_branch


# Returns every branch we currently have stored.
def list_branches(db: Session):
    return db.query(Branch).all()


# Finds a single branch by its id.
# Returns None when there is no branch with that id.
def get_branch(db: Session, branch_code: int):
    return db.query(Branch).filter(Branch.branch_code == branch_code).first()


# Hires a staff member into a branch.
# Returns the new Staff row, or None if the branch does not exist.
def add_staff_member(db: Session, branch_code: int, name: str):
    branch = get_branch(db, branch_code)

    if branch is None:
        return None

    new_staff = Staff(name=name)

    # The Module 1 method still does the work. Appending to the relationship
    # is what sets the new row's branch_id, so we never assign it by hand.
    branch.add_staff(new_staff)

    db.commit()
    db.refresh(new_staff)

    return new_staff


# Gathers the numbers a branch manager needs to see: how many customers and
# accounts the branch has, how much money it holds in total, and how the
# branch is staffed. Returns None if the branch doesn't exist.
def get_branch_metrics(db: Session, branch_code: int):
    branch = get_branch(db, branch_code)

    if branch is None:
        return None

    customer_count = (
        db.query(func.count(Customer._customer_id))
        .filter(Customer.branch_code == branch_code)
        .scalar()
    )

    account_count = (
        db.query(func.count(Account.account_number))
        .filter(Account.branch_code == branch_code)
        .scalar()
    )

    total_balance = (
        db.query(func.sum(Account._balance))
        .filter(Account.branch_code == branch_code)
        .scalar()
    )

    return {
        "branch_code": branch.branch_code,
        # The same code in the form people read, alongside the raw number so
        # existing callers keep working.
        "branch_ref": format_branch_ref(branch.branch_code),
        "location": branch.location,
        "manager_id": branch.manager_id,
        "customer_count": customer_count,
        "account_count": account_count,
        # func.sum returns None instead of 0 when there are no matching
        # rows, so this catches that case rather than returning "null".
        "total_balance": float(total_balance) if total_balance is not None else 0.0,
        "staff_count": len(branch.staff),
        "staff_to_manager_ratio": branch.staff_to_manager_ratio(),
    }