import os
import uuid
from typing import Generator, Optional

from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from psycopg2 import pool

from fastapi import Header, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

from api_models import UserOut, RoleType
from auth import decode_token

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Load environment variables
load_dotenv()

# Connection pool configuration from env with sensible defaults
DB_MIN_CONN = int(os.getenv("DB_POOL_MINCONN", "1"))
DB_MAX_CONN = int(os.getenv("DB_POOL_MAXCONN", "5"))
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "moveinsync_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}


# Initialize a module-level SimpleConnectionPool. This happens once on import.
try:
    connection_pool: pool.SimpleConnectionPool = pool.SimpleConnectionPool(
        DB_MIN_CONN,
        DB_MAX_CONN,
        **DB_CONFIG
    )
except Exception as e:
    # If pool creation fails, raise a clear error so developers notice on startup.
    raise RuntimeError(f"Failed to create DB connection pool: {e}")


def get_db_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    FastAPI dependency that yields a DB connection from the module-level pool.

    Usage in FastAPI route:
      async def endpoint(conn=Depends(get_db_conn)):
          cur = conn.cursor()
          cur.execute(...)

    Behavior:
      - Borrow a connection from the pool at the start of the request.
      - Yield it to the request handler.
      - Return the connection to the pool after the request completes.
    """
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        if conn:
            try:
                # Rollback any open transaction to leave connection clean
                conn.rollback()
            except Exception:
                pass
            connection_pool.putconn(conn)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def get_current_user(token: str = Depends(oauth2_scheme), conn=Depends(get_db_conn) ) -> UserOut:
    """Validate JWT and return the current user object."""
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Malformed token")

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id,email,role,client_id,vendor_id FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
    return UserOut(**row)


def require_role(*allowed: RoleType):
    def _inner(current_user: UserOut = Depends(get_current_user)):
        if current_user.role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return _inner


# ---------------------------------------------------------------------------
# Legacy header client-id (to be deprecated)
# ---------------------------------------------------------------------------

def get_client_id(x_client_id: str = Header(...)) -> str:
    """
    FastAPI dependency that extracts and validates the `X-Client-ID` header.

    Validation rules:
      - Non-empty header required (FastAPI enforces via Header(...)).
      - Must be a valid UUID string.

    Returns the client id (as string) which maps to `client_id` in the DB.
    """
    try:
        # Validate UUID format
        _ = uuid.UUID(x_client_id)
        return x_client_id
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid X-Client-ID header; must be a UUID")
