# Customer represents a person who holds one or more accounts at the bank.
# This is a plain data-holding class, similar in style to Account.
class Customer:

    # A class attribute (shared by ALL Customer objects, not one per object).
    # We use it as a counter so every new customer gets a unique ID
    # automatically: 1, 2, 3, and so on.
    _id_counter = 0

    # Constructor method that runs when a Customer object is created.
    # name, email, and branch_id are expected to be strings.
    def __init__(self, name: str, email: str, branch_id: str):
        # Increase the shared counter, then use it as this customer's ID.
        # We write Customer._id_counter (not self._id_counter) because we
        # want to change the value on the CLASS, shared by every customer.
        Customer._id_counter += 1

        # ENCAPSULATION: the leading underscore marks this as protected.
        # It's accessed through the customer_id property below rather than
        # directly, since an ID should never be changed once it's assigned.
        self._customer_id = Customer._id_counter

        self.name = name
        self.email = email
        self.branch_id = branch_id

        # A customer can hold several accounts (Savings, Checking, etc.).
        # We store the actual Account objects here.
        self.accounts = []

    # A read-only way to access the customer's ID from outside the class.
    @property
    def customer_id(self):
        return self._customer_id

    # Links an account to this customer.
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
    # own answer.
    def get_accounts_by_type(self, account_type):
        matching_accounts = []
        for account in self.accounts:
            if account.account_type() == account_type:
                matching_accounts.append(account)
        return matching_accounts