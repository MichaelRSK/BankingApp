from abc import ABC, abstractmethod

class Account(ABC):
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self._balance = balance # ENCAPSULATION because _balance is a private attribute

    def deposit(self, amount):
        if amount <= 0:
            print("Deposit amount must be positive.")
            return
        self._balance += amount
        print(f"Deposited ${amount:.2f}. New balance: ${self._balance:.2f}")
    def withdraw(self, amount):
        if amount <= 0:
            print("Withdrawal amount must be positive.")
            return
        if amount > self._balance:
            print("Insufficient funds.")
            return
        self._balance -= amount
        print(f"Withdrew ${amount:.2f}. New balance: ${self._balance:.2f}")

    def get_balance(self):
        return self._balance
    
    @abstractmethod
    def account_type(self):
        pass  # every subclass MUST implement this


# INHERITANCE: SavingsAccount inherits from Account
class SavingsAccount(Account):
    def __init__(self, owner, balance=0, interest_rate=0.02):
        super().__init__(owner, balance)
        self.interest_rate = interest_rate

    def add_interest(self):
        interest = self._balance * self.interest_rate
        self._balance += interest
        print(f"Interest added: ${interest:.2f}. New balance: ${self._balance:.2f}")

    def account_type(self):  # POLYMORPHISM: same method name, different result
        return "Savings"

# INHERITANCE: CheckingAccount inherits from Account
class CheckingAccount(Account):
    def __init__(self, owner, balance=0, overdraft_limit=50):
        super().__init__(owner, balance)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount):  # overrides parent's withdraw (also polymorphism)
        if amount <= 0:
            print("Withdrawal amount must be positive.")
            return
        if amount > self._balance + self.overdraft_limit:
            print("Exceeds overdraft limit.")
            return
        self._balance -= amount
        print(f"Withdrew ${amount:.2f}. New balance: ${self._balance:.2f}")

    def account_type(self):
        return "Checking"

class User:
    def __init__(self, name):
        self.name = name
        self.accounts = []

    def add_account(self, account: Account):
        self.accounts.append(account)
        print(f"Account of type '{account.account_type()}' added for user '{self.name}'.")

    def get_total_balance(self):
        total = sum(account.get_balance() for account in self.accounts)
        return total