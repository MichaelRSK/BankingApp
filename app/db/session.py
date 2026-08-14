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
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

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