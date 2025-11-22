-- =============================================
-- MASTER SCRIPT: MoveInSync Architecture
-- =============================================

-- 1. ENABLE ADVANCED FEATURES
-- We need this to generate those random UUIDs (a0eebc...)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- 2. CREATE TABLES (The Skeleton)
-- =============================================

-- A. TENANCY (Clients & Vendors)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    billing_address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    service_regions JSONB DEFAULT '[]', -- Stores ["Bangalore", "NCR"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- B. USERS (RBAC - The Linker)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- In real life, this is Bcrypt
    role VARCHAR(50) NOT NULL, -- 'SUPER_ADMIN', 'CLIENT_ADMIN', 'VENDOR_ADMIN'
    
    -- The Magic Links (Nullable)
    client_id UUID REFERENCES clients(id),
    vendor_id UUID REFERENCES vendors(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- C. OPERATIONS (The Resources)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    name VARCHAR(100) NOT NULL,
    employee_code VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- D. BILLING ENGINE (The Brain)
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    name VARCHAR(100), -- e.g., "Google-Uber 2025"
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, ACTIVE
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE contract_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id),
    version_number INT NOT NULL,
    
    -- The Flexible Math Column
    billing_model VARCHAR(50) NOT NULL, -- 'PER_TRIP', 'FIXED'
    rules_config JSONB NOT NULL,        -- The logic lives here!
    
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ, -- Null means "Forever"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- E. TRANSACTIONS (The Events)
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    vendor_id UUID REFERENCES vendors(id),
    employee_id UUID REFERENCES employees(id),
    
    distance_km DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ
);

CREATE TABLE trip_cost_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id),
    contract_version_id UUID NOT NULL REFERENCES contract_versions(id),
    
    base_cost DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    total_cost DECIMAL(10,2) NOT NULL,
    
    -- The Audit Trail
    calculation_log JSONB NOT NULL, -- Snapshot of the math used
    created_at TIMESTAMPTZ DEFAULT NOW()
);