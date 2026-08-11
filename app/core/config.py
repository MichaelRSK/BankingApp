# os.getenv reads environment variables, the same way app/db/session.py picks
# up DATABASE_URL.
import os

# load_dotenv copies the values out of the .env file into the environment, so
# the signing key never has to be written in the source code.
from dotenv import load_dotenv

# Read .env. Calling this more than once is harmless, it simply does nothing
# the second time if the values are already loaded.
load_dotenv()


# The secret used to sign every token we issue. Anyone holding this key can
# mint a token for any user, which is why it lives in .env and not here.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Fail loudly and early if the key is missing. Without this the error would
# surface later as a confusing encoding failure inside the JWT library.
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Copy .env.example to .env and fill it in."
    )

# HS256 signs with a single shared secret, which is the right choice when the
# same application both issues and verifies the tokens. The alternatives use a
# public/private key pair, which only helps when a separate service needs to
# verify tokens without being able to create them.
JWT_ALGORITHM = "HS256"

# How long an access token stays valid. Short lifetimes limit the damage if a
# token leaks, because a stolen token stops working on its own.
ACCESS_TOKEN_EXPIRE_MINUTES = 30