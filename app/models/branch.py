# Column types and ForeignKey come from the main sqlalchemy package.
from sqlalchemy import Column, Integer, String, ForeignKey

# relationship is what links two models together so we can walk from a
# branch to its staff without writing the join by hand.
from sqlalchemy.orm import relationship

# Base is the class that turns these into real tables.
from app.db.base import Base


# Staff represents one employee working at a branch.
#
# In Module 1 Branch.staff was just a list of id numbers with nothing behind
# them. Now each staff member is a real row, so an employee can carry a name
# and the database can enforce that they belong to a branch that exists.
class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)

    # ForeignKey ties this column to branches.id. PostgreSQL will refuse to
    # store a branch_id that does not match a real branch, which is the kind
    # of guarantee the in-memory list could never give us.
    branch_id = Column(Integer, ForeignKey("branches.branch_code"))

    # The other side of Branch.staff below.
    branch = relationship("Branch", back_populates="staff")


# Branch represents a physical location of the bank, with its own
# manager and staff.
class Branch(Base):
    __tablename__ = "branches"

    # Module 1's Branch had no id at all. It needs one now because accounts
    # and customers both point at a branch, and a foreign key has to point
    # at a primary key.
    # id = Column(Integer, primary_key=True)

    # unique=True means PostgreSQL rejects a second branch with the same
    # code, so branch codes stay meaningful.
    branch_code = Column(Integer, unique=True, nullable=False, primary_key=True)
    location = Column(String(200))
    manager_id = Column(String(50))

    # Every staff member at this branch. cascade="all, delete-orphan" means
    # removing a staff member from this list deletes their row, which is
    # what makes remove_staff() below behave like the original did.
    staff = relationship(
        "Staff", back_populates="branch", cascade="all, delete-orphan"
    )

    # Accounts and customers registered at this branch.
    accounts = relationship("Account", back_populates="branch")
    customers = relationship("Customer", back_populates="branch")

    # Adds a staff member to this branch.
    # In Module 1 this took a bare id. It now takes a Staff object, because
    # the staff list holds real rows rather than loose numbers.
    def add_staff(self, staff_member):
        self.staff.append(staff_member)

    # Removes a staff member from this branch, if they work here.
    def remove_staff(self, staff_member):
        if staff_member in self.staff:
            self.staff.remove(staff_member)

    # Calculates how many staff members exist per manager.
    # This model assumes exactly one manager per branch, so the ratio
    # simplifies down to just the number of staff members.
    def staff_to_manager_ratio(self):
        return len(self.staff)