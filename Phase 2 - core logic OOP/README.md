Phase 2 — Core Billing Logic (OOP)

Overview

This folder implements the core billing engine using an object-oriented Strategy pattern.
It is intentionally framework-agnostic so the same logic can be invoked from CLI or a web service.

Contents

- `billing/schemas.py` — Dataclasses and enums for TripData, ContractRuleConfig, CalculationResult
- `billing/strategies.py` — Strategy implementations: `HybridStrategy`, `PerTripStrategy`, `FixedPackageStrategy` and `StrategyFactory`
- `billing/repository.py` — Raw psycopg2 access to fetch trip context and contract versions
- `main.py` — CLI runner to calculate billing for a trip (example usage)
- `diagnosis.py` — Helper script to inspect DB state for a trip (debugging)

Quick Usage

- Run the CLI billing script for a trip_id (uses .env for DB credentials):

  python main.py <trip_id>

- Run diagnostics to check data and contract coverage:

  python diagnosis.py <trip_id>

Design Notes

- The code uses `psycopg2` and raw SQL for clarity and low-level control.
- Repository methods accept an optional `conn` parameter to support both CLI (local connection) and API (pooled connection) usage.
- Business logic is separated from data access to enable easy re-use inside a web API or tests.

Public/Private

- These files are safe to publish to GitHub. Do not include local `.env` files or database passwords.
