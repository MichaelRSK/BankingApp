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

# os.getenv reads the deployment's extra CORS origins, the same way
# app/core/config.py reads its settings.
import os

# Create the FastAPI application.
app = FastAPI()


# Origins allowed in addition to the localhost regex below.
#
# Read from the environment rather than hard coded, because the values are
# facts about a particular deployment, not about the application. The EC2
# public IP changes whenever the instance stops, and the CloudFront URL does
# not exist until the frontend is built, so baking either into the source
# would mean editing and redeploying code every time infrastructure moves.
#
# Set on the instance in /etc/bankingapp/env, comma separated, for example:
#
#   CORS_ALLOWED_ORIGINS=http://54.243.21.175,http://54.243.21.175:8000
#
# and later, once the frontend exists, by appending the CloudFront origin:
#
#   CORS_ALLOWED_ORIGINS=http://54.243.21.175,https://d111111abcdef8.cloudfront.net
#
# Unset locally, which leaves this empty and hands every local request to the
# regex below, exactly as before this change.
#
# An origin is scheme + host + port with no trailing slash and no path.
# "https://example.com/" or "https://example.com/app" will silently never
# match, because the browser compares against the bare origin.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Allow the Vite dev server regardless of which port it landed on. Vite bumps
# to 5174, 5175 and so on when its default port is taken, so a fixed list
# silently breaks the moment that happens. The regex accepts either spelling
# of localhost on any port, and nothing else, so it stays a dev-only allowance
# rather than opening the API to the world.
#
# allow_origin_regex is matched against the whole Origin header, which is only
# ever scheme + host + port, so there is no path for a trailing slash to creep
# in. A production origin would be added to allow_origins explicitly.
#
# allow_origins and allow_origin_regex are checked independently, and an
# origin matching either one is accepted. So the regex keeps covering local
# development on any port while the deployed origins come from the
# environment, and neither has to know about the other.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
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