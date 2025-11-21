"""
Authentication & Authorization System for MCP API
==================================================

Provides JWT-based authentication with role-based access control (RBAC)
for securing MCP endpoints and multi-tenant operations.

Features:
- JWT token generation and validation
- Role-based access control (admin, developer, user)
- API key authentication for service-to-service
- Multi-tenant isolation
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
API_KEY_HEADER_NAME = "X-API-Key"

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


# =============================================================================
# MODELS
# =============================================================================

class User(BaseModel):
    """User model"""
    user_id: str
    username: str
    email: str
    roles: List[str] = []
    tenant_id: Optional[str] = None
    is_active: bool = True


class TokenData(BaseModel):
    """Token payload data"""
    sub: str  # user_id
    username: str
    roles: List[str]
    tenant_id: Optional[str] = None
    exp: datetime


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


# =============================================================================
# IN-MEMORY USER STORE (Replace with database in production)
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with automatic salt generation.

    Security:
        - Uses bcrypt for password hashing (industry standard)
        - Automatically generates random salt per password
        - Computationally expensive to prevent brute force attacks
        - Work factor: 12 rounds (2^12 = 4096 iterations)

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash using constant-time comparison.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def _load_demo_users() -> dict:
    """
    Load demo user credentials from environment variables.

    Security:
        - Passwords loaded from environment variables instead of hardcoded
        - Hashed with bcrypt before storing
        - Can be customized per deployment environment

    Environment Variables:
        DEMO_ADMIN_USERNAME: Admin username (default: admin)
        DEMO_ADMIN_PASSWORD: Admin password (default: admin123)
        DEMO_DEVELOPER_USERNAME: Developer username (default: developer)
        DEMO_DEVELOPER_PASSWORD: Developer password (default: dev123)
        DEMO_USER_USERNAME: User username (default: user)
        DEMO_USER_PASSWORD: User password (default: user123)

    Returns:
        Dictionary of demo users with hashed passwords
    """
    admin_username = os.getenv("DEMO_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "admin123")

    developer_username = os.getenv("DEMO_DEVELOPER_USERNAME", "developer")
    developer_password = os.getenv("DEMO_DEVELOPER_PASSWORD", "dev123")

    user_username = os.getenv("DEMO_USER_USERNAME", "user")
    user_password = os.getenv("DEMO_USER_PASSWORD", "user123")

    return {
        admin_username: {
            "user_id": "user_admin",
            "username": admin_username,
            "email": f"{admin_username}@example.com",
            "password_hash": hash_password(admin_password),
            "roles": ["admin", "developer", "user"],
            "tenant_id": "tenant_default",
            "is_active": True
        },
        developer_username: {
            "user_id": "user_dev",
            "username": developer_username,
            "email": f"{developer_username}@example.com",
            "password_hash": hash_password(developer_password),
            "roles": ["developer", "user"],
            "tenant_id": "tenant_default",
            "is_active": True
        },
        user_username: {
            "user_id": "user_001",
            "username": user_username,
            "email": f"{user_username}@example.com",
            "password_hash": hash_password(user_password),
            "roles": ["user"],
            "tenant_id": "tenant_default",
            "is_active": True
        }
    }


# Demo users for testing - loaded from environment variables
DEMO_USERS = _load_demo_users()

# API Keys for service-to-service authentication
API_KEYS = {
    "sk_test_abc123": {
        "name": "Test Service Key",
        "tenant_id": "tenant_default",
        "roles": ["developer"],
        "is_active": True
    },
    "sk_prod_xyz789": {
        "name": "Production Service Key",
        "tenant_id": "tenant_prod",
        "roles": ["admin"],
        "is_active": True
    }
}


# =============================================================================
# AUTHENTICATION FUNCTIONS
# =============================================================================

def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password

    Args:
        username: Username
        password: Plain text password

    Returns:
        User object if authenticated, None otherwise
    """
    user_data = DEMO_USERS.get(username)

    if not user_data:
        return None

    if not user_data.get("is_active"):
        return None

    # Use constant-time comparison to prevent timing attacks
    if not verify_password(password, user_data.get("password_hash")):
        return None

    return User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        email=user_data["email"],
        roles=user_data["roles"],
        tenant_id=user_data.get("tenant_id"),
        is_active=user_data["is_active"]
    )


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        user: User object
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": user.user_id,
        "username": user.username,
        "roles": user.roles,
        "tenant_id": user.tenant_id,
        "exp": expire
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData object

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        roles: List[str] = payload.get("roles", [])
        tenant_id: Optional[str] = payload.get("tenant_id")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))

        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user information"
            )

        return TokenData(
            sub=user_id,
            username=username,
            roles=roles,
            tenant_id=tenant_id,
            exp=exp
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def verify_api_key(api_key: str) -> Optional[dict]:
    """
    Verify API key for service-to-service authentication

    Args:
        api_key: API key string

    Returns:
        API key data if valid, None otherwise
    """
    key_data = API_KEYS.get(api_key)

    if not key_data or not key_data.get("is_active"):
        return None

    return key_data


# =============================================================================
# DEPENDENCY INJECTION FUNCTIONS
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """
    Get current authenticated user from JWT token

    Dependency injection for protected endpoints
    """
    token = credentials.credentials
    token_data = verify_token(token)

    # In production, fetch user from database
    # For now, reconstruct from token
    user = User(
        user_id=token_data.sub,
        username=token_data.username,
        roles=token_data.roles,
        tenant_id=token_data.tenant_id,
        is_active=True
    )

    return user


async def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = Security(api_key_header)
) -> User:
    """
    Authenticate via JWT token OR API key

    Supports both user authentication and service-to-service
    """
    # Try API key first
    if api_key:
        key_data = verify_api_key(api_key)
        if key_data:
            return User(
                user_id=f"service_{key_data['name']}",
                username=key_data["name"],
                roles=key_data["roles"],
                tenant_id=key_data["tenant_id"],
                is_active=True
            )

    # Fall back to JWT token
    if credentials:
        return await get_current_user(credentials)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No valid credentials provided"
    )


def require_role(required_roles: List[str]):
    """
    Dependency factory for role-based access control

    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_role(["admin"]))])
    """
    async def role_checker(user: User = Depends(get_current_user)):
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user

    return role_checker


def require_tenant(
    user: User = Depends(get_current_user),
    tenant_id: Optional[str] = None
):
    """
    Ensure user has access to specified tenant

    For multi-tenant isolation
    """
    if tenant_id and user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    return user


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_api_key(prefix: str = "sk") -> str:
    """
    Generate a new API key

    Args:
        prefix: Key prefix (e.g., 'sk' for secret key)

    Returns:
        API key string
    """
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key

    Args:
        api_key: API key to revoke

    Returns:
        True if revoked, False if not found
    """
    if api_key in API_KEYS:
        API_KEYS[api_key]["is_active"] = False
        return True
    return False


# =============================================================================
# DEMO CREDENTIALS
# =============================================================================

def get_demo_credentials() -> dict:
    """
    Get demo credentials for testing

    Returns:
        Dict with demo user credentials
    """
    return {
        "demo_users": [
            {
                "username": "admin",
                "password": "admin123",
                "roles": ["admin", "developer", "user"],
                "description": "Full access to all endpoints"
            },
            {
                "username": "developer",
                "password": "dev123",
                "roles": ["developer", "user"],
                "description": "Access to MCP endpoints and user features"
            },
            {
                "username": "user",
                "password": "user123",
                "roles": ["user"],
                "description": "Basic access to learning materials"
            }
        ],
        "demo_api_keys": [
            {
                "api_key": "sk_test_abc123",
                "name": "Test Service Key",
                "roles": ["developer"]
            },
            {
                "api_key": "sk_prod_xyz789",
                "name": "Production Service Key",
                "roles": ["admin"]
            }
        ],
        "usage": {
            "jwt_login": "POST /api/auth/login with username and password",
            "api_key": "Include 'X-API-Key: sk_test_abc123' header in requests"
        }
    }
