# MongoClient is pymongo's entry point. It manages the connection to the
# MongoDB server running on this machine.
# ReturnDocument lets us say whether we want a document back as it looked
# BEFORE or AFTER an update. We use it in next_id() below.
from pymongo import MongoClient, ReturnDocument

# Where the MongoDB server is listening.
# "localhost" means the server is on this same computer, and 27017 is
# MongoDB's default port. This is the same string Compass connects with.
MONGO_URL = "mongodb://localhost:27017"

# The name of the database we created in Compass.
DATABASE_NAME = "bankingapp"

# Open the connection. Creating the client does not actually talk to the
# server yet, pymongo waits until the first real query to connect.
client = MongoClient(MONGO_URL)

# Grab the database. If it does not exist yet MongoDB creates it the first
# time we write a document into it.
database = client[DATABASE_NAME]

# Collections are MongoDB's version of tables, and each one holds documents,
# which are basically dictionaries. MongoDB creates a collection on the
# first insert, so these lines work even before the collection exists.
accounts_collection = database["accounts"]
customers_collection = database["customers"]
transactions_collection = database["transactions"]

# A small helper collection used only for handing out id numbers. It holds
# one document per counter, for example {"_id": "accounts", "value": 7}.
counters_collection = database["counters"]


# Returns the next id number for the given counter, starting at 1.
#
# Our old code used a plain Python variable (next_account_id) to track ids,
# but that resets to 1 every time the server restarts, which would collide
# with accounts already saved in the database. Storing the counter in
# MongoDB means it survives restarts.
#
# find_one_and_update does the increment and the read in a single operation,
# so two requests arriving at the same time can never get the same id.
# counter_name is the name of the counter, such as "accounts".
def next_id(counter_name: str) -> int:
    counter = counters_collection.find_one_and_update(
        # Find the counter document for this collection.
        {"_id": counter_name},
        # $inc adds 1 to the "value" field. If the field does not exist yet
        # MongoDB treats it as 0 and sets it to 1.
        {"$inc": {"value": 1}},
        # upsert means "create the document if it isn't there", so the very
        # first call works without us having to set anything up by hand.
        upsert=True,
        # Give us the document as it looks AFTER the increment, which is the
        # new id. Without this we would get the old value back.
        return_document=ReturnDocument.AFTER,
    )

    return counter["value"]