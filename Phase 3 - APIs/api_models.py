from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, EmailStr


# -----------------------------
# User & Auth models
# -----------------------------
RoleType = Literal["SUPER_ADMIN", "CLIENT_ADMIN", "VENDOR_ADMIN", "VIEWER"]

class UserCreate(BaseModel):
    email: str
    password: str
    role: RoleType
    client_id: Optional[str] = None
    vendor_id: Optional[str] = None

class UserOut(BaseModel):
    id: str
    email: str
    role: RoleType
    client_id: Optional[str]
    vendor_id: Optional[str]

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleType
    client_id: Optional[str] = None
    vendor_id: Optional[str] = None


# -----------------------------
# Trip input
# -----------------------------
class TripInput(BaseModel):
    """Pydantic model for POST /trips input payload."""
    distance_km: float = Field(..., ge=0, description="Distance travelled in kilometres")
    start_time: datetime = Field(..., description="Trip start time (ISO 8601)")
    end_time: Optional[datetime] = Field(None, description="Trip end time (ISO 8601)")
    vendor_id: str = Field(..., description="Vendor / provider id associated with trip")
    vehicle_type: Optional[str] = Field("Standard", description="Vehicle type, e.g. Sedan, Mini")
    is_carpool: bool = Field(False, description="Whether this trip was a carpool/shared ride")