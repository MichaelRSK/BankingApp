# datetime is how we stamp a token with its expiry. timezone.utc keeps the
# clock unambiguous, since the server and the database may sit in different
# time zones.
from datetime import datetime, timedelta, timezone

# PyJWT does the actual signing and verification.
import jwt

from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


# Raised when a token cannot be trusted, whether it was tampered with, signed
# with the wrong key, or simply expired.
#
# The controllers catch this and turn it into a 401. Defining our own error
# means the rest of the application never has to import PyJWT just to name the
# exceptions it might see.
class TokenError(Exception):
    pass


# Builds a signed access token for a user who has already proven who they are.
#
# This function does not check any password. By the time it runs, the login
# route has already verified the credentials, and this only records the result
# in a form the client can hand back on later requests.
#
# subject is the user id, stored in the "sub" claim, which is the standard
# place for "who this token is about". It goes in as a string because the JWT
# spec expects one, and some libraries reject a numeric sub outright.
def create_access_token(subject, email, roles, expires_delta=None):
    now = datetime.now(timezone.utc)

    # Let the caller override the lifetime, otherwise fall back to the value
    # from config. Refresh tokens later on will want a much longer window.
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # The payload is the set of claims travelling inside the token.
    #
    # Everything here is readable by anyone holding the token. A JWT is signed,
    # not encrypted, so it proves nobody altered the contents, but it does not
    # hide them. Never put a password or anything private in this dictionary.
    payload = {
        "sub": str(subject),
        "email": email,
        "roles": list(roles),
        # Expiry, as a UNIX timestamp. The library checks this automatically
        # when the token is decoded.
        "exp": now + expires_delta,
        # When the token was issued. Useful for auditing, and it lets us
        # invalidate everything issued before a given moment if we ever need to.
        "iat": now,
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# Verifies a token and hands back the claims inside it.
#
# Decoding is the security boundary of the whole system. If the signature does
# not match our key, the token was not issued by us and nothing in it can be
# believed. PyJWT raises in that case, and it also raises once the exp claim
# has passed, so both checks happen here.
def decode_access_token(token):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            # Passing the algorithm explicitly matters. Letting the token name
            # its own algorithm is a well known way to forge one, because an
            # attacker can ask for "none" and skip the signature entirely.
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError:
        # Covers a bad signature, a malformed string, and anything else PyJWT
        # refuses to accept.
        raise TokenError("Token is invalid")

    return payload