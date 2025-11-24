-- =============================================
-- SCENARIO: CONTRACT RENEWAL (FIXED)
-- We are expiring Version 1 and creating Version 2
-- =============================================

-- 1. EXPIRE VERSION 1
-- Update the old contract to end "NOW"
UPDATE contract_versions 
SET valid_until = NOW()
WHERE id = 'b0000000-0000-0000-0000-000000000001';

-- 2. CREATE VERSION 2 (New Higher Rates)
INSERT INTO contract_versions (id, contract_id, version_number, billing_model, valid_from, rules_config)
VALUES (
    'b0000000-0000-0000-0000-000000000002', -- New ID ending in 2
    'a0000000-0000-0000-0000-000000000001', -- Same Google-Uber Contract
    2,                                      -- Version 2
    'HYBRID',
    NOW(),                                  -- Valid from right now
    '{
        "currency": "INR",
        "base_monthly_fee": 60000.00,
        "free_km_included": 1000,
        "per_km_rate_after_limit": 25.00,
        "night_shift_surcharge": 300.00,
        "incentive_rules": { "carpool_bonus": 50.00 }
    }'::jsonb
);