# Session is the type of the database handle every function here receives.
# It is passed in by the controller rather than created here, so that several
# calls can share one session and be committed together as a single unit.
from sqlalchemy.orm import Session, Query

# Import the account classes from their new location in app/models.
from app.models.login import User

import bcrypt

# from jose import jwt

from datetime import datetime, timedelta

import os


secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
expire_time = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


def create_token(
    user: User
):
    data = {
        "email": user.email, 
        "sub": user.sub,
        "roles": user.roles
    }

    expire = datetime.now() + timedelta(minutes=int(expire_time))

    data["exp"] = expire

    return jwt.encode(data, secret_key, algorithm=algorithm)


def attempt_login(
    db: Session,
    username: str,
    password: str
):

    user =  (
        db.query(User)
        .filter(User.username == username)
        .one()
    )
    
    # return {
    #     "message": user.password
    # }

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return {
            "message": "Please enter correct credentials."
        }


    return {
        "Authorization": "Bearer "+create_token(user)
    }


def register_user(db, username, password, roles, email, sub):

    salt = bcrypt.gensalt()
    encrypted_pass = bcrypt.hashpw(password.encode(), salt)
    
    new_user = User(username, encrypted_pass.decode(), roles, email, sub)

    db.add(new_user)
    db.commit()

    # Pick up the id PostgreSQL generated during the commit.
    db.refresh(new_user)

    return new_user
