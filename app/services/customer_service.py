from sqlalchemy.orm import Session

# Import the Customer class from its location in app/models.
from app.models.customer import Customer


# Function that creates a new customer and saves it to the customers table.
# db is the database session.
# name is the customer's full name.
# email is the customer's email address.
# branch_id is the branch the customer belongs to. This is an integer now,
# because it points at branches.id. It used to be a string.
def create_customer(db: Session, name: str, email: str, branch_id: int = None):
    new_customer = Customer(name, email, branch_id)

    db.add(new_customer)
    db.commit()

    # Pick up the id PostgreSQL generated during the commit.
    db.refresh(new_customer)

    return new_customer


# Returns every customer we currently have stored.
def list_customers(db: Session):
    return db.query(Customer).all()


# Finds a single customer by their id.
# Returns None so the controller knows the customer does not exist.
#
# The manual loop this replaced walked every customer in a list. PostgreSQL
# looks the row up by primary key instead, which stays fast as the table
# grows.
def get_customer(db: Session, customer_id: int):
    return db.query(Customer).filter(Customer._customer_id == customer_id).first()


# Updates a customer's name and/or email.
# Only the values that were passed in get changed, the model handles that.
# Returns None if there is no customer with that id.
def update_customer(db: Session, customer_id: int, name: str = None, email: str = None):
    customer = get_customer(db, customer_id)

    if customer is None:
        return None

    # The Module 1 method still does the work. SQLAlchemy notices that the
    # object changed and writes the new values out on commit, so there is no
    # separate "save" step to remember.
    customer.update_info(name, email)

    db.commit()
    db.refresh(customer)

    return customer


# Deactivates a customer instead of deleting them.
# Returns True if it worked, False if the customer was not found.
def deactivate_customer(db: Session, customer_id: int):
    customer = get_customer(db, customer_id)

    if customer is None:
        return False

    customer.deactivate()

    db.commit()

    return True