"""
UHA API Service - Main Application

Cosmological dataset aggregation and statistical analysis.
Organization: All Your Baseline LLC
"""
import time
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .models import (
    MergeRequest, MergeResponse, ErrorResponse, ValidationResponse,
    HealthResponse, APIKeyInfo, ResponseMetadata, ErrorDetail,
    APIKeyUsage, RateLimit
)
from .auth import get_api_key
from .database import db
from .merge import perform_merge, validate_datasets


# Ensure required directories exist
settings.ensure_directories()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print(f"🚀 Starting {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"📁 Database: {settings.DATABASE_PATH}")
    print(f"📊 Rate limits: {settings.RATE_LIMIT_PER_MINUTE}/min, {settings.RATE_LIMIT_PER_HOUR}/hour")

    # Validate configuration
    settings.validate()

    yield

    # Shutdown
    print("👋 Shutting down UHA API Service")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware if configured
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses"""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Start timer
    start_time = time.time()

    # Process request
    try:
        response = await call_next(request)
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log to database if API key is present
        key_info = getattr(request.state, 'key_info', None)
        db.log_request(
            key_id=key_info['key_id'] if key_info else None,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            processing_time_ms=processing_time_ms,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log error
        key_info = getattr(request.state, 'key_info', None)
        db.log_request(
            key_id=key_info['key_id'] if key_info else None,
            endpoint=request.url.path,
            method=request.method,
            status_code=500,
            processing_time_ms=processing_time_ms,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e),
        )

        # Return error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="An internal error occurred",
                    details={"error": str(e)} if settings.DEBUG else None
                ),
                metadata=ResponseMetadata(
                    request_id=request_id,
                    timestamp=datetime.utcnow(),
                    processing_time_ms=processing_time_ms
                )
            ).dict()
        )


# Routes

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs or show info"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "organization": settings.ORGANIZATION,
        "docs": "/docs" if settings.DEBUG else "Contact support@aybllc.org",
    }


@app.get("/v1/health", response_model=HealthResponse, tags=["System"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Health check endpoint

    Returns service status and version information.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow()
    )


@app.post("/v1/merge", response_model=MergeResponse, tags=["Merge"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def merge_datasets(
    request: Request,
    merge_request: MergeRequest,
    key_info: dict = Depends(get_api_key)
):
    """
    Merge cosmological datasets using UHA

    Requires valid API key in X-API-Key header.

    **Example:**
    ```json
    {
      "datasets": {
        "planck": {
          "H0": 67.4,
          "Omega_m": 0.315,
          "Omega_Lambda": 0.685,
          "sigma": {"H0": 0.5, "Omega_m": 0.007}
        },
        "shoes": {
          "H0": 73.04,
          "sigma_H0": 1.04
        }
      }
    }
    ```
    """
    start_time = time.time()

    # Validate input
    valid, warnings, suggestions = validate_datasets(merge_request)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {warnings[0]}"
        )

    # Perform merge
    result = perform_merge(merge_request)

    processing_time_ms = int((time.time() - start_time) * 1000)

    return MergeResponse(
        success=True,
        result=result,
        metadata=ResponseMetadata(
            request_id=request.state.request_id,
            timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms
        )
    )


@app.post("/v1/validate", response_model=ValidationResponse, tags=["Merge"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def validate_input(
    request: Request,
    merge_request: MergeRequest,
    key_info: dict = Depends(get_api_key)
):
    """
    Validate input datasets without performing merge

    Useful for checking if your data format is correct before submitting
    a merge request.
    """
    valid, warnings, suggestions = validate_datasets(merge_request)

    return ValidationResponse(
        valid=valid,
        warnings=warnings,
        suggestions=suggestions
    )


@app.get("/v1/key/info", response_model=APIKeyInfo, tags=["API Keys"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_key_info(
    request: Request,
    key_info: dict = Depends(get_api_key)
):
    """
    Get information about your API key

    Returns usage statistics, rate limits, and expiration info.
    """
    # Get usage stats
    usage_stats = db.get_usage_stats(key_info['key_id'])

    return APIKeyInfo(
        key_id=key_info['key_id'],
        owner=key_info['owner_name'],
        institution=key_info['institution'],
        created=key_info['created_at'],
        expires=key_info['expires_at'],
        usage=APIKeyUsage(
            requests_today=usage_stats['requests_today'],
            requests_month=usage_stats['requests_month'],
            limit_daily=key_info['daily_limit'],
            limit_monthly=key_info['monthly_limit']
        ),
        rate_limit=RateLimit(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            requests_per_hour=settings.RATE_LIMIT_PER_HOUR
        )
    )


# Error handlers

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            success=False,
            error=ErrorDetail(
                code="NOT_FOUND",
                message=f"Endpoint not found: {request.url.path}",
            ),
            metadata=ResponseMetadata(
                request_id=getattr(request.state, 'request_id', 'unknown'),
                timestamp=datetime.utcnow()
            )
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
