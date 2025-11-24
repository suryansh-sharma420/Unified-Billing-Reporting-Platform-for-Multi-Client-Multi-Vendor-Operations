"""Authentication utilities: password hashing and JWT handling."""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt  # PyJWT
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Configuration (override in environment variables in production)
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "development-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_TTL_MIN", "60"))  # default 1h

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _token_payload(user_id: uuid.UUID, role: str, client_id: Optional[str], vendor_id: Optional[str]) -> Dict[str, Any]:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "client_id": client_id,
        "vendor_id": vendor_id,
        "exp": exp,
    }
    return payload


def create_access_token(*, user_id: uuid.UUID, role: str, client_id: Optional[str] = None, vendor_id: Optional[str] = None) -> str:
    """Create a signed JWT access token."""
    payload = _token_payload(user_id, role, client_id, vendor_id)
    encoded_jwt: str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode & validate a JWT. Raises jwt exceptions on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
