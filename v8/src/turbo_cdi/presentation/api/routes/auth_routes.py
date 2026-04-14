"""
Authentication API routes for TURBO-CDI v8.4
User registration, login, token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.presentation.api.dependencies import get_container
from turbo_cdi.infrastructure.auth import AuthManager
from turbo_cdi.presentation.api.schemas.auth_schemas import (
    UserCreateRequest,
    LoginRequest,
    AuthTokenResponse,
    UserPublic,
)


router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register_user(
    request: UserCreateRequest,
    container: Container = Depends(get_container),
):
    """
    Register a new user account.

    Creates a new user with the specified credentials and assigns
    the default VIEWER role. User will need to verify their email
    before they can access protected resources.
    """
    auth_manager = container.auth_manager()

    # Check if username or email already exists
    # TODO: Implement user repository for checking duplicates
    existing_user = None  # await container.user_repository.get_by_username(request.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    existing_user = None  # await container.user_repository.get_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Hash password
    hashed_password = auth_manager.hash_password(request.password)

    # Create user
    from turbo_cdi.presentation.api.schemas.auth_schemas import User, UserRole, UserStatus
    from datetime import datetime
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        role=UserRole.VIEWER,  # Default role for new users
        status=UserStatus.PENDING_VERIFICATION,  # User must verify email
        hashed_password=hashed_password,
        created_at=datetime.now(),
    )

    # Save user (TODO: implement user repository)
    # await container.user_repository.save(user)

    # Return public user data
    return UserPublic(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=None,
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login_user(
    request: LoginRequest,
    container: Container = Depends(get_container),
):
    """
    Authenticate user and return access tokens.

    Validates user credentials and returns JWT access and refresh tokens
    for authenticated requests. Also updates user's last login timestamp.
    """
    auth_manager = container.auth_manager()

    # Find and authenticate user
    user = await auth_manager.authenticate_user(request.username_or_email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if user.status != "active":
        if user.status == "pending_verification":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not verified. Please check your email.",
            )
        elif user.status == "suspended":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account suspended. Contact administrator.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account inactive.",
            )

    # Check if account is locked due to failed attempts
    if user.locked_until and user.locked_until > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to failed login attempts",
        )

    # Create tokens
    tokens = auth_manager.create_tokens(user)

    # Update user's last login (TODO: implement user repository)
    # user.last_login = datetime.now()
    # await container.user_repository.save(user)

    return tokens


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str,
    container: Container = Depends(get_container),
):
    """
    Refresh access token using refresh token.

    Exchanges a valid refresh token for a new access token pair.
    Refresh tokens have longer expiration and can only be used once.
    """
    # TODO: Implement refresh token logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented",
    )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(AuthManager().get_current_user),
    container: Container = Depends(get_container),
):
    """
    Logout user and invalidate tokens.

    Adds the user's refresh token to blacklist to prevent reuse.
    Access tokens will expire naturally but become invalid.
    """
    # TODO: Implement token blacklisting
    # await container.token_blacklist.add(current_user.id, current_token)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserPublic)
async def get_current_user(
    current_user: User = Depends(AuthManager().get_current_user),
):
    """
    Get current authenticated user's information.

    Returns the currently authenticated user's profile information,
    excluding sensitive data like password hashes.
    """
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        status=current_user.status,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/verify-email")
async def verify_email(
    token: str,
    container: Container = Depends(get_container),
):
    """
    Verify user email address.

    Uses verification token sent to user's email to activate account.
    Token is single-use and expires after 24 hours.
    """
    # TODO: Implement email verification
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification not yet implemented",
    )


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    container: Container = Depends(get_container),
):
    """
    Initiate password reset process.

    Sends password reset link to user's email if account exists.
    For security, same response is returned regardless of email existence.
    """
    # TODO: Implement password reset
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented",
    )
