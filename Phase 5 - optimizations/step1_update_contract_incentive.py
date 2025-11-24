"""
Utility: safely add/update incentive_rules.carpool_bonus on a contract_versions row.
Run locally (requires psycopg2 and DB env vars set or pass via args)

Usage (PowerShell):
PS> python .\Phase\ 5 - optimizations\step1_update_contract_incentive.py --version-id b0000000-0000-0000-0000-000000000002 --bonus 50

This script prints the rules_config before and after the change.
"""
import os
import argparse
import json
import psycopg2
import psycopg2.extras

parser = argparse.ArgumentParser()
parser.add_argument('--version-id', '-v', required=True, help='contract_versions.id to update')
parser.add_argument('--bonus', '-b', type=float, default=50.0, help='carpool bonus amount')
parser.add_argument('--db-name', default=os.getenv('DB_NAME','moveinsync_db'))
parser.add_argument('--db-user', default=os.getenv('DB_USER','postgres'))
parser.add_argument('--db-password', default=os.getenv('DB_PASSWORD',''))
parser.add_argument('--db-host', default=os.getenv('DB_HOST','localhost'))
parser.add_argument('--db-port', default=os.getenv('DB_PORT','5432'))
args = parser.parse_args()

conn = None
try:
    conn = psycopg2.connect(dbname=args.db_name, user=args.db_user, password=args.db_password, host=args.db_host, port=args.db_port)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch current rules_config
    cur.execute('SELECT id, rules_config FROM contract_versions WHERE id = %s', (args.version_id,))
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"No contract_versions row found for id={args.version_id}")

    print('\n--- BEFORE ---')
    print(json.dumps(row['rules_config'], indent=2, default=str))

    # Build JSON to set: ensure incentive_rules exists and set carpool_bonus
    # We'll use jsonb_set to set the incentive_rules value atomically
    bonus_obj = json.dumps({"carpool_bonus": args.bonus})

    sql = """
    UPDATE contract_versions
    SET rules_config = jsonb_set(
        COALESCE(rules_config, '{}'::jsonb),
        '{incentive_rules}',
        %s::jsonb,
        true
    )
    WHERE id = %s
    RETURNING rules_config;
    """

    cur.execute(sql, (bonus_obj, args.version_id))
    updated = cur.fetchone()
    conn.commit()

    print('\n--- AFTER ---')
    print(json.dumps(updated['rules_config'], indent=2, default=str))

    print('\n✅ Updated incentive_rules.carpool_bonus successfully')

except Exception as e:
    print('❌ Error:', e)
    if conn:
        conn.rollback()
finally:
    if conn:
        conn.close()
