import sys
from dataclasses import fields
from billing.schemas import ContractRuleConfig
from billing.strategies import StrategyFactory
from billing.repository import PostgresRepository

def create_config_safe(data: dict) -> ContractRuleConfig:
    """Helper to safely convert DB JSON to Dataclass."""
    valid_keys = {f.name for f in fields(ContractRuleConfig)}
    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
    return ContractRuleConfig(**filtered_data)

def run_billing_for_trip(trip_id: str):
    print(f"\n🚀 Starting Billing Engine for Trip: {trip_id}")
    print("------------------------------------------------")
    
    repo = PostgresRepository()

    try:
        # 1. Fetch Data
        print("📡 Connecting to PostgreSQL to fetch context...")
        trip_data, model_type, rules_dict = repo.fetch_trip_context(trip_id)
        
        print(f"✅ Data Found!")
        print(f"   - Distance: {trip_data.distance_km} km")
        print(f"   - Duration: {trip_data.duration_minutes:.2f} min")
        print(f"   - Model: {model_type.value}")
        print(f"   - Start Hour: {trip_data.start_hour}:00") # Shows the hour now

        # 2. Convert JSON to Dataclass safely
        rules_config = create_config_safe(rules_dict)

        # 3. Calculate
        strategy = StrategyFactory.get_strategy(model_type)
        result = strategy.calculate_cost(trip_data, rules_config)

        # 4. Print Bill
        print("\n💰 FINAL BILLING GENERATED")
        print("================================================")
        print(f"Trip ID      : {result.trip_id}")
        print(f"Base Cost    : ₹{result.base_cost:.2f}")
        print(f"Tax (18%)    : ₹{result.tax_amount:.2f}")
        print(f"TOTAL        : ₹{result.total_cost:.2f}")
        print("------------------------------------------------")
        print("Auditable Log:", result.breakdown)
        print("================================================")

    except ValueError as e:
        print(f"⚠️  Business Logic Error: {e}")
    except Exception as e:
        print(f"🔥 System Error: {e}")

if __name__ == "__main__":
    target_trip_id = sys.argv[1] if len(sys.argv) > 1 else "d0001"
    run_billing_for_trip(target_trip_id)