"""
Service layer that wraps repository calls and adds caching.

The service layer bridges the repository (raw DB access) and the API routes.
It provides higher-level business logic and caching using functools.lru_cache.
"""

from functools import lru_cache
from typing import Any, Dict
import sys
import os
import logging

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

# Now import from Phase 2 modules
from billing.repository import PostgresRepository  # type: ignore
from billing.strategies import StrategyFactory  # type: ignore
from billing.schemas import ContractRuleConfig  # type: ignore
from dataclasses import fields
import csv
import io


def create_config_safe(data: Dict[str, Any]) -> ContractRuleConfig:
    """Convert raw JSON/dict from DB into ContractRuleConfig dataclass safely."""
    valid_keys = {f.name for f in fields(ContractRuleConfig)}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return ContractRuleConfig(**filtered)


# Basic logger for quick debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BillingService:
    """
    Service layer for billing operations.
    
    - Handles repository calls
    - Applies caching for read operations
    - Wraps billing calculation logic
    """

    def __init__(self):
        self.repo = PostgresRepository()

    def calculate_trip_cost(self, trip_id: str, client_id: str, conn=None, override_is_carpool: bool = None) -> Dict[str, Any]:
        """
        Calculate cost for a trip.

        Steps:
        1. Fetch trip context from repository
        2. Convert rules config safely
        3. Get appropriate strategy
        4. Calculate cost
        5. Return formatted result
        """
        try:
            trip_data, model_type, rules_dict = self.repo.fetch_trip_context(trip_id, client_id, conn)

            # Debug logging to inspect why incentives may be missing
            try:
                logger.info("DEBUG: fetched trip.is_carpool=%s for trip_id=%s", getattr(trip_data, 'is_carpool', None), trip_id)
                logger.info("DEBUG: raw rules_dict = %s", rules_dict)
            except Exception:
                logger.exception("Failed to log debug info for trip or rules")

            # If caller supplied an override (e.g., from UI checkbox), apply it here so
            # the calculation reflects the requested carpool status even if DB isn't updated yet.
            if override_is_carpool is not None:
                trip_data.is_carpool = bool(override_is_carpool)

            # Log after applying override
            logger.info("DEBUG: effective trip.is_carpool=%s (override=%s)", trip_data.is_carpool, override_is_carpool)

            rules_config = create_config_safe(rules_dict)
            strategy = StrategyFactory.get_strategy(model_type)
            result = strategy.calculate_cost(trip_data, rules_config)

            return {
                "trip_id": result.trip_id,
                "billing_model": result.billing_model.value,
                "base_cost": result.base_cost,
                "tax_amount": result.tax_amount,
                "total_cost": result.total_cost,
                "breakdown": result.breakdown,
                "employee_incentive": getattr(result, 'employee_incentive', 0.0),
                "incentive_breakdown": getattr(result, 'incentive_breakdown', None),
            }
        except Exception as e:
            if conn:
                conn.rollback()
            raise e

    @staticmethod
    @lru_cache(maxsize=128)
    def get_cached_active_contract(client_id: str) -> tuple:
        """
        Fetch and cache active contract for a client.

        This uses lru_cache to avoid repeated DB hits for the same client.
        
        Parameters:
          - client_id (str): The client UUID
        
        Returns:
          - tuple: (contract_id, vendor_id, billing_model, rules_config_json_str)
            The tuple format is used because dicts aren't hashable and lru_cache requires hashable args/returns.
        
        Why caching here:
          - Contract data rarely changes for a given client
          - Repeated calls for /contracts endpoint will hit cache
          - 128 cache entries = up to 128 unique clients cached in memory
        """
        repo = PostgresRepository()
        contract_data = repo.fetch_active_contract(client_id)

        # Convert to tuple for hashability (lru_cache requirement)
        rules_config_str = str(contract_data["rules_config"])
        return (
            contract_data["contract_id"],
            contract_data["vendor_id"],
            contract_data["billing_model"],
            rules_config_str,
        )

    def get_active_contract(self, client_id: str, conn=None) -> Dict[str, Any]:
        """
        Get active contract for a client (uses caching if no conn provided).

        If a pooled connection is provided (from FastAPI), we skip caching
        since the request should be fresh. Otherwise, we use lru_cache.
        """
        if conn is not None:
            # Fresh request from API with pooled connection, don't cache
            contract_data = self.repo.fetch_active_contract(client_id, conn)
        else:
            # CLI or service-to-service call, use cache
            contract_id, vendor_id, billing_model, rules_str = self.get_cached_active_contract(
                client_id
            )
            contract_data = {
                "contract_id": contract_id,
                "vendor_id": vendor_id,
                "billing_model": billing_model,
                "rules_config": rules_str,
            }

        return contract_data

    def insert_new_trip(
        self,
        trip_id: str,
        client_id: str,
        vendor_id: str,
        distance_km: float,
        start_time: str,
        end_time: str,
        is_carpool: bool = False,
        conn=None,
    ) -> Dict[str, Any]:
        """
        Insert a new trip (simulating a completed ride).

        Parameters match the TripInput model + trip_id.
        Returns the inserted trip record.
        """
        result = self.repo.insert_trip(
            trip_id=trip_id,
            client_id=client_id,
            vendor_id=vendor_id,
            distance_km=distance_km,
            start_time=start_time,
            end_time=end_time,
            is_carpool=is_carpool,
            conn=conn,
        )
        return result

    def get_client_billing_data(self, client_id: str, conn=None) -> list[Dict[str, Any]]:
        """
        Fetch and calculate billing data for all trips of a client.
        Returns a list of dictionaries containing trip details and calculated costs.
        """
        trips = self.repo.fetch_client_trips(client_id, conn)
        results = []

        for trip in trips:
            trip_id = trip["trip_id"]
            try:
                # Reuse existing calculation; pass conn to reuse same DB connection
                calc = self.calculate_trip_cost(trip_id, client_id, conn)
                
                # Merge trip details with calculation results
                merged = {
                    "trip_id": calc.get("trip_id"),
                    "start_time": trip.get("start_time"),
                    "end_time": trip.get("end_time"),
                    "distance_km": trip.get("distance_km"),
                    "billing_model": calc.get("billing_model"),
                    "base_cost": calc.get("base_cost"),
                    "tax_amount": calc.get("tax_amount"),
                    "total_cost": calc.get("total_cost"),
                    "employee_incentive": calc.get("employee_incentive", 0.0),
                    "status": "SUCCESS",
                    "error": None
                }
                results.append(merged)
            except Exception as e:
                # If a trip fails to calculate, include an error row with details
                if conn:
                    conn.rollback()
                
                results.append({
                    "trip_id": trip_id,
                    "start_time": trip.get("start_time"),
                    "end_time": trip.get("end_time"),
                    "distance_km": trip.get("distance_km"),
                    "billing_model": "ERROR",
                    "base_cost": 0.0,
                    "tax_amount": 0.0,
                    "total_cost": 0.0,
                    "employee_incentive": 0.0,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return results

    def generate_client_report(self, client_id: str, conn=None) -> bytes:
        """
        Generate a CSV report of trips for the given client_id.

        The CSV columns: trip_id, start_time, end_time, distance_km, billing_model,
        base_cost, tax_amount, total_cost, employee_incentive

        This function calculates billing for each trip using existing calculation
        logic to ensure consistency.
        """
        billing_data = self.get_client_billing_data(client_id, conn)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "trip_id",
            "start_time",
            "end_time",
            "distance_km",
            "billing_model",
            "base_cost",
            "tax_amount",
            "total_cost",
            "employee_incentive",
        ])

        for row in billing_data:
            if row["status"] == "ERROR":
                writer.writerow([
                    row["trip_id"],
                    row["start_time"],
                    row["end_time"],
                    row["distance_km"],
                    "ERROR",
                    "",
                    "",
                    "",
                    row["error"],
                ])
            else:
                writer.writerow([
                    row["trip_id"],
                    row["start_time"],
                    row["end_time"],
                    row["distance_km"],
                    row["billing_model"],
                    row["base_cost"],
                    row["tax_amount"],
                    row["total_cost"],
                    row["employee_incentive"],
                ])

        csv_text = output.getvalue()
        output.close()

        return csv_text.encode("utf-8")
