from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

# --- Enums ---
class BillingModelType(str, Enum):
    PER_TRIP = "PER_TRIP"
    FIXED_PACKAGE = "FIXED_PACKAGE"
    HYBRID = "HYBRID"

# --- Data Models ---

@dataclass
class TripData:
    """
    Represents trip data fetched from the DB.
    """
    trip_id: str
    distance_km: float
    duration_minutes: float
    start_hour: int  # <--- THIS IS THE CRITICAL FIX
    vehicle_type: str = "Standard"
    is_carpool: bool = False

@dataclass
class ContractRuleConfig:
    """
    Matches the keys in your 'contract_versions' JSONB column.
    """
    currency: str = "USD"
    
    # HYBRID Model Fields (Your specific keys)
    base_monthly_fee: Optional[float] = 0.0
    free_km_included: Optional[float] = 0.0
    night_shift_surcharge: Optional[float] = 0.0
    per_km_rate_after_limit: Optional[float] = 0.0
    
    # Compatibility Fields
    base_fare: Optional[float] = 0.0
    cost_per_km: Optional[float] = 0.0
    cost_per_minute: Optional[float] = 0.0
    min_fare: Optional[float] = 0.0
    package_price: Optional[float] = 0.0
    included_km: Optional[float] = 0.0
    overage_per_km: Optional[float] = 0.0

    # Incentive rules (nested dictionary) e.g. {"carpool_bonus": 50.0}
    incentive_rules: Optional[Dict[str, float]] = None

@dataclass
class CalculationResult:
    trip_id: str
    billing_model: BillingModelType
    base_cost: float
    tax_amount: float
    total_cost: float
    breakdown: Dict[str, Any]
    # Amount paid to employee as incentive (client pays this)
    employee_incentive: float = 0.0
    # Optional detailed incentive breakdown
    incentive_breakdown: Optional[Dict[str, float]] = None