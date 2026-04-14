"""
JWT Authentication utilities for TURBO-CDI v8.4
Token creation, verification, and user authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from turbo_cdi.presentation.api.schemas.auth_schemas import (
    User,
    TokenData,
    AuthTokenResponse,
    UserRole,
)


class JWTManager:
    """JWT token management utilities"""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            username = payload.get("username")
            role = payload.get("role")

            if user_id is None or username is None or role is None:
                return None

            token_data = TokenData(user_id=user_id, username=username, role=UserRole(role))

            # Check expiration in token data
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return None

            return token_data

        except JWTError:
            return None

    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and return token data"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token_data = self.decode_token(token)
        if token_data is None:
            raise credentials_exception

        return token_data


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(self, jwt_manager: JWTManager = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.security = HTTPBearer()

    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        TODO: Implement actual user lookup from database
        """
        # Placeholder implementation - in real system, check database
        if username_or_email == "admin" and password == "admin123":
            # Create mock admin user for testing
            return User(
                id="admin_001",
                email="admin@turbo-cdi.ai",
                username="admin",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                status="active",
                hashed_password="$2b$12$placeholder",  # Mock hashed password
            )
        elif username_or_email == "researcher" and password == "researcher123":
            return User(
                id="researcher_001",
                email="researcher@turbo-cdi.ai",
                username="researcher",
                full_name="Research User",
                role=UserRole.RESEARCHER,
                status="active",
                hashed_password="$2b$12$placeholder",
            )

        return None

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.verify(plain_password, hashed_password)

    def create_tokens(self, user: User) -> AuthTokenResponse:
        """Create access and refresh tokens for user"""
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
        }

        access_token = self.jwt_manager.create_access_token(token_data)
        refresh_token = self.jwt_manager.create_refresh_token(token_data)

        # Create public user data (without sensitive fields)
        user_public = UserPublic(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,  # UserStatus enum
            created_at=user.created_at,
            last_login=user.last_login,
        )

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_manager.access_token_expire_minutes * 60,  # seconds
            user=user_public,
        )

    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> User:
        """
        FastAPI dependency to get current authenticated user.
        Extracts and verifies JWT token from Authorization header.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = credentials.credentials
        token_data = self.jwt_manager.verify_token(token)

        # In real implementation, fetch user from database using token_data.user_id
        # For now, return mock user based on token data
        if token_data.username == "admin":
            return User(
                id=token_data.user_id,
                email="admin@turbo-cdi.ai",
                username="admin",
                role=UserRole.ADMIN,
                status="active",
                hashed_password="$2b$12$placeholder",
            )
        elif token_data.username == "researcher":
            return User(
                id=token_data.user_id,
                email="researcher@turbo-cdi.ai",
                username="researcher",
                role=UserRole.RESEARCHER,
                status="active",
                hashed_password="$2b$12$placeholder",
            )
        else:
            raise credentials_exception

    def require_role(self, required_role: UserRole):
        """Create dependency that requires specific role"""

        def role_checker(current_user: User = Depends(self.get_current_user)) -> User:
            if current_user.role != required_role and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role.value} required",
                )
            return current_user

        return role_checker

    def require_permission(self, permission: str):
        """Create dependency that requires specific permission"""

        def permission_checker(current_user: User = Depends(self.get_current_user)) -> User:
            from turbo_cdi.presentation.api.schemas.auth_schemas import ROLE_PERMISSIONS

            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            permission_enum = getattr(
                type(user_permissions[0]) if user_permissions else None,
                permission.upper().replace(":", "_"),
            )

            if permission_enum not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )
            return current_user

        return permission_checker
