# FastAPI is the class we use to create the actual application instance.
from fastapi import FastAPI

# Import the router that holds the /api/v1/accounts endpoint.
from app.controllers.account_controller import router as account_router

# Import the router that holds the /api/v1/transactions endpoints.
from app.controllers.transaction_controller import router as transaction_router

# Import the router that holds the /api/v1/customers endpoints.
from app.controllers.customer_controller import router as customer_router

# Import the router that holds the /api/v1/login and /api/v1/registration
# endpoints.
from app.controllers.login_controller import router as login_router

# Import the router that holds the /api/v1/branches endpoints.
from app.controllers.branch_controller import router as branch_router

# Import the router that holds the /api/v1/limits endpoints.
from app.controllers.transfer_limit_controller import router as transfer_limit_router

from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI application.
app = FastAPI()

# Allow the Vite dev server regardless of which port it landed on. Vite bumps
# to 5174, 5175 and so on when its default port is taken, so a fixed list
# silently breaks the moment that happens. The regex accepts either spelling
# of localhost on any port, and nothing else, so it stays a dev-only allowance
# rather than opening the API to the world.
#
# allow_origin_regex is matched against the whole Origin header, which is only
# ever scheme + host + port, so there is no path for a trailing slash to creep
# in. A production origin would be added to allow_origins explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, OPTIONS, GET, etc.
    allow_headers=["*"],  # Allows custom headers like Content-Type
)


# Register the account router so its routes become part of the app.
app.include_router(account_router)

# Register the transaction router so its routes become part of the app.
app.include_router(transaction_router)

# Register the customer router so its routes become part of the app.
app.include_router(customer_router)

# Register the login router so its routes become part of the app.
app.include_router(login_router)

# Register the branch router so its routes become part of the app.
app.include_router(branch_router)

# Register the transfer limit router so its routes become part of the app.
app.include_router(transfer_limit_router)