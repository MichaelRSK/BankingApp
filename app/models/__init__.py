# Importing every model here serves two purposes.
#
# First, SQLAlchemy only knows about a model once its module has been
# imported. Relationships are declared using strings such as
# relationship("Branch"), and SQLAlchemy can only resolve those names for
# classes it has already seen.
#
# Second, Alembic compares Base.metadata against the real database to work
# out what changed. A model in a file nobody imported is invisible to that
# comparison, and Alembic would try to drop its table.
from app.models.branch import Branch, Staff
from app.models.customer import Customer
from app.models.account import Account, SavingsAccount, CheckingAccount
from app.models.transaction import Transaction

# Names re-exported from this package, so `from app.models import Account`
# works from anywhere in the app.
__all__ = [
    "Branch",
    "Staff",
    "Customer",
    "Account",
    "SavingsAccount",
    "CheckingAccount",
    "Transaction",
]