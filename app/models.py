"""
Pydantic models for request/response validation
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Request Models

class DatasetSigma(BaseModel):
    """Uncertainty/sigma values for a dataset"""
    H0: Optional[float] = Field(None, description="H0 uncertainty")
    Omega_m: Optional[float] = Field(None, description="Omega_m uncertainty")
    Omega_Lambda: Optional[float] = Field(None, description="Omega_Lambda uncertainty")


class Dataset(BaseModel):
    """Cosmological dataset"""
    H0: float = Field(..., description="Hubble constant in km/s/Mpc", gt=0, lt=200)
    Omega_m: Optional[float] = Field(None, description="Matter density parameter", ge=0, le=1)
    Omega_Lambda: Optional[float] = Field(None, description="Dark energy density parameter", ge=0, le=1)
    sigma: Optional[DatasetSigma] = Field(None, description="Uncertainties")
    sigma_H0: Optional[float] = Field(None, description="H0 uncertainty (alternative format)")

    @validator('sigma_H0', pre=True, always=True)
    def set_sigma_h0(cls, v, values):
        """Allow either sigma.H0 or sigma_H0 format"""
        if v is None and 'sigma' in values and values['sigma']:
            return values['sigma'].H0
        return v


class MergeOptions(BaseModel):
    """Options for merge operation"""
    coordinate_system: str = Field("ICRS2016", description="Reference coordinate system")
    epoch: str = Field("J2000.0", description="Epoch for coordinates")
    validate_only: bool = Field(False, description="Only validate input without merging")


class MergeRequest(BaseModel):
    """Request to merge datasets"""
    datasets: Dict[str, Dataset] = Field(..., description="Named datasets to merge", min_items=2)
    options: Optional[MergeOptions] = Field(default_factory=MergeOptions)

    class Config:
        json_schema_extra = {
            "example": {
                "datasets": {
                    "planck": {
                        "H0": 67.4,
                        "Omega_m": 0.315,
                        "Omega_Lambda": 0.685,
                        "sigma": {
                            "H0": 0.5,
                            "Omega_m": 0.007
                        }
                    },
                    "shoes": {
                        "H0": 73.04,
                        "sigma_H0": 1.04
                    }
                },
                "options": {
                    "coordinate_system": "ICRS2016",
                    "epoch": "J2000.0"
                }
            }
        }


# Response Models

class MergeResult(BaseModel):
    """Result of merge operation"""
    merged_H0: float = Field(..., description="Merged Hubble constant")
    uncertainty: float = Field(..., description="Combined uncertainty")
    chi_squared: float = Field(..., description="Chi-squared statistic")
    p_value: float = Field(..., description="P-value for goodness of fit")
    method: str = Field("UHA", description="Method used for merging")
    coordinate_encoding: bool = Field(True, description="Whether coordinate encoding was applied")


class ResponseMetadata(BaseModel):
    """Metadata included in all responses"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class MergeResponse(BaseModel):
    """Successful merge response"""
    success: bool = Field(True, description="Operation success status")
    result: MergeResult = Field(..., description="Merge results")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class ErrorDetail(BaseModel):
    """Error details"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(False, description="Operation success status")
    error: ErrorDetail = Field(..., description="Error information")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class ValidationResponse(BaseModel):
    """Validation response"""
    valid: bool = Field(..., description="Whether input is valid")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: list[str] = Field(default_factory=list, description="Suggestions for improvement")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field("healthy", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# API Key Models

class APIKeyUsage(BaseModel):
    """API key usage statistics"""
    requests_today: int = Field(0, description="Requests made today")
    requests_month: int = Field(0, description="Requests made this month")
    limit_daily: int = Field(..., description="Daily request limit")
    limit_monthly: int = Field(..., description="Monthly request limit")


class RateLimit(BaseModel):
    """Rate limit configuration"""
    requests_per_minute: int = Field(60, description="Requests per minute limit")
    requests_per_hour: int = Field(1000, description="Requests per hour limit")


class APIKeyInfo(BaseModel):
    """API key information"""
    key_id: str = Field(..., description="Key identifier")
    owner: str = Field(..., description="Key owner name")
    institution: Optional[str] = Field(None, description="Owner institution")
    created: datetime = Field(..., description="Key creation date")
    expires: Optional[datetime] = Field(None, description="Key expiration date")
    usage: APIKeyUsage = Field(..., description="Usage statistics")
    rate_limit: RateLimit = Field(..., description="Rate limits")
