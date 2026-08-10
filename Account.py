from abc import ABC, abstractmethod

class Account(ABC):
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self._balance = balance # ENCAPSULATION

    def deposit(self, amount):
        if amount <= 0:
            print("Deposit amount must be positive.")
            return
        self._balance += amount
        print(f"Deposited ${amount}. New balance: ${self._balance:.2f}")
    def withdraw(self, amount):
        if amount > self._balance:
            print("Insufficient funds.")
            return
        self._balance -= amount
        print(f"Withdrew ${amount}. New balance: ${self._balance:.2f}")

    def get_balance(self):
        return self._balance

    @abstractmethod
    def account_type(self):
        pass  # every subclass MUST implement this


class SavingsAccount(Account):
    pass

class CheckingAccount(Account):
    pass

class User:
    pass