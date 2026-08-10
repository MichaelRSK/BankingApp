# Import ABC (Abstract Base Class) and abstractmethod from Python's abc module.
# ABC allows us to create an abstract class, and abstractmethod allows us
# to define methods that subclasses are required to implement.
from abc import ABC, abstractmethod


# Account inherits from ABC.
# This makes Account an Abstract Base Class.
# ABSTRACTION: Account provides the general structure/behavior of an account
# without requiring us to create a specific type of account here.
class Account(ABC):
    # Constructor method that runs when an Account object is created.
    # owner is expected to be a string.
    # balance is expected to be a floating-point number and defaults to 0.0. 
    def __init__(self, owner: str, balance: float = 0):
        self.owner = owner
        self._balance = balance  # ENCAPSULATION: protected, accessed via methods only

    # Store the account owner's name.
    def deposit(self, amount):
        # Check whether the amount being deposited is zero or negative. 
        if amount <= 0:
            # Tell the user that the deposit amount must be positive.
            print("Deposit amount must be positive.")
            return
        # Add the deposit amount to the account's balance.
        self._balance += amount
        print(f"Deposited ${amount}. New balance: ${self._balance:.2f}")

    # Method used to withdraw money from the account.
    def withdraw(self, amount):
    
     # Check whether the person is trying to withdraw more money
     # than they currently have in the account.
        if amount > self._balance:
          
     # Tell the user there isn't enough money.     
            print("Insufficient funds.")
            return
        
      # Subtract the withdrawal amount from the balance.   
        self._balance -= amount
       
      # Display the amount withdrawn and the new balance. 
        print(f"Withdrew ${amount}. New balance: ${self._balance:.2f}")

    # Method used to retrieve the current account balance.
    def get_balance(self):
        return self._balance


     # @abstractmethod marks account_type() as an abstract method.
    # ABSTRACTION: Every concrete account subclass must provide its
    # own implementation of account_type().
    @abstractmethod
   
   # Define the abstract account_type method.
    def account_type(self):
        pass  # every subclass MUST implement this


# SavingsAccount inherits from Account.
# INHERITANCE: SavingsAccount receives Account's attributes and methods,
# such as owner, _balance, deposit(), withdraw(), and get_balance().
class SavingsAccount(Account):
    def account_type(self):  # POLYMORPHISM: same method name, different result
        return "Savings"


# CheckingAccount also inherits from Account.
# INHERITANCE: CheckingAccount receives Account's existing functionality.
class CheckingAccount(Account):
    def account_type(self):
        return "Checking"
