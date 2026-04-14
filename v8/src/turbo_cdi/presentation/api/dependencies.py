"""
FastAPI dependency injection utilities.
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional

from turbo_cdi.infrastructure.config.container import Container


def get_container(request: Request) -> Container:
    """
    Get the dependency injection container for the current request.

    The container is stored in the FastAPI app state during startup.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=500, detail="Application container not initialized")
    return container


def get_current_user(request: Request) -> Optional[str]:
    """
    Get current authenticated user.

    TODO: Implement proper authentication and user extraction.
    For now, returns None (anonymous access).
    """
    # TODO: Implement JWT token validation, session management, etc.
    return None


def require_authentication(current_user: Optional[str] = None) -> str:
    """
    Require user authentication for protected endpoints.

    Raises HTTPException if user is not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_administrator(current_user: str = Depends(require_authentication)) -> str:
    """
    Require administrator privileges.

    TODO: Implement proper role-based access control.
    """
    # TODO: Check if user has admin role
    # For now, all authenticated users are considered admins
    return current_user
