-- =============================================
-- SEED DATA SCRIPT (FIXED HEX CODES)
-- Filename: 02_seed_contracts.sql
-- =============================================

-- 1. Create CLIENT: "Google India" (ID starts with 'c' - Valid)
INSERT INTO clients (id, name, billing_address)
VALUES (
    'c0000000-0000-0000-0000-000000000001', 
    'Google India Pvt Ltd', 
    'No. 3, RMZ Infinity, Bangalore'
);

-- 2. Create VENDOR: "Uber Enterprise" 
-- CHANGED 'v' -> 'f' (valid hex)
INSERT INTO vendors (id, name, tax_id, service_regions)
VALUES (
    'f0000000-0000-0000-0000-000000000001',
    'Uber Enterprise', 
    'GSTIN-UBER-999', 
    '["Bangalore", "Hyderabad", "Delhi"]'::jsonb
);

-- 3. Create USERS
-- A. Super Admin
INSERT INTO users (email, password_hash, role, client_id, vendor_id)
VALUES ('admin@moveinsync.com', 'hashed_secret', 'SUPER_ADMIN', NULL, NULL);

-- B. Google Admin
INSERT INTO users (email, password_hash, role, client_id, vendor_id)
VALUES (
    'alice@google.com', 
    'hashed_secret', 
    'CLIENT_ADMIN', 
    'c0000000-0000-0000-0000-000000000001', -- Links to Google
    NULL
);

-- 4. Create CONTRACT (Google hires Uber)
INSERT INTO contracts (id, client_id, vendor_id, name, status)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001', -- Google
    'f0000000-0000-0000-0000-000000000001', -- Uber (Fixed ID)
    'Google-Uber 2025 Agreement',
    'ACTIVE'
);

-- 5. Create CONTRACT RULES (Version 1)
-- CHANGED 'r' -> 'b' (valid hex)
INSERT INTO contract_versions (id, contract_id, version_number, billing_model, valid_from, rules_config)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001', -- Contract ID
    1,
    'HYBRID',
    NOW(),
    '{
        "currency": "INR",
        "base_monthly_fee": 50000.00,
        "free_km_included": 1000,
        "per_km_rate_after_limit": 18.50,
        "night_shift_surcharge": 200.00
    }'::jsonb
);

-- 6. Create EMPLOYEE
INSERT INTO employees (id, client_id, name, employee_code)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001', 
    'Rohan Gupta',
    'GOOG-404'
);

-- 7. Create TRIP
-- CHANGED 't' -> 'd' (valid hex)
INSERT INTO trips (id, client_id, vendor_id, employee_id, distance_km, status, start_time, end_time)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001', -- Google
    'f0000000-0000-0000-0000-000000000001', -- Uber (Fixed ID)
    'e0000000-0000-0000-0000-000000000001', -- Rohan
    25.5, 
    'COMPLETED',
    NOW() - INTERVAL '2 hours', 
    NOW() - INTERVAL '1 hour'
);


SELECT * FROM clients;