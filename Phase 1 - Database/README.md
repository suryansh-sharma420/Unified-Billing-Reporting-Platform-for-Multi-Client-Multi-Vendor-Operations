Phase 1 — Database

Overview

This folder contains the database schema and seed data for the MoveInSync project.

Contents

- MoveInSync_DB/01_schema_design/01_tables.sql — Primary table definitions
- MoveInSync_DB/01_schema_design/02_indexes.sql — Indexes and constraints
- MoveInSync_DB/02_seed_data/01_seed_users.sql — Sample users/clients/vendors
- MoveInSync_DB/02_seed_data/02_seed_contracts.sql — Sample contracts and versions
- MoveInSync_DB/02_seed_data/03_renewal.sql — Optional renewal/maintenance scripts

Quick Setup

1. Create the database (Postgres):

   psql -U <user> -c "CREATE DATABASE moveinsync_db;"

2. Run schema SQL files (in order):

   psql -U <user> -d moveinsync_db -f "MoveInSync_DB/01_schema_design/01_tables.sql"
   psql -U <user> -d moveinsync_db -f "MoveInSync_DB/01_schema_design/02_indexes.sql"

3. Load seed data:

   psql -U <user> -d moveinsync_db -f "MoveInSync_DB/02_seed_data/01_seed_users.sql"
   psql -U <user> -d moveinsync_db -f "MoveInSync_DB/02_seed_data/02_seed_contracts.sql"
   psql -U <user> -d moveinsync_db -f "MoveInSync_DB/02_seed_data/03_renewal.sql"

Notes

- Adjust `psql` user and host options as needed for your environment.
- These SQL files are safe to include in the public repository; they do not contain secrets.
