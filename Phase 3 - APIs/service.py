"""
Service layer that wraps repository calls and adds caching.

The service layer bridges the repository (raw DB access) and the API routes.
It provides higher-level business logic and caching using functools.lru_cache.
"""

from functools import lru_cache
from typing import Any, Dict
import sys
import os

# Add Phase 2 to sys.path dynamically
phase2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 2 - core logic OOP'))
if phase2_path not in sys.path:
    sys.path.insert(0, phase2_path)

# Now import from Phase 2 modules
from billing.repository import PostgresRepository  # type: ignore
from billing.strategies import StrategyFactory  # type: ignore
from billing.schemas import ContractRuleConfig  # type: ignore
from dataclasses import fields


def create_config_safe(data: Dict[str, Any]) -> ContractRuleConfig:
    """Convert raw JSON/dict from DB into ContractRuleConfig dataclass safely."""
    valid_keys = {f.name for f in fields(ContractRuleConfig)}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return ContractRuleConfig(**filtered)


class BillingService:
    """
    Service layer for billing operations.
    
    - Handles repository calls
    - Applies caching for read operations
    - Wraps billing calculation logic
    """

    def __init__(self):
        self.repo = PostgresRepository()

    def calculate_trip_cost(self, trip_id: str, client_id: str, conn=None) -> Dict[str, Any]:
        """
        Calculate cost for a trip.

        Steps:
        1. Fetch trip context from repository
        2. Convert rules config safely
        3. Get appropriate strategy
        4. Calculate cost
        5. Return formatted result
        """
        trip_data, model_type, rules_dict = self.repo.fetch_trip_context(trip_id, client_id, conn)

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
        }

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
            conn=conn,
        )
        return result
