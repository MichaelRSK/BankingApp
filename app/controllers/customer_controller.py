# APIRouter lets us define routes separately and plug them into main.py's app.
from fastapi import APIRouter, HTTPException
# BaseModel is used to define the shape of the incoming request body.
from pydantic import BaseModel

# Import the service functions that contain the actual logic.
from app.services.customer_service import (
    create_customer,
    list_customers,
    get_customer,
    update_customer,
    deactivate_customer,
)

# Create a router for customer related endpoints.
router = APIRouter()


# Defines what the request body must look like when creating a customer.
# name and email default to None so we can return our own 400 when they
# are left out, instead of FastAPI's automatic validation error.
class CustomerCreateRequest(BaseModel):
    name: str = None
    email: str = None
    branch_id: str = None


# Defines what the request body must look like when updating a customer.
# Both fields are optional, only what gets sent is changed.
class CustomerUpdateRequest(BaseModel):
    name: str = None
    email: str = None


# Turns a Customer object into a plain dictionary for the JSON response.
def customer_to_response(customer):
    return {
        "id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "branch_id": customer.branch_id,
        "is_active": customer.is_active,
    }


# POST /api/v1/customers
# Creates a new customer using the data sent in the request body.
@router.post("/api/v1/customers", status_code=201)
def add_customer(request: CustomerCreateRequest):
    # Both name and email are required to create a customer.
    if not request.name or not request.email:
        raise HTTPException(status_code=400, detail="name and email are required")

    # Call the service layer to do the actual work of creating the customer.
    new_customer = create_customer(request.name, request.email, request.branch_id)

    return customer_to_response(new_customer)


# GET /api/v1/customers
# Returns every customer we currently have stored.
@router.get("/api/v1/customers")
def get_all_customers():
    customers = list_customers()

    # Shape each customer for the response.
    return [customer_to_response(customer) for customer in customers]


# GET /api/v1/customers/{customer_id}
# Returns a single customer by id.
@router.get("/api/v1/customers/{customer_id}")
def get_customer_by_id(customer_id: int):
    customer = get_customer(customer_id)

    # If the service returned None, no customer has that id.
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer_to_response(customer)


# PUT /api/v1/customers/{customer_id}
# Updates the name and/or email of an existing customer.
@router.put("/api/v1/customers/{customer_id}")
def edit_customer(customer_id: int, request: CustomerUpdateRequest):
    updated_customer = update_customer(customer_id, request.name, request.email)

    # If the service returned None, no customer has that id.
    if updated_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer_to_response(updated_customer)


# DELETE /api/v1/customers/{customer_id}
# Deactivates the customer instead of removing them from storage.
@router.delete("/api/v1/customers/{customer_id}")
def remove_customer(customer_id: int):
    was_deactivated = deactivate_customer(customer_id)

    # If the service returned False, no customer has that id.
    if not was_deactivated:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {"message": "Customer deactivated", "id": customer_id}
