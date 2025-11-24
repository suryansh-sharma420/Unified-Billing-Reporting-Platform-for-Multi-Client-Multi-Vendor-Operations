# Security Architecture Diagram & Flow Charts

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MoveInSync Security Stack                     │
└──────────────────────────────────────────────────────────────────────┘

                            FRONTEND LAYER
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit UI (Phase 4)                    │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Email/Password │  │  JWT Storage   │  │ Bearer Token │  │
│  │     Form       │  │  in Session    │  │   in Header  │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│           │                  │                     │          │
│           └──────────────────┴─────────────────────┘          │
│                         │                                     │
│              All Requests: Authorization: Bearer             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                             │
                    HTTP/HTTPS (Encrypted)
                             │
┌──────────────────────────────────────────────────────────────┐
│                    API SECURITY LAYER                        │
├──────────────────────────────────────────────────────────────┤
│ 1. OAuth2PasswordBearer (Extract token from header)          │
│ 2. decode_token() (Verify JWT signature & expiration)        │
│ 3. get_current_user() (Query user from database)             │
│ 4. require_role() (Check RBAC permissions)                   │
│ 5. Endpoint Logic (Tenant isolation check)                   │
└──────────────────────────────────────────────────────────────┘
                             │
┌──────────────────────────────────────────────────────────────┐
│              BACKEND SERVICE LAYER (Phase 3)                 │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Auth.py    │  │  Billing     │  │  Trip Service    │  │
│  │              │  │  Calculation │  │                  │  │
│  │ • hash_pwd   │  │              │  │ • Create trips   │  │
│  │ • create_jwt │  │ • Estimate   │  │ • Validate scope │  │
│  │ • decode_jwt │  │ • Rules      │  │ • Check vendor   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                               │
│              Connection Pool (Min: 1, Max: 5)                │
└──────────────────────────────────────────────────────────────┘
                             │
                         PostgreSQL
                             │
┌──────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER (Phase 1)                   │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Users     │  │ Contracts│  │  Trips   │  │  Vendors │ │
│  │             │  │          │  │          │  │          │ │
│  │ • id (PK)   │  │ • id     │  │ • id     │  │ • id     │ │
│  │ • email     │  │ • rules  │  │ • dist   │  │ • name   │ │
│  │ • pwd_hash  │  │          │  │ • client │  │          │ │
│  │ • role ← →  │  │          │  │ • vendor │  │          │ │
│  │ • client_id │  │          │  │ • cost   │  │          │ │
│  │ • vendor_id │  │          │  │          │  │          │ │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                               │
│  CHECK: role-tenant relationship constraints                 │
│  - SUPER_ADMIN: client_id=NULL, vendor_id=NULL              │
│  - CLIENT_ADMIN: client_id!=NULL, vendor_id=NULL            │
│  - VENDOR_ADMIN: vendor_id!=NULL                             │
│  - VIEWER: client_id!=NULL, vendor_id=NULL                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

```
                      User Provides Credentials
                       (Email + Password)
                              │
                              ▼
                    ┌────────────────────┐
                    │  Streamlit UI      │
                    │  Email/Password    │
                    │  Form              │
                    └────────┬───────────┘
                             │
                             │ POST /auth/login
                             │ Content-Type: application/json
                             │ Body: {"email": "...", "password": "..."}
                             │
                             ▼
                    ┌────────────────────┐
                    │  FastAPI Backend   │
                    │  /auth/login       │
                    └────────┬───────────┘
                             │
                    ┌────────▼──────────┐
                    │ Query users table │
                    │ WHERE email = ?   │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────────────┐
                    │ User Found?                │
                    └────────┬──────────┬───────┘
                             │         │
                        YES  │         │  NO
                             │         │
                    ┌────────▼──┐  ┌──▼────────────┐
                    │ Verify    │  │ Return 401    │
                    │ Password  │  │ Unauthorized  │
                    │ (bcrypt)  │  └───────────────┘
                    └────────┬──┘
                             │
                    ┌────────▼──────────┐
                    │ Password Valid?   │
                    └────────┬──┬───────┘
                             │  │
                        YES  │  │  NO
                             │  │
                    ┌────────▼──┐  ┌──▼────────────┐
                    │ Create    │  │ Return 401    │
                    │ JWT Token │  │ Unauthorized  │
                    │ (HS256)   │  └───────────────┘
                    └────────┬──┘
                             │
                    ┌────────▼──────────────────┐
                    │ JWT Payload:              │
                    │ {                         │
                    │   "sub": user_id,         │
                    │   "role": role,           │
                    │   "client_id": ...,       │
                    │   "vendor_id": ...,       │
                    │   "exp": expiration       │
                    │ }                         │
                    └────────┬──────────────────┘
                             │
                    ┌────────▼──────────────────┐
                    │ Return TokenResponse:     │
                    │ {                         │
                    │   "access_token": "...",  │
                    │   "token_type": "bearer", │
                    │   "role": role,           │
                    │   "client_id": ...        │
                    │ }                         │
                    └────────┬──────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │  Streamlit UI      │
                    │  Store in          │
                    │  st.session_state  │
                    │  Display user info │
                    └────────────────────┘
```

---

## Authorization Flow (Request with JWT)

```
                    User Makes Request
                  (with Authorization header)
                         │
                         ▼
        ┌─────────────────────────────────────────┐
        │ Authorization: Bearer <JWT_TOKEN>       │
        │ GET /secure/billing/{trip_id}           │
        └──────────────┬──────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────┐
        │  OAuth2PasswordBearer dependency        │
        │  Extract token from Authorization       │
        │  header (remove "Bearer " prefix)       │
        └──────────────┬──────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────┐
        │  decode_token(token)                    │
        │  • Verify signature using JWT_SECRET    │
        │  • Check expiration time (exp)          │
        │  • Extract payload                      │
        └──────────────┬──────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        │  Token Valid?               │
        │                             │
        ▼                             ▼
    ┌─────────┐               ┌──────────────┐
    │   YES   │               │      NO      │
    └────┬────┘               └──────┬───────┘
         │                           │
         │                    ┌──────▼────────┐
         │                    │ Return 401    │
         │                    │ Unauthorized  │
         │                    └───────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │ get_current_user()       │
    │ Query users WHERE id=sub │
    │ from token payload       │
    └────────┬─────────────────┘
             │
        ┌────┴───────────────┐
        │                    │
        │ User Found?        │
        │                    │
        ▼                    ▼
    ┌────────┐          ┌──────────────┐
    │  YES   │          │     NO       │
    └───┬────┘          └────┬─────────┘
        │                    │
        │             ┌──────▼────────┐
        │             │ Return 401    │
        │             │ User not found│
        │             └───────────────┘
        │
        ▼
    ┌──────────────────────────┐
    │ require_role dependency  │
    │ Check user.role in       │
    │ allowed_roles            │
    └────────┬─────────────────┘
             │
        ┌────┴──────────────┐
        │                   │
        │ Role Allowed?     │
        │                   │
        ▼                   ▼
    ┌────────┐          ┌──────────────┐
    │  YES   │          │     NO       │
    └───┬────┘          └────┬─────────┘
        │                    │
        │             ┌──────▼────────┐
        │             │ Return 403    │
        │             │ Forbidden     │
        │             └───────────────┘
        │
        ▼
    ┌──────────────────────────┐
    │ Endpoint Logic           │
    │ Get trip from database   │
    │ Check: trip.client_id == │
    │        user.client_id    │
    └────────┬─────────────────┘
             │
        ┌────┴──────────────────┐
        │                       │
        │ Tenant Match?         │
        │                       │
        ▼                       ▼
    ┌──────────┐         ┌──────────────┐
    │   YES    │         │     NO       │
    └────┬─────┘         └────┬─────────┘
         │                    │
         │             ┌──────▼────────┐
         │             │ Return 403    │
         │             │ Forbidden     │
         │             │ (cross-tenant)│
         │             └───────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │ Execute Business Logic   │
    │ Calculate billing costs  │
    │ Return data to user      │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Return 200 OK            │
    │ JSON response with data  │
    └──────────────────────────┘
```

---

## Role-Based Access Control (RBAC) Matrix

```
┌────────────────────────────────────────────────────────────────────┐
│                         RBAC Permission Matrix                    │
├────────────────────────────────────────────────────────────────────┤
│ Role         │ GET Billing │ POST Trip │ GET Contracts │ SUPER_ADMIN │
├──────────────┼─────────────┼───────────┼───────────────┼─────────────┤
│ SUPER_ADMIN  │ ALL DATA ✓  │ ✓ All     │ ✓ All         │ ✓ Yes       │
├──────────────┼─────────────┼───────────┼───────────────┼─────────────┤
│ CLIENT_ADMIN │ ✓ Own       │ ✓ Own     │ ✓ Own         │ ✗ No        │
│              │ Tenant Only │ Tenant    │ Tenant        │             │
├──────────────┼─────────────┼───────────┼───────────────┼─────────────┤
│ VENDOR_ADMIN │ ✓ Own       │ ✓ Own     │ ✗ No          │ ✗ No        │
│              │ Vendor Only │ Vendor    │                │             │
├──────────────┼─────────────┼───────────┼───────────────┼─────────────┤
│ VIEWER       │ ✓ Read      │ ✗ No      │ ✓ Read Only   │ ✗ No        │
│              │ Only        │ (403)     │                │             │
└────────────────────────────────────────────────────────────────────┘

Tenant Isolation Rules:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLIENT_ADMIN / VIEWER:
  Trip.client_id MUST EQUAL User.client_id
  Result: 403 Forbidden if mismatch

VENDOR_ADMIN:
  Trip.vendor_id MUST EQUAL User.vendor_id
  Result: 403 Forbidden if mismatch

SUPER_ADMIN:
  No restriction (can access all tenants/vendors)
  Can use role to perform audits and admin tasks
```

---

## Database Schema with Security

```
┌────────────────────────────────────────────────────────────────────┐
│                      users Table (Secured)                         │
├────────────────────────────────────────────────────────────────────┤
│ Column       │ Type     │ Constraints      │ Purpose              │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ id           │ UUID     │ PRIMARY KEY      │ User identifier      │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ email        │ TEXT     │ UNIQUE, NOT NULL │ Login credential     │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ password_hash│ TEXT     │ NOT NULL         │ Bcrypt hash (salted) │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ role         │ TEXT     │ NOT NULL         │ Permission level     │
│              │          │ CHECK IN(...)    │ Values: SUPER_ADMIN, │
│              │          │                  │ CLIENT_ADMIN,        │
│              │          │                  │ VENDOR_ADMIN, VIEWER │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ client_id    │ UUID     │ NULL             │ Tenant binding       │
│              │          │ (Conditional)    │ Required for:        │
│              │          │                  │ CLIENT_ADMIN, VIEWER │
├──────────────┼──────────┼──────────────────┼──────────────────────┤
│ vendor_id    │ UUID     │ NULL             │ Vendor binding       │
│              │          │ (Conditional)    │ Required for:        │
│              │          │                  │ VENDOR_ADMIN         │
└────────────────────────────────────────────────────────────────────┘

CHECK Constraint (Role-Tenant Relationship):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(role = 'SUPER_ADMIN' AND client_id IS NULL AND vendor_id IS NULL)
    OR
(role IN ('CLIENT_ADMIN','VIEWER') AND client_id IS NOT NULL AND vendor_id IS NULL)
    OR
(role = 'VENDOR_ADMIN' AND vendor_id IS NOT NULL)

This ensures:
✓ SUPER_ADMIN cannot be bound to a tenant
✓ CLIENT_ADMIN/VIEWER must have a client but no vendor
✓ VENDOR_ADMIN must have a vendor
✓ No orphaned roles without proper bindings
```

---

## Token Lifecycle

```
                      User Initiates Login
                              │
                              ▼
                    ┌──────────────────────┐
                    │ POST /auth/login     │
                    │ (Email + Password)   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Create JWT Token     │
                    │ Payload:             │
                    │ • sub: user_id       │
                    │ • role: role         │
                    │ • client_id: ...     │
                    │ • vendor_id: ...     │
                    │ • iat: issued_at     │
                    │ • exp: now + 60min   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Return JWT Token     │
                    │ Stored in UI         │
                    │ (Session State)      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                  │
        Time passes (0-60 min)          Time passes (>60 min)
              │                                  │
              ▼                                  ▼
    ┌──────────────────────┐       ┌──────────────────────┐
    │ Token Still Valid    │       │ Token Expired        │
    │                      │       │                      │
    │ User makes request   │       │ User makes request   │
    │ with Bearer token    │       │ with Bearer token    │
    │                      │       │                      │
    │ Backend validates:   │       │ Backend validates:   │
    │ ✓ Signature OK       │       │ ✗ Expiration check:  │
    │ ✓ Not expired        │       │   exp < current_time │
    │ ✓ User in database   │       │                      │
    │                      │       │ Return 401:          │
    │ Return 200 OK        │       │ "Invalid or expired  │
    │ with data            │       │ token"               │
    │                      │       │                      │
    │ Refresh: Continue    │       │ UI catches 401 and   │
    │ making requests      │       │ redirects to login   │
    └──────────────────────┘       │                      │
                                    │ User enters new      │
                                    │ credentials and      │
                                    │ gets fresh token     │
                                    └──────────────────────┘
```

---

## Error Handling Flow

```
                    API Request Received
                         │
                         ▼
        ┌──────────────────────────────────┐
        │ Is Authorization Header Present? │
        └────────┬──────────────┬──────────┘
                 │              │
                YES             NO
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 403:         │
                 │    │ "Not authenticated" │
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Does Token Start with "Bearer "? │
        └────────┬──────────────┬──────────┘
                 │              │
                YES             NO
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 403:         │
                 │    │ "Not authenticated" │
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ decode_token(token_string)       │
        └────────┬──────────────┬──────────┘
                 │              │
             VALID           INVALID
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 401:         │
                 │    │ "Invalid or expired │
                 │    │ token"              │
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Extract "sub" (user_id)          │
        │ Query user from database         │
        └────────┬──────────────┬──────────┘
                 │              │
            FOUND            NOT FOUND
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 401:         │
                 │    │ "User not found"    │
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Is role in allowed_roles?        │
        └────────┬──────────────┬──────────┘
                 │              │
                YES             NO
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 403:         │
                 │    │ "Forbidden"         │
                 │    │ (Insufficient perms)│
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Execute Endpoint Logic           │
        │ (Tenant isolation checks, etc.)  │
        └────────┬──────────────┬──────────┘
                 │              │
              SUCCESS        VALIDATION
                 │            ERROR
                 │              │
                 │              ▼
                 │    ┌─────────────────────┐
                 │    │ Return 400:         │
                 │    │ "Bad Request"       │
                 │    │ (Invalid input)     │
                 │    └─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Return 200/201                   │
        │ with JSON response               │
        └──────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRODUCTION DEPLOYMENT                      │
└─────────────────────────────────────────────────────────────────┘

                        INTERNET
                           │
                           │ HTTPS (TLS 1.3)
                           │
                    ┌──────▼────────┐
                    │  Reverse Proxy│  (nginx, CloudFlare)
                    │ (CORS Config) │
                    └──────┬────────┘
                           │
                    ┌──────▼─────────────┐
                    │  Rate Limiter      │
                    │  (Max 10 reqs/sec) │
                    │  on /auth/login    │
                    └──────┬─────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    │              LOAD BALANCER                  │
    │           (Round-Robin / LB)                │
    │                                             │
    ├─────────────┬─────────────┬─────────────┤
    │             │             │             │
    ▼             ▼             ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ FastAPI│ │ FastAPI│ │ FastAPI│ │ FastAPI│
│Instance│ │Instance│ │Instance│ │Instance│
│Port 8K1│ │Port 8K2│ │Port 8K3│ │Port 8K4│
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    │ Connection Pools (min: 1, max: 5 each)
    │          │          │          │
    └──────────┼──────────┼──────────┘
               │
               ▼
        ┌─────────────────┐
        │  PostgreSQL DB  │
        │  (Replicated)   │
        │  Master + Slave │
        │                 │
        │ SSL/TLS for     │
        │ DB connections  │
        └─────────────────┘

Security Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ HTTPS (TLS 1.3) for all traffic
✓ JWT_SECRET stored in secrets manager (not in code)
✓ Database credentials from environment
✓ Rate limiting on auth endpoints
✓ CORS configured for known domains
✓ Connection pool with SSL to database
✓ Health checks on all instances
✓ Audit logging to external service
✓ Monitoring and alerting enabled
✓ Automatic failover on instance failure
```

---

## Summary

This security architecture provides:

1. **Authentication:** JWT tokens with cryptographic signatures
2. **Authorization:** Four-tier RBAC with role validation
3. **Multi-Tenancy:** Explicit tenant isolation via client_id/vendor_id
4. **Audit:** Logging of critical operations
5. **Resilience:** Connection pooling and error handling
6. **Scalability:** Stateless design for horizontal scaling

All flows ensure that **only authenticated, authorized users** can access **only their tenant's data**.

