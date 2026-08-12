# Depends is how FastAPI wires one function into another. HTTPException is how
# we answer with a 401 when a token does not hold up.
from fastapi import Depends, HTTPException

# HTTPBearer reads the "Authorization: Bearer <token>" header for us and is
# what puts the Authorize button in the /docs page.
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token, TokenError


# auto_error=False stops HTTPBearer from raising its own 403 when the header is
# missing, so we can answer with a 401 instead. A missing token means "you have
# not identified yourself", which is what 401 says. 403 would mean "we know who
# you are and you still may not do this", and that is the wrong message here.
bearer_scheme = HTTPBearer(auto_error=False)


# The caller behind the current request, built purely from the claims in the
# token.
#
# This deliberately does not query the database. The claims were signed by us,
# so they can be trusted without a second lookup, and skipping it keeps this
# file independent of the User model that Step 1 is still building. If a route
# later needs the full row, it can load it by id from here.
class CurrentUser:
    def __init__(self, user_id, email, roles):
        self.user_id = user_id
        self.email = email
        self.roles = roles

    # Small convenience so routes never have to remember whether roles is a
    # list or a single string.
    def has_role(self, role):
        return role in self.roles


# FastAPI dependency that turns an incoming Authorization header into a
# CurrentUser, and rejects the request if it cannot.
#
# Any route that adds current_user: CurrentUser = Depends(get_current_user)
# becomes protected, because the request never reaches the route body unless
# this function returns successfully.
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # No Authorization header at all, or one that was not a Bearer header.
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            # The spec says a 401 must say how to authenticate. Some clients
            # rely on this header to know they should retry with a token.
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as error:
        # Expired and malformed tokens both land here, which is the 401 case in
        # the Postman security matrix.
        raise HTTPException(
            status_code=401,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    # A token we signed always carries sub. If it is missing, the token is
    # structurally wrong even though the signature checked out.
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Token is missing the subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=int(user_id),
        email=payload.get("email"),
        # Default to no roles rather than None, so callers can iterate over
        # this without checking it first.
        roles=payload.get("roles", []),
    )



# Returns a dependency that only lets the listed roles reach the route.
#
# CUSTOMER, TELLER, BRANCH_MANAGER, and ADMIN are the roles named in the
# module README. A route stacks this on top of get_current_user, so a
# request is rejected in two stages: 401 if it isn't authenticated at all,
# 403 if it's authenticated but not allowed here.
#
# Usage: current_user: CurrentUser = Depends(require_role("ADMIN", "TELLER"))
def require_role(*allowed_roles: str):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if not any(current_user.has_role(role) for role in allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of these roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker