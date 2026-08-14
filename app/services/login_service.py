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

# Used to create the matching customers row when a CUSTOMER signs up, so
# that row's real id can become the new user's sub instead of trusting
# whatever the client sent.
from app.services.customer_service import create_customer

# Used to open a starter account for a new CUSTOMER at signup, so their
# dashboard has something real to show instead of the empty
# "Unable to load dashboard data" state a brand-new customer used to see.
from app.services.account_service import create_account


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


# Creates a new user with a hashed password.
# sub is now optional. For a CUSTOMER signing up through the app, sub is not
# supplied at all, name and branch_code are, and the real sub is derived
# below from the customers row this function creates. This is what was
# missing before: nothing guaranteed users.sub actually pointed at a real
# customers.id.
# Staff accounts created by hand (e.g. through
# Postman) can still pass sub directly since they have no customers row.
#
# Returns None when the username is already taken, matching how attempt_login
# reports failure and leaving the status code to the controller.
def register_user(
    db: Session,
    username: str,
    password: str,
    roles: str,
    email: str,
    sub: str = None,
    name: str = None,
    branch_code: int = None,
):
    # gensalt makes a fresh random salt every call, so two users with the same
    # password still end up with different hashes.
    salt = bcrypt.gensalt()

    # hashpw returns bytes. The column is a String, so it is decoded here
    # rather than letting SQLAlchemy store the repr of a bytes object.
    hashed_password = bcrypt.hashpw(password.encode(), salt).decode()

    # Tracked separately so it can be cleaned up below if the user insert
    # fails after this row has already been committed.
    new_customer = None
    new_account = None

    if roles == "CUSTOMER":
        # create_customer commits on its own and returns the row with its
        # real database-generated id, so this becomes the one and only
        # source of truth for sub, instead of a value typed on the frontend.
        new_customer = create_customer(db, name, email, branch_code)
        sub = str(new_customer.customer_id)
    

    # Opens a $0 Checking account in the same branch, owned by the
        # customer row just created above. create_account also commits on
        # its own, same as create_customer. Without this, a brand-new
        # customer would have a login and a customer record but zero
        # accounts, and their dashboard/account search would show nothing
        # until staff opened one for them by hand.
        new_account = create_account(
            db,
            name,
            new_customer.customer_id,
            "Checking",
            0,
            branch_code,
        )


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

        # create_customer and create_account already committed above, so a failed user insert
        # here (duplicate username/email) would otherwise leave an orphan
        # customers row with no login attached to it. The account is deleted first since it has a foreign key
        # pointing at the customer, deleting the customer first would fail
        # the same way the registration itself just did.
        if new_account is not None:
            db.delete(new_account)
            db.commit()

        if new_customer is not None:
            db.delete(new_customer)
            db.commit()

        return None

    return new_user