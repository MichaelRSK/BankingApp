# os.getenv reads environment variables, which is how we pick up DATABASE_URL.
import os

# load_dotenv copies the values out of the .env file into the environment,
# so the password never has to be written in the source code.
from dotenv import load_dotenv

# create_engine builds the object that manages actual connections to
# PostgreSQL. sessionmaker builds the factory that hands out sessions.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Read .env. Calling this more than once is harmless, it simply does nothing
# the second time if the values are already loaded.
load_dotenv()

# Pull the connection string out of the environment.
DATABASE_URL = os.getenv("DATABASE_URL")

# Fail loudly and early if the variable is missing. Without this the error
# would surface much later as a confusing "could not parse None" message.
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
    )

# The engine holds a pool of connections to PostgreSQL and hands them out as
# queries need them. One engine for the whole application is correct, opening
# a new connection per request would be slow.
# echo=True would print every SQL statement, which is useful while learning.
#
# pool_pre_ping sends a cheap "are you still there" check before handing a
# pooled connection to a query, and quietly replaces it if the answer is no.
#
# Without it, a connection that died while sitting idle in the pool is handed
# out anyway and the request fails with
#
#     OperationalError: server closed the connection unexpectedly
#
# which surfaces to the caller as a 500. Connections do not stay alive
# indefinitely: Supabase's pooler closes idle ones, and anything that changes
# the network path underneath an open socket kills it too. Attaching an
# Elastic IP to the EC2 instance did exactly that, and every request failed
# until the service was restarted.
#
# The cost is one extra round trip per checkout, which is negligible next to
# the query that follows it.
#
# pool_size and max_overflow are set explicitly because the defaults are too
# large for Supabase. SQLAlchemy defaults to 5 connections plus 10 overflow,
# and Supabase's session mode pooler allows 15 clients in total, so a single
# engine at full stretch can consume the entire quota and lock out every
# other client, including psql and a second copy of the app. 5 plus 5 leaves
# headroom while still being far more concurrency than this app needs.
#
# prepare_threshold=None disables psycopg's automatic prepared statements.
#
# They have to be off when talking to a transaction mode pooler (port 6543),
# because it hands each transaction whichever backend is free. A statement
# prepared on one backend does not exist on the next, and the query fails
# with "prepared statement does not exist". Disabling them costs a little
# planning time per query and is what makes transaction mode usable at all.
# It is harmless in session mode, so it is set unconditionally rather than
# guessing the mode from the port number.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={"prepare_threshold": None},
)

# A Session is the object we run queries through, and it also tracks the
# objects we have changed so it knows what to write on commit.
#
# autocommit=False means nothing is saved until we explicitly call
# db.commit(). That is what lets a transfer change two accounts and either
# save both or neither.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Hands a database session to a FastAPI endpoint and makes sure it is closed
# again afterwards.
#
# The controllers use this with Depends(get_db). FastAPI runs the function
# up to the yield before the endpoint, hands the session over, then comes
# back and runs the finally block once the response has been sent. Closing
# the session returns its connection to the pool.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()