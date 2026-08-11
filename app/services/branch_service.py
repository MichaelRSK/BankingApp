from sqlalchemy.orm import Session

# Import the Branch and Staff classes from their location in app/models.
from app.models.branch import Branch, Staff


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
def get_branch(db: Session, branch_id: int):
    return db.query(Branch).filter(Branch.id == branch_id).first()


# Hires a staff member into a branch.
# Returns the new Staff row, or None if the branch does not exist.
def add_staff_member(db: Session, branch_id: int, name: str):
    branch = get_branch(db, branch_id)

    if branch is None:
        return None

    new_staff = Staff(name=name)

    # The Module 1 method still does the work. Appending to the relationship
    # is what sets the new row's branch_id, so we never assign it by hand.
    branch.add_staff(new_staff)

    db.commit()
    db.refresh(new_staff)

    return new_staff