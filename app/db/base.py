# DeclarativeBase is the modern SQLAlchemy 2.x starting point for models.
from sqlalchemy.orm import DeclarativeBase


# Every model class in app/models inherits from Base.
#
# Inheriting from Base is what turns a normal Python class into a database
# table. SQLAlchemy watches for subclasses and collects their columns into
# Base.metadata, which is the in-memory picture of what our schema should
# look like. Alembic reads that same metadata to work out which migrations
# to generate, which is why every model has to inherit from this one class.
class Base(DeclarativeBase):
    pass