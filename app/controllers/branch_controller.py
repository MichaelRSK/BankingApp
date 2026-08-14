# APIRouter lets us define routes separately and plug them into main.py's app.
# Depends is how FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from app.db.session import get_db

# Import the service function that gathers a branch's numbers.
from app.services.branch_service import get_branch_metrics

# require_role restricts this route to specific roles. CurrentUser is what
# it hands back once the check passes.
from app.core.dependencies import require_role, CurrentUser

# Branch codes are stored as integers but shown as "BR001". This turns the
# displayed form back into the number the database stores.
from app.core.branch_ref import parse_branch_ref

# Create a router for branch related endpoints.
router = APIRouter()


# GET /api/v1/branches/{branch_code}/metrics
# Returns performance and staffing numbers for one branch.
# Only BRANCH_MANAGER and ADMIN can see this, matching the README's rule
# that branch performance metadata and staff metrics are manager-level
# information, not something a TELLER or CUSTOMER should have access to.
@router.get("/api/v1/branches/{branch_code}/metrics")
def get_metrics(
    branch_code: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("BRANCH_MANAGER", "ADMIN")),
):
    # Annotated as str rather than int so /branches/BR001/metrics reaches us
    # intact. FastAPI would answer 422 before this function ran if the
    # annotation still said int. A plain /branches/1/metrics still works,
    # because parse_branch_ref accepts both.
    try:
        branch_code = parse_branch_ref(branch_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    metrics = get_branch_metrics(db, branch_code)

    # If the service returned None, no branch has that code.
    if metrics is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    return metrics