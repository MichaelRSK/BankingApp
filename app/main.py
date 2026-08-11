# FastAPI is the class we use to create the actual application instance.
from fastapi import FastAPI

# Import the router that holds the /api/v1/accounts endpoint.
from app.controllers.account_controller import router as account_router

# Import the router that holds the /api/v1/transactions endpoints.
from app.controllers.transaction_controller import router as transaction_router

# Create the FastAPI application.
app = FastAPI()

# Register the account router so its routes become part of the app.
app.include_router(account_router)

# Register the transaction router so its routes become part of the app.
app.include_router(transaction_router)