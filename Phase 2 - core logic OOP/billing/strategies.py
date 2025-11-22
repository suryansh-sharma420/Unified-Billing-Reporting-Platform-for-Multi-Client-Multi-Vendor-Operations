from abc import ABC, abstractmethod
from .schemas import TripData, ContractRuleConfig, CalculationResult, BillingModelType

# --- 1. The Interface (Abstraction) ---
class BillingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        pass

    def apply_tax(self, base_cost: float, tax_rate: float = 0.18) -> float:
        return round(base_cost * tax_rate, 2)

# --- 2. Concrete Strategy: HYBRID (What you already had) ---
class HybridStrategy(BillingStrategy):
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        cost = 0.0
        breakdown = {}

        # Night Shift Logic
        is_night_shift = trip.start_hour >= 20 or trip.start_hour < 6
        if is_night_shift:
            surcharge = rules.night_shift_surcharge or 0.0
            cost += surcharge
            breakdown['night_shift_surcharge'] = surcharge
        else:
            breakdown['night_shift_surcharge'] = 0.0
            breakdown['note'] = "Not a night shift trip"

        # Distance Cost
        km_rate = rules.per_km_rate_after_limit or 0.0
        km_cost = trip.distance_km * km_rate
        cost += km_cost
        
        breakdown['distance_cost'] = km_cost
        breakdown['rate_per_km'] = km_rate

        tax = self.apply_tax(cost)

        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.HYBRID,
            base_cost=round(cost, 2),
            tax_amount=tax,
            total_cost=round(cost + tax, 2),
            breakdown=breakdown
        )

# --- 3. Concrete Strategy: PER TRIP (The Uber Model) ---
class PerTripStrategy(BillingStrategy):
    """
    Simple Logic: (Distance * Rate) + Base Fare
    """
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        # Use generic fields from schemas.py
        rate = rules.cost_per_km or 0.0
        base = rules.base_fare or 0.0
        
        dist_cost = trip.distance_km * rate
        subtotal = base + dist_cost

        tax = self.apply_tax(subtotal)

        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.PER_TRIP,
            base_cost=round(subtotal, 2),
            tax_amount=tax,
            total_cost=round(subtotal + tax, 2),
            breakdown={
                "base_fare": base,
                "distance_cost": dist_cost,
                "rate_per_km": rate
            }
        )

# --- 4. Concrete Strategy: FIXED PACKAGE (The Retainer Model) ---
class FixedPackageStrategy(BillingStrategy):
    """
    Logic: The trip is free (Cost = 0) because the client paid a monthly fee.
    We just record the usage.
    """
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        # Cost is effectively 0 for the invoice
        cost = 0.0
        tax = 0.0
        
        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.FIXED_PACKAGE,
            base_cost=cost,
            tax_amount=tax,
            total_cost=0.0,
            breakdown={
                "note": "Covered by Monthly Fixed Fee",
                "monthly_fee_reference": rules.package_price, # Reference only
                "km_consumed": trip.distance_km
            }
        )

# --- 5. The Factory (The Switch) ---
class StrategyFactory:
    _strategies = {
        BillingModelType.HYBRID: HybridStrategy(),
        BillingModelType.PER_TRIP: PerTripStrategy(),
        BillingModelType.FIXED_PACKAGE: FixedPackageStrategy()
    }

    @classmethod
    def get_strategy(cls, model_type: BillingModelType) -> BillingStrategy:
        strategy = cls._strategies.get(model_type)
        if not strategy:
            # Default to Hybrid if something goes wrong
            print(f"⚠️ Warning: Unknown strategy {model_type}, defaulting to HYBRID.")
            return HybridStrategy()
        return strategy