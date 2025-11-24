import psycopg2
import psycopg2.extras
import os
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Tuple, Dict, Any, Optional
from dotenv import load_dotenv
from .schemas import TripData, BillingModelType

# Load environment variables from .env file
load_dotenv()

class PostgresRepository:
    def __init__(self):
        self.db_config = {
            "dbname": os.getenv("DB_NAME", "moveinsync_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }

    def get_db_connection(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    def fetch_trip_context(
        self,
        trip_id: str,
        client_id: str,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> Tuple[TripData, BillingModelType, Dict[str, Any]]:
        """
        Fetch trip context and matching contract version for a given trip and client.
        """
        sql = """
        SELECT 
            t.id as trip_id,
            t.distance_km,
            t.start_time,
            t.end_time,
            t.is_carpool,
            cv.billing_model,
            cv.rules_config
        FROM trips t
        JOIN contracts c ON t.client_id = c.client_id AND t.vendor_id = c.vendor_id
        JOIN contract_versions cv ON c.id = cv.contract_id
        WHERE t.id = %s
          AND t.client_id = %s
          AND t.start_time >= cv.valid_from
          AND (cv.valid_until IS NULL OR t.start_time <= cv.valid_until)
        LIMIT 1;
        """

        local_conn = False
        if conn is None:
            conn = self.get_db_connection()
            local_conn = True

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            cursor.execute(sql, (trip_id, client_id))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No active contract found for Trip ID: {trip_id}")

            start = row['start_time']
            end = row['end_time']
            is_carpool = bool(row.get('is_carpool'))

            # Calculate duration safely even if start or end are missing
            if end and start:
                duration_minutes = (end - start).total_seconds() / 60.0
            else:
                duration_minutes = 0.0

            # Safely derive the hour component; default to 0 if start is NULL
            start_hour = start.hour if start else 0

            trip_data = TripData(
                trip_id=str(row['trip_id']),
                distance_km=float(row['distance_km'] or 0.0),
                duration_minutes=duration_minutes,
                start_hour=start_hour,
                vehicle_type="Standard",
                is_carpool=is_carpool,
            )

            raw_model = row['billing_model'].upper()
            try:
                model_enum = BillingModelType(raw_model)
            except ValueError:
                model_enum = BillingModelType.HYBRID 
            
            rules_config = row['rules_config'] 

            return trip_data, model_enum, rules_config

        except Exception as e:
            if conn:
                conn.rollback()
            raise e

        finally:
            cursor.close()
            if local_conn and conn:
                conn.close()

    def fetch_active_contract(
        self,
        client_id: str,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> Dict[str, Any]:
        sql = """
        SELECT 
            c.id as contract_id,
            c.vendor_id,
            cv.billing_model,
            cv.rules_config,
            cv.valid_from,
            cv.valid_until
        FROM contracts c
        JOIN contract_versions cv ON c.id = cv.contract_id
        WHERE c.client_id = %s
          AND cv.valid_from <= NOW()
          AND (cv.valid_until IS NULL OR cv.valid_until >= NOW())
        ORDER BY cv.valid_from DESC
        LIMIT 1;
        """

        local_conn = False
        if conn is None:
            conn = self.get_db_connection()
            local_conn = True

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            cursor.execute(sql, (client_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No active contract found for Client ID: {client_id}")

            return {
                "contract_id": str(row["contract_id"]),
                "vendor_id": str(row["vendor_id"]),
                "billing_model": row["billing_model"].upper(),
                "rules_config": row["rules_config"],
            }
        except Exception as e:
            if conn:
                conn.rollback()
            raise e

        finally:
            cursor.close()
            if local_conn and conn:
                conn.close()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    def insert_trip(
        self,
        trip_id: str,
        client_id: str,
        vendor_id: str,
        distance_km: float,
        start_time: str,
        end_time: str,
        is_carpool: bool = False,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> Dict[str, Any]:
        """
        Insert a new trip record into the database.
        """
        sql = """
        INSERT INTO trips (id, client_id, vendor_id, distance_km, start_time, end_time, is_carpool)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, client_id, vendor_id, distance_km, start_time, end_time, is_carpool;
        """

        local_conn = False
        if conn is None:
            conn = self.get_db_connection()
            local_conn = True

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            # Note: `end_time` may be None
            cursor.execute(sql, (trip_id, client_id, vendor_id, distance_km, start_time, end_time, is_carpool))
            row = cursor.fetchone()
            
            conn.commit()

            if not row:
                raise ValueError("Failed to insert trip")

            return {
                "trip_id": str(row["id"]),
                "client_id": str(row["client_id"]),
                "vendor_id": str(row["vendor_id"]),
                "distance_km": float(row["distance_km"]),
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "is_carpool": bool(row.get("is_carpool", False)),
            }

        except Exception as e:
            if local_conn:
                conn.rollback()
            raise e
        finally:
            cursor.close()
            if local_conn and conn:
                conn.close()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    def fetch_client_trips(
        self,
        client_id: str,
        conn: Optional[psycopg2.extensions.connection] = None,
    ) -> list:
        """
        Fetch all trips for a given client. Returns a list of dict rows with
        keys: id, distance_km, start_time, end_time, vendor_id, is_carpool
        """
        sql = """
        SELECT id, distance_km, start_time, end_time, vendor_id, is_carpool
        FROM trips
        WHERE client_id = %s
        ORDER BY start_time DESC;
        """

        local_conn = False
        if conn is None:
            conn = self.get_db_connection()
            local_conn = True

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cursor.execute(sql, (client_id,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "trip_id": str(row["id"]),
                    "distance_km": float(row["distance_km"] or 0.0),
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "vendor_id": str(row["vendor_id"]),
                    "is_carpool": bool(row.get("is_carpool", False)),
                })

            return results
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            cursor.close()
            if local_conn and conn:
                conn.close()
