"""
Authentication Routes for MCP API
==================================

Provides login, token management, and user info endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta

from auth import (
    LoginRequest, TokenResponse, User,
    authenticate_user, create_access_token,
    get_current_user, get_demo_credentials,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(login_req: LoginRequest):
    """
    Login with username and password

    Returns JWT access token for subsequent requests
    """
    user = authenticate_user(login_req.username, login_req.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user, expires_delta=access_token_expires)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires valid JWT token
    """
    return current_user


@router.get("/demo-credentials")
async def get_demo_creds():
    """
    Get demo credentials for testing

    Returns demo users and API keys
    """
    return get_demo_credentials()


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT token

    Returns new token with extended expiration
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(current_user, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
