from fastapi import FastAPI

app = FastAPI()


customer_db = {}
account_db = []
transaction_db = []


@app.post("/api/v1/customers")
def create_customer(
    id: int,
    name: str,
    email: str,
    accounts: list[Account],
    branch_id: int
):
    customer_db[id] = Customer(id=id, name=name, email=email, accounts=accounts, branch_id=branch_id)
    
    return {
        "statusCode": 200,
        "message": "Success"
    }

@app.get("/api/v1/customers")
def get_customers():
    return {
        "statusCode": 200,
        "customers": customer_db.values()
    }

@app.get("/api/v1/customers/{id}")
def get_customer(id: int):
    return {
        "statusCode": 200,
        "customer": customer_db[id]
    }

@app.put("/api/v1/customers/{id}")
def update_customer(
    id: int,
    name: str,
    email: str,
    accounts: list[Account],
    branch_id: int
):
    customer_db[id] = Customer(id=id, name=name, email=email, accounts=accounts, branch_id=branch_id)

    return {
        "statusCode": 200,
        "message": "Success"
    }


@app.delete("/api/v1/customers/{id}")
def delete_customer(id: int):
    del customer_db[id]

    return {
        "statusCode": 200,
        "message": "Success"
    }

@app.post("/api/v1/accounts")
def get_accounts():
    return {
        "statusCode": 200,
        "accounts": account_db
    }

@app.get("/api/v1/transactions/transfer")
def get_transactions():
    return {
        "statusCode": 200,
        "transactions": transaction_db
    }

@app.get("/api/v1/accounts")
def filter_accounts(
    branch_id: int,
    min_balance: float
):
    filtered_accounts = [acc for acc in account_db if acc.get_branch_id()==branch_id and acc.check_balance() >= min_balance]

    return {
        "statusCode": 200,
        "accounts": filtered_accounts
    }

@app.get("/api/v1/transactions")
def filter_transactions(
    start_date: str,
    ttype: str
):
    filtered_transactions = [transaction for transaction in transaction_db if transaction.get_type()==ttype and transaction.start_date() == start_date]
    
    return {
        "statusCode": 200,
        "transactions": filtered_transactions
    }