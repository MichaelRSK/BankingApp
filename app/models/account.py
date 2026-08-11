# Decimal is Python's exact decimal type. Money is stored as Numeric in
# PostgreSQL, which comes back as a Decimal, so the maths below uses it too.
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Sequence
from sqlalchemy.orm import relationship

from app.db.base import Base


# Account is the base class every specific account type builds on.
#
# ABSTRACTION: in Module 1 this inherited from ABC and marked account_type()
# with @abstractmethod. That is not possible now, because ABC's metaclass and
# SQLAlchemy's declarative metaclass cannot be combined on one class. The
# intent is kept by raising NotImplementedError instead: a subclass that
# forgets to implement account_type() still fails loudly, just when the
# method is called rather than when the object is created.
#
# INHERITANCE: SavingsAccount and CheckingAccount below share this one table.
# SQLAlchemy calls that single table inheritance. The "type" column records
# which class each row is, and SQLAlchemy uses it to rebuild the right
# subclass when loading a row back out.
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    owner = Column(String(120), nullable=False)

    # ENCAPSULATION: the column is called "balance" in PostgreSQL, but in
    # Python it stays the protected _balance from Module 1, reached through
    # get_balance(). Nothing outside the class touches it directly.
    #
    # Numeric(12, 2) stores an exact number with 2 decimal places rather
    # than a float. Floats cannot represent values like 0.10 exactly, and
    # those tiny errors accumulate. Money should never be a float.
    _balance = Column("balance", Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # The discriminator column. It holds "Savings" or "Checking" and tells
    # SQLAlchemy which subclass a row belongs to.
    #
    # It is named "type" rather than "account_type" on purpose, so it does
    # not collide with the account_type() method inherited from Module 1.
    type = Column(String(20), nullable=False)

    # The customer-facing account number, separate from the primary key.
    #
    # Module 1 handed these out with a class counter that started at 1000 and
    # was bumped in __init__. A counter in Python restarts at 1000 every time
    # the server does, which would hand the same number to two accounts. A
    # PostgreSQL sequence does the same job and keeps its place permanently.
    #
    # Nothing sets this in Python. The sequence supplies it during the INSERT,
    # which is why the value only appears after the row is saved.
    account_number = Column(
        Integer,
        Sequence("account_number_seq", start=1000),
        unique=True,
        nullable=False,
        server_default=Sequence("account_number_seq", start=1000).next_value(),
    )

    branch_id = Column(Integer, ForeignKey("branches.branch_code"))

    # Links this account back to the Customer that owns it.
    #
    # nullable=False means every account must name an owner, matching the
    # required owner_id on the create request. The foreign key means the
    # customer has to actually exist.
    owner_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    branch = relationship("Branch", back_populates="accounts")

    # The Customer object behind owner_id. SQLAlchemy works the join out from
    # the foreign key, so the relationship does not have to name the column.
    customer = relationship("Customer", back_populates="accounts")

    # Tells SQLAlchemy to read "type" when deciding which class to build.
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "account",
    }

    # Keeps the constructor working the way the rest of the code calls it:
    # SavingsAccount("Alice", 1, 500.0), where 1 is the owner's customer id.
    #
    # Without this you would have to write SavingsAccount(owner="Alice",
    # _balance=Decimal("500.00")), which leaks the protected attribute name
    # to every caller. Converting the balance here means the rest of the app
    # can keep passing plain numbers.
    #
    # account_number is deliberately absent. PostgreSQL fills it from the
    # sequence when the row is inserted.
    #
    # SQLAlchemy only calls __init__ when we build a NEW object in Python. It
    # restores rows loaded from the database by a different route, so this
    # does not interfere with queries.
    def __init__(self, owner: str, owner_id: int, balance: float = 0, **kwargs):
        super().__init__(
            owner=owner,
            owner_id=owner_id,
            _balance=Decimal(str(balance)),
            **kwargs,
        )

    # Method used to add money to the account.
    def deposit(self, amount):
        # Callers pass ordinary floats, but _balance is a Decimal, and
        # Python refuses to add the two together. Converting through str()
        # avoids inheriting the float's rounding error.
        amount = Decimal(str(amount))

        # Check whether the amount being deposited is zero or negative.
        if amount <= 0:
            # Tell the user that the deposit amount must be positive.
            print("Deposit amount must be positive.")
            return

        # Add the deposit amount to the account's balance.
        self._balance = self._balance + amount
        print(f"Deposited ${amount}. New balance: ${self._balance:.2f}")

    # Method used to withdraw money from the account.
    def withdraw(self, amount):
        amount = Decimal(str(amount))

        # Check whether the person is trying to withdraw more money
        # than they currently have in the account.
        if amount > self._balance:
            # Tell the user there isn't enough money.
            print("Insufficient funds.")
            return False

        # Subtract the withdrawal amount from the balance.
        self._balance = self._balance - amount

        # Display the amount withdrawn and the new balance.
        print(f"Withdrew ${amount}. New balance: ${self._balance:.2f}")

        return True

    # Method used to retrieve the current account balance.
    def get_balance(self):
        return self._balance

    # Every concrete account subclass must provide its own version of this.
    def account_type(self):
        raise NotImplementedError("Subclasses must implement account_type()")


# SavingsAccount inherits from Account.
# INHERITANCE: it receives Account's columns and methods, such as owner,
# _balance, deposit(), withdraw(), and get_balance(). It declares no
# __tablename__ because it shares the accounts table with its parent.
class SavingsAccount(Account):
    # Rows with type = "Savings" are loaded back as SavingsAccount objects.
    __mapper_args__ = {"polymorphic_identity": "Savings"}

    def account_type(self):  # POLYMORPHISM: same method name, different result
        return "Savings"


# CheckingAccount also inherits from Account.
class CheckingAccount(Account):
    __mapper_args__ = {"polymorphic_identity": "Checking"}

    def account_type(self):
        return "Checking"