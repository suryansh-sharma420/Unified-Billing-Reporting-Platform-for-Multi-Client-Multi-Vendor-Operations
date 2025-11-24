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

        # Track employee incentive separately
        employee_incentive = 0.0
        incentive_breakdown = {}

        # Night Shift Logic
        is_night_shift = trip.start_hour >= 20 or trip.start_hour < 6
        if is_night_shift:
            surcharge = rules.night_shift_surcharge or 0.0
            cost += surcharge
            breakdown['night_shift_surcharge'] = surcharge
            # Note: night shift employee bonuses can be added to incentive rules if desired
        else:
            breakdown['night_shift_surcharge'] = 0.0
            breakdown['note'] = "Not a night shift trip"

        # Distance Cost
        km_rate = rules.per_km_rate_after_limit or 0.0
        km_cost = trip.distance_km * km_rate
        cost += km_cost
        
        breakdown['distance_cost'] = km_cost
        breakdown['rate_per_km'] = km_rate

        # Carpool incentive: if trip marked as carpool, get bonus from nested incentive_rules
        if getattr(trip, 'is_carpool', False):
            inv = rules.incentive_rules or {}
            carpool_bonus = float(inv.get('carpool_bonus', 0.0) or 0.0)
            if carpool_bonus:
                # Business decision: Incentive is added to the final total (client pays it)
                employee_incentive += carpool_bonus
                incentive_breakdown['carpool_bonus'] = carpool_bonus
                breakdown['carpool_bonus'] = carpool_bonus
        else:
            breakdown['carpool_bonus'] = 0.0

        tax = self.apply_tax(cost)

        # total_cost: base + tax + incentives (incentives not taxed in this implementation)
        total = round(cost + tax + employee_incentive, 2)

        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.HYBRID,
            base_cost=round(cost, 2),
            tax_amount=tax,
            total_cost=total,
            breakdown=breakdown,
            employee_incentive=round(employee_incentive, 2),
            incentive_breakdown=incentive_breakdown or None
        )

# --- 3. Concrete Strategy: PER TRIP (The Uber Model) ---
class PerTripStrategy(BillingStrategy):
    """
    Simple Logic: (Distance * Rate) + Base Fare
    """
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        rate = rules.cost_per_km or 0.0
        base = rules.base_fare or 0.0
        
        dist_cost = trip.distance_km * rate
        subtotal = base + dist_cost

        # Employee incentives (carpool)
        employee_incentive = 0.0
        incentive_breakdown = {}
        inv = rules.incentive_rules or {}
        if getattr(trip, 'is_carpool', False):
            carpool_bonus = float(inv.get('carpool_bonus', 0.0) or 0.0)
            if carpool_bonus:
                employee_incentive += carpool_bonus
                incentive_breakdown['carpool_bonus'] = carpool_bonus

        tax = self.apply_tax(subtotal)
        total = round(subtotal + tax + employee_incentive, 2)

        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.PER_TRIP,
            base_cost=round(subtotal, 2),
            tax_amount=tax,
            total_cost=total,
            breakdown={
                "base_fare": base,
                "distance_cost": dist_cost,
                "rate_per_km": rate,
                "carpool_bonus": inv.get('carpool_bonus', 0.0) if getattr(trip, 'is_carpool', False) else 0.0
            },
            employee_incentive=round(employee_incentive, 2),
            incentive_breakdown=incentive_breakdown or None
        )

# --- 4. Concrete Strategy: FIXED PACKAGE (The Retainer Model) ---
class FixedPackageStrategy(BillingStrategy):
    """
    Logic: The trip is free (Cost = 0) because the client paid a monthly fee.
    We just record the usage.
    """
    def calculate_cost(self, trip: TripData, rules: ContractRuleConfig) -> CalculationResult:
        cost = 0.0
        tax = 0.0
        employee_incentive = 0.0
        incentive_breakdown = {}
        inv = rules.incentive_rules or {}
        if getattr(trip, 'is_carpool', False):
            carpool_bonus = float(inv.get('carpool_bonus', 0.0) or 0.0)
            if carpool_bonus:
                employee_incentive += carpool_bonus
                incentive_breakdown['carpool_bonus'] = carpool_bonus

        # For fixed-package, client paid monthly; we still track incentives separately
        return CalculationResult(
            trip_id=trip.trip_id,
            billing_model=BillingModelType.FIXED_PACKAGE,
            base_cost=cost,
            tax_amount=tax,
            total_cost=round(employee_incentive, 2),
            breakdown={
                "note": "Covered by Monthly Fixed Fee",
                "monthly_fee_reference": rules.package_price,
                "km_consumed": trip.distance_km,
                "carpool_bonus": inv.get('carpool_bonus', 0.0) if getattr(trip, 'is_carpool', False) else 0.0
            },
            employee_incentive=round(employee_incentive, 2),
            incentive_breakdown=incentive_breakdown or None
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
            print(f"⚠️ Warning: Unknown strategy {model_type}, defaulting to HYBRID.")
            return HybridStrategy()
        return strategy