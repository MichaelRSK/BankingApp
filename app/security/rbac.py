from fastapi import Depends, HTTPException

from app.security.auth import get_current_user


def require_roles(*allowed_roles):

    def role_checker(current_user=Depends(get_current_user)):

        user_roles = current_user.get("roles", [])

        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker