# MoveInSync Database Schema

Core database schema and initialization scripts for the MoveInSync billing platform.

## Structure

### Schema Design (`01_schema_design/`)
- **01_tables.sql** - Main database tables and structure definitions
- **02_indexes.sql** - Database indexes for performance optimization

### Seed Data (`02_seed_data/`)
- **01_seed_users.sql** - Initial user data and roles
- **02_seed_contracts.sql** - Contract templates and configurations
- **03_renewal.sql** - Contract renewal and lifecycle management

## Setup

Run in order:
1. Execute `01_schema_design/01_tables.sql` to create database structure
2. Execute `01_schema_design/02_indexes.sql` to add performance indexes
3. Execute `02_seed_data/` scripts in order to initialize data

## Database Configuration

- **Host:** localhost (configurable via .env)
- **Port:** 5432 (default PostgreSQL)
- **Database:** moveinsync_db
- **User:** postgres (or configured via environment)
