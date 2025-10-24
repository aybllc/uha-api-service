"""
API Key authentication and authorization
"""
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any

from .config import settings
from .database import db

# API Key header
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header)
) -> Dict[str, Any]:
    """
    Validate API key and return key information

    Raises:
        HTTPException: If key is invalid or rate limited
    """
    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Authenticate key
    key_info = db.authenticate_key(api_key)

    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check rate limits
    allowed, reason = db.check_rate_limit(key_info['key_id'], key_info)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {reason}",
        )

    # Store key info in request state for logging
    request.state.key_info = key_info

    return key_info


# Optional: Function to create admin API key programmatically
def create_admin_key(
    owner_name: str = "Administrator",
    owner_email: str = "admin@aybllc.org"
) -> tuple[str, str]:
    """
    Create an admin API key with high limits

    Returns: (key_id, api_key)
    """
    return db.create_api_key(
        owner_name=owner_name,
        owner_email=owner_email,
        institution="All Your Baseline LLC",
        daily_limit=100000,
        monthly_limit=1000000,
        expires_days=None,  # Never expires
        notes="Administrator key"
    )


def create_researcher_key(
    owner_name: str,
    owner_email: str,
    institution: Optional[str] = None,
    daily_limit: int = 1000,
    monthly_limit: int = 50000,
    expires_days: int = 365
) -> tuple[str, str]:
    """
    Create a researcher API key

    Returns: (key_id, api_key)
    """
    return db.create_api_key(
        owner_name=owner_name,
        owner_email=owner_email,
        institution=institution,
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
        expires_days=expires_days,
        notes=f"Researcher key for {owner_name}"
    )
