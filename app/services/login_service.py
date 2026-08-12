# Session is the type of the database handle every function here receives.
# It is passed in by the controller rather than created here, so that several
# calls can share one session and be committed together as a single unit.
from sqlalchemy.orm import Session

# Raised when a write breaks a database constraint, which is how a duplicate
# username surfaces.
from sqlalchemy.exc import IntegrityError

# The credentials table this module reads from.
from app.models.login import User

# bcrypt hashes a password on the way in and checks one on the way back. The
# salt is embedded in the hash itself, so checkpw pulls it back out and does
# not need it passed separately.
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
    return "Bearer " + create_access_token(
        subject=user.sub,
        email=user.email,
        roles=[user.roles],
    )


# Creates a new user with a hashed password.
#
# Returns None when the username is already taken, matching how attempt_login
# reports failure and leaving the status code to the controller.
def register_user(
    db: Session,
    username: str,
    password: str,
    roles: str,
    email: str,
    sub: str
):
    # gensalt makes a fresh random salt every call, so two users with the same
    # password still end up with different hashes.
    salt = bcrypt.gensalt()

    # hashpw returns bytes. The column is a String, so it is decoded here
    # rather than letting SQLAlchemy store the repr of a bytes object.
    hashed_password = bcrypt.hashpw(password.encode(), salt).decode()

    # Passed by keyword. The constructor takes its arguments in the order
    # user, pwd, sb, eml, rls, which is not the order this function receives
    # them in, so positional arguments would quietly swap sub and roles.
    new_user = User(
        user=username,
        pwd=hashed_password,
        sb=sub,
        eml=email,
        rls=roles,
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        # Username, sub and email are all unique. Roll back so the session is
        # usable again, then let the controller answer with a 409.
        db.rollback()
        return None

    return new_user