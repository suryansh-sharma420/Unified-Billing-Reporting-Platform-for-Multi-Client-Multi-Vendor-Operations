from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TripInput(BaseModel):
    """Pydantic model for POST /trips input payload.

    Fields:
      - distance_km: Float distance in kilometers (required)
      - start_time: ISO datetime string when trip started (required)
      - end_time: ISO datetime string when trip ended (optional)
      - vendor_id: Vendor identifier (required)
      - vehicle_type: Optional vehicle type string
    """

    distance_km: float = Field(..., ge=0, description="Distance travelled in kilometres")
    start_time: datetime = Field(..., description="Trip start time (ISO 8601)")
    end_time: Optional[datetime] = Field(None, description="Trip end time (ISO 8601)")
    vendor_id: str = Field(..., description="Vendor / provider id associated with trip")
    vehicle_type: Optional[str] = Field("Standard", description="Vehicle type, e.g. Sedan, Mini")
