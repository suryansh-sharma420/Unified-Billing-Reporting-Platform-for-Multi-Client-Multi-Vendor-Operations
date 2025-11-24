-- THIS is where the JSON code will go
-- FILENAME: 02_seed_contracts.sql
/*
Why this is "Audit Ready"
When a trip happens, your Python/Backend code will:

1. Fetch the contract_version active at that moment.
2. Read the rules_config JSON.
3. Calculate the cost (e.g., 10km * 15.00 + 100.00 = 250.00).
4. Save the result AND a snapshot of the math into trip_cost_ledger.

This way, if you change the per_km_rate to 16.00 next year, the old trip records still show they were calculated using the old 15.00 rate.
*/

-- 1. Insert a Contract for "Google" (Pay Per Trip Model)
INSERT INTO contract_versions 
(id, contract_id, version_number, billing_model, rules_config, valid_from)
VALUES 
(
    gen_random_uuid(), -- Generates a unique ID automatically
    'uuid-of-google-contract-row', -- You would replace this with a real ID later
    1, 
    'PER_TRIP', 
    '{
        "currency": "INR",
        "base_fare": 100.00,
        "per_km_rate": 15.00,
        "min_trip_charge": 150.00,
        "tax_percentage": 18.0,
        "incentive_rules": { "carpool_bonus": 50.00 }
    }'::jsonb, -- <--- This tells Postgres "Treat this text as JSON data"
    NOW()
);

-- 2. Insert a Contract for "Infosys" (Fixed Monthly Model)
INSERT INTO contract_versions 
(id, contract_id, version_number, billing_model, rules_config, valid_from)
VALUES 
(
    gen_random_uuid(),
    'uuid-of-infosys-contract-row', 
    1, 
    'FIXED_MONTHLY', 
    '{
        "currency": "INR",
        "monthly_fee": 500000.00,
        "max_vehicles": 50,
        "sla_penalty_amount": 5000.00,
        "incentive_rules": { "carpool_bonus": 0.0 }
    }'::jsonb, 
    NOW()
);