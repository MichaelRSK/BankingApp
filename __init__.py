from banking.Account import *


def runGeneralMenu(savings: Account, checking: Account):

    menu = """1. Savings account
2. Checking account
3. Exit"""

    running = True

    while running:
        print(menu)

        while not (1 <= (selection := int(input("Enter a valid number from the menu options above: "))) <= 3):
            print("Invalid option, try again.")
                          

        if selection == 1:
            runAccountMenu(savings)
        elif selection == 2:
            runAccountMenu(checking)
        elif selection == 3:
            running = False


def runAccountMenu(account: Account):
    menu = """1. Check balance
2. Deposit
3. Withdraw
4. Transfer
5. Go back to main menu"""

    running = True

    while running:
        print(menu)

        while  not (1 <= (selection := int(input("Enter a valid number from the menu options above: "))) <= 5):
            print("Invalid option, try again.")


        if selection == 1:
            print(f"Account balance = ${account.get_balance():.2f}")
        elif selection == 2:
            depositAmnt = float(input("Enter the amount to deposit: "))
            account.deposit(depositAmnt)
        elif selection == 3:
            withdrawAmnt = float(input("Enter the amount to withdraw: "))
            account.withdraw(withdrawAmnt)
        elif selection == 4:
            pass
        elif selection == 5:
            running = False




def main():
    owner = "John"
    savings = SavingsAccount(owner, 500.0)
    checking = CheckingAccount(owner, 500.0)

    runGeneralMenu(savings, checking)

    


if __name__ == "__main__":
    main()