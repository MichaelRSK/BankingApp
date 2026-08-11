# Session is the type of the database handle every function here receives.
# It is passed in by the controller rather than created here, so that several
# calls can share one session and be committed together as a single unit.
from sqlalchemy.orm import Session, Query

# Import the account classes from their new location in app/models.
from app.models.login import User

import bcrypt

from jose import jwt

import datetime

import os


secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
expire_time = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


def create_token(
    user: Query
):
    data = {
        "email": user["email"], 
        "sub": user["sub"],
        "roles": user["roles"]
    }

    expire = datetime.utcnow() + datetime.timedelta(minutes=expire_time)

    data["exp"] = expire

    return jwt.encode(data, secret_key, algorithm=algorithm)


def try_login(
    db: Session,
    username: str,
    password: str
):

    user =  (
        db.query(User)
        .filter(User.username == username)
        .one()
    )

    if not bcrypt.checkpw(password.encode(), user["password"]):
        pass


    return {
        "Authorization": "Bearer "+create_token(user)
    }
