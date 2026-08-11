# Import the Customer class from its location in app/models.
from app.models.customer import Customer

# In-memory list acting as our customers "database" for now.
# Each entry is a Customer object, which already assigns its own id.
customers_db = []


# Function that creates a new customer and stores it in customers_db.
# name is the customer's full name.
# email is the customer's email address.
# branch_id is the branch the customer belongs to.
def create_customer(name: str, email: str, branch_id: str):
    new_customer = Customer(name, email, branch_id)

    # Save the customer so it can be looked up later.
    customers_db.append(new_customer)

    return new_customer


# Returns every customer we currently have stored.
def list_customers():
    return customers_db


# Finds a single customer by their id.
# Returns None so the controller knows the customer does not exist.
def get_customer(customer_id: int):
    for customer in customers_db:
        if customer.customer_id == customer_id:
            return customer
    return None


# Updates a customer's name and/or email.
# Only the values that were passed in get changed, the model handles that.
# Returns None if there is no customer with that id.
def update_customer(customer_id: int, name: str = None, email: str = None):
    customer = get_customer(customer_id)

    if customer is None:
        return None

    customer.update_info(name, email)

    return customer


# Deactivates a customer instead of deleting them.
# Returns True if it worked, False if the customer was not found.
def deactivate_customer(customer_id: int):
    customer = get_customer(customer_id)

    if customer is None:
        return False

    customer.deactivate()

    return True
