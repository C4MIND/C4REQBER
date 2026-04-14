"""
User Authentication and Authorization for TURBO-CDI v8.4
JWT-based auth with role-based access control (RBAC).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from jose import JWTError, jwt
from passlib.hash import bcrypt
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User roles for RBAC"""

    ADMIN = "admin"  # Full system access
    RESEARCHER = "researcher"  # Corpus creation/modification
    ANALYST = "analyst"  # Discovery operations
    VIEWER = "viewer"  # Read-only access


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(BaseModel):
    """User model for authentication"""

    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Unique username")
    full_name: Optional[str] = Field(None, description="Full display name")
    role: UserRole = Field(UserRole.VIEWER, description="User role for permissions")
    status: UserStatus = Field(UserStatus.ACTIVE, description="Account status")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_attempts: int = Field(0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiration")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class UserCreateRequest(BaseModel):
    """Request model for user registration"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for user login"""

    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class TokenData(BaseModel):
    """JWT token payload"""

    user_id: str
    username: str
    role: UserRole
    exp: Optional[datetime] = None


class AuthTokenResponse(BaseModel):
    """Response containing authentication tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class UserPublic(BaseModel):
    """Public user information (no sensitive data)"""

    id: str
    email: EmailStr
    username: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime]


class Permission(str, Enum):
    """Available permissions in the system"""

    # Corpus permissions
    CORPUS_CREATE = "corpus:create"
    CORPUS_READ = "corpus:read"
    CORPUS_UPDATE = "corpus:update"
    CORPUS_DELETE = "corpus:delete"
    CORPUS_OPTIMIZE = "corpus:optimize"

    # Discovery permissions
    DISCOVERY_ANALYZE = "discovery:analyze"
    DISCOVERY_READ = "discovery:read"
    DISCOVERY_TRANSFORM = "discovery:transform"

    # System permissions
    SYSTEM_HEALTH = "system:health"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_ADMIN = "system:admin"

    # User permissions
    USER_MANAGE = "user:manage"
    USER_LIST = "user:list"


# Role-to-Permission mappings
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        Permission.CORPUS_CREATE,
        Permission.CORPUS_READ,
        Permission.CORPUS_UPDATE,
        Permission.CORPUS_DELETE,
        Permission.CORPUS_OPTIMIZE,
        Permission.DISCOVERY_ANALYZE,
        Permission.DISCOVERY_READ,
        Permission.DISCOVERY_TRANSFORM,
        Permission.SYSTEM_HEALTH,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_METRICS,
        Permission.SYSTEM_ADMIN,
        Permission.USER_MANAGE,
        Permission.USER_LIST,
    ],
    UserRole.RESEARCHER: [
        Permission.CORPUS_CREATE,
        Permission.CORPUS_READ,
        Permission.CORPUS_UPDATE,
        Permission.CORPUS_OPTIMIZE,
        Permission.DISCOVERY_ANALYZE,
        Permission.DISCOVERY_READ,
        Permission.DISCOVERY_TRANSFORM,
        Permission.SYSTEM_HEALTH,
    ],
    UserRole.ANALYST: [
        Permission.CORPUS_READ,
        Permission.CORPUS_UPDATE,
        Permission.DISCOVERY_ANALYZE,
        Permission.DISCOVERY_READ,
        Permission.DISCOVERY_TRANSFORM,
        Permission.SYSTEM_HEALTH,
        Permission.SYSTEM_METRICS,
    ],
    UserRole.VIEWER: [
        Permission.CORPUS_READ,
        Permission.DISCOVERY_READ,
        Permission.SYSTEM_HEALTH,
    ],
}
