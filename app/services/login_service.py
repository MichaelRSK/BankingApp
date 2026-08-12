# Session is the type of the database handle every function here receives.
# It is passed in by the controller rather than created here, so that several
# calls can share one session and be committed together as a single unit.
from sqlalchemy.orm import Session

# The credentials table this module reads from.
from app.models.login import User

# bcrypt checks a plaintext password against a stored hash. The salt is
# embedded in the hash itself, so checkpw pulls it back out and does not need
# it passed separately.
import bcrypt

# Token creation lives in app/core/security.py, which is the one place that
# knows the signing key and the claim layout. Keeping it there means the
# login route and the request-verifying dependency can never drift apart.
from app.core.security import create_access_token


# Checks a username and password and hands back a signed access token.
#
# Returns None when the login fails, following the same pattern as the other
# services: the service reports what happened, and the controller decides
# which HTTP status that maps to.
def attempt_login(
    db: Session,
    username: str,
    password: str
):
    # one_or_none rather than one, because one raises when nothing matches and
    # an unknown username is an ordinary failed login, not a server error.
    user = (
        db.query(User)
        .filter(User.username == username)
        .one_or_none()
    )

    # Deliberately does not say which of the two was wrong. Telling an
    # attacker that a username exists lets them work through a list of
    # usernames before they start guessing passwords.
    if user is None:
        return None

    # Both arguments have to be bytes. The column stores the hash as text, so
    # it gets encoded back on the way in.
    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return None

    # roles is a single string column, and create_access_token expects a list,
    # so it is wrapped here. If roles ever becomes a real many-to-many, this
    # is the only line that has to change.
    return create_access_token(
        subject=user.sub,
        email=user.email,
        roles=[user.roles],
    )