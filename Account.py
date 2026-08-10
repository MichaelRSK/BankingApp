from abc import ABC, abstractmethod

class Account(ABC):
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self._balance = balance # ENCAPSULATION


    # Method used to deposit money into the account.
    def deposit(self, amount):
        
    # Check whether the amount being deposited is zero or negative.   
        if amount <= 0:
            
            
     # Tell the user that the deposit amount must be positive.       
            print("Deposit amount must be positive.")
            return


        self._balance += amount
        print(f"Deposited ${amount}. New balance: ${self._balance:.2f}")
    
    
     # Check whether the person is trying to withdraw more money
     # than they currently have in the account.
    def withdraw(self, amount):
        if amount > self._balance:
          
     # Tell the user there isn't enough money.     
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