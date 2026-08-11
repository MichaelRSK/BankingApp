from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


# Customer represents a person who holds one or more accounts at the bank.
class Customer(Base):
    __tablename__ = "customers"

    # ENCAPSULATION: this is the same protected-attribute idea from Module 1.
    # The first argument names the COLUMN in PostgreSQL ("id"), while the
    # attribute we access it through in Python is still _customer_id. Outside
    # code goes through the customer_id property below, so an id still cannot
    # be reassigned by accident.
    #
    # The class counter Module 1 used is gone. PostgreSQL assigns ids now,
    # which means they no longer reset to 1 when the server restarts.
    _customer_id = Column("id", Integer, primary_key=True)

    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)

    # This was a str in Module 1 while Account.branch_id was an int. They
    # both point at the same branches table, so both are integers now.
    branch_id = Column(Integer, ForeignKey("branches.branch_code"))

    # Customers are active when they are first created. We deactivate
    # instead of deleting so the customer's history is never lost.
    # nullable=False plus a default means this can never end up as NULL.
    is_active = Column(Boolean, nullable=False, default=True)

    branch = relationship("Branch", back_populates="customers")

    # A customer can hold several accounts (Savings, Checking, etc.).
    # In Module 1 this was a plain Python list that nothing ever filled in.
    # It is now a real relationship, so SQLAlchemy loads the matching
    # accounts from the database the first time we touch it.
    accounts = relationship("Account", back_populates="customer")

    # Keeps the Module 1 constructor working: Customer("Ada", "a@b.com", 1).
    #
    # is_active is set here rather than relying on the column default,
    # because a column default is only applied when the row is written. Doing
    # it here means a brand new Customer object reads as active straight
    # away, exactly as it did in Module 1.
    def __init__(self, name: str, email: str, branch_id: int = None, **kwargs):
        super().__init__(
            name=name,
            email=email,
            branch_id=branch_id,
            is_active=True,
            **kwargs,
        )

    # A read-only way to access the customer's ID from outside the class.
    @property
    def customer_id(self):
        return self._customer_id

    # Updates the customer's details. Only the arguments that were actually
    # passed in get changed, anything left as None is kept as it was.
    def update_info(self, name: str = None, email: str = None):
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email

    # Marks the customer as inactive rather than removing them.
    def deactivate(self):
        self.is_active = False

    # Links an account to this customer.
    # Appending to the relationship sets the account's customer_id for us,
    # so the link is written to the database on the next commit.
    def add_account(self, account):
        self.accounts.append(account)

    # Adds up the balances of every account this customer holds.
    def get_total_balance(self):
        total = 0
        for account in self.accounts:
            total += account.get_balance()
        return total

    # Returns only this customer's accounts of a specific type,
    # Example: get_accounts_by_type("Savings").
    # POLYMORPHISM: we call account_type() without caring whether the
    # object is a SavingsAccount or CheckingAccount, each one knows its
    # own answer. SQLAlchemy reads the discriminator column and builds the
    # right subclass for us, so this still works exactly as it did.
    def get_accounts_by_type(self, account_type):
        matching_accounts = []
        for account in self.accounts:
            if account.account_type() == account_type:
                matching_accounts.append(account)
        return matching_accounts