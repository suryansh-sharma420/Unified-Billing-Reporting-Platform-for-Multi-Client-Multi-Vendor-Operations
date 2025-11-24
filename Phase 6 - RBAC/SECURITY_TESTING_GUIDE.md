# Security Testing & Quick Start Guide

## Prerequisites

Ensure your environment has:
```bash
pip install fastapi uvicorn pydantic python-jose PyJWT passlib python-multipart psycopg2-binary streamlit requests python-dotenv
```

## Step 1: Start the Backend

```bash
cd "Phase 3 - APIs"
python -m uvicorn main_api:app --reload --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 2: Start the Frontend

In a new terminal:
```bash
cd "Phase 4 - UI"
streamlit run app.py
```

Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## Step 3: Test Login Flow

### 3.1 Test Credentials (Pre-seeded in DB)

**CLIENT_ADMIN Account:**
- Email: `admin@client.com`
- Password: `Password@123`
- Role: CLIENT_ADMIN
- Client ID: `c0000000-0000-0000-0000-000000000001`

### 3.2 Login in UI
1. Open Streamlit UI at http://localhost:8501
2. Enter email: `admin@client.com`
3. Enter password: `Password@123`
4. Click "Sign In"

Expected: Successfully logged in, JWT token stored, see role-based UI

## Step 4: Test Core Functionality

### 4.1 Calculate Billing (Tab 1)
1. After login, enter Trip ID: `d0000000-0000-0000-0000-000000000001`
2. Check "Is Carpool?" if desired
3. Click "Calculate Billing"

Expected: Billing breakdown shown with costs

### 4.2 View Contract (Tab 2)
1. Click "Load Contract"

Expected: Contract details and billing rules displayed

### 4.3 Download Report (Tab 3)
1. Scroll to "Download Client Report"
2. Click "Download CSV Report"

Expected: CSV file downloaded to your computer

### 4.4 System Monitor (Tab 4)
1. View last 50 lines of backend logs
2. Click "Refresh Logs" to update

Expected: Log entries visible, refreshes on button click

## Step 5: Create Additional Users (SUPER_ADMIN Only)

### 5.1 Create SUPER_ADMIN User via API

```bash
# First, login as super admin
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@client.com", "password": "Password@123"}'

# Save the access_token from response
# Create another user
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <saved_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "super@moveinsync.com",
    "password": "SuperAdmin@123",
    "role": "SUPER_ADMIN",
    "client_id": null,
    "vendor_id": null
  }'
```

### 5.2 Create New CLIENT_ADMIN User via API

```bash
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <super_admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@company2.com",
    "password": "Manager@123",
    "role": "CLIENT_ADMIN",
    "client_id": "c0000000-0000-0000-0000-000000000002",
    "vendor_id": null
  }'
```

### 5.3 Create New VIEWER User via API

```bash
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <super_admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "auditor@company.com",
    "password": "Auditor@123",
    "role": "VIEWER",
    "client_id": "c0000000-0000-0000-0000-000000000001",
    "vendor_id": null
  }'
```

## Step 6: Test Role-Based Access Control (RBAC)

### 6.1 Test VIEWER Cannot Create Trips

1. Create a VIEWER user (see Step 5.3)
2. Login as VIEWER in UI
3. Note: "Create Trip" button is not available (VIEWER is read-only)

### 6.2 Test Tenant Isolation

1. Login as CLIENT_ADMIN for client_id: `c0000000-0000-0000-0000-000000000001`
2. Try to access billing for a trip belonging to client_id: `c0000000-0000-0000-0000-000000000002`

Expected: 403 Forbidden response

### 6.3 Test SUPER_ADMIN Access

1. Create SUPER_ADMIN user (Step 5.1)
2. Login as SUPER_ADMIN
3. You should see the "⚙️ Admin Config" tab

---

## Manual API Testing (cURL)

### Test 1: Login
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@client.com",
    "password": "Password@123"
  }'
```

Expected Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "CLIENT_ADMIN",
  "client_id": "c0000000-0000-0000-0000-000000000001",
  "vendor_id": null
}
```

### Test 2: Access Secured Endpoint with JWT
```bash
# Extract token from login response
export JWT_TOKEN="<your_access_token>"

curl -X GET "http://127.0.0.1:8000/secure/billing/d0000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

Expected: Billing data in JSON format

### Test 3: Try to Access Without JWT
```bash
curl -X GET "http://127.0.0.1:8000/secure/billing/d0000000-0000-0000-0000-000000000001"
```

Expected Response (403 or 401):
```json
{"detail": "Not authenticated"}
```

### Test 4: Try to Access with Invalid JWT
```bash
curl -X GET "http://127.0.0.1:8000/secure/billing/d0000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer invalid_token_here"
```

Expected Response:
```json
{"detail": "Invalid or expired token"}
```

### Test 5: Access Admin Endpoint without SUPER_ADMIN Role
```bash
# Use CLIENT_ADMIN JWT
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer $CLIENT_ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@123",
    "role": "CLIENT_ADMIN",
    "client_id": "c0000000-0000-0000-0000-000000000001"
  }'
```

Expected Response (403 Forbidden):
```json
{"detail": "Forbidden"}
```

---

## Troubleshooting

### Issue: "Cannot connect to API"

**Solution:**
- Ensure FastAPI backend is running on port 8000
- Check: http://127.0.0.1:8000/health
- Should return: `{"status": "ok", "service": "MoveInSync Billing API"}`

### Issue: "Invalid credentials"

**Solution:**
- Verify email and password are correct
- Pre-seeded user: `admin@client.com` / `Password@123`
- Check database has users table created (happens on startup)

### Issue: "Token expired"

**Solution:**
- Login again to get a fresh token
- Default TTL is 60 minutes
- Set `JWT_TTL_MIN` environment variable to change

### Issue: Database connection error

**Solution:**
- Ensure PostgreSQL is running
- Check DB credentials in environment variables
- Verify database `moveinsync_db` exists
- Check Phase 1 SQL files for schema setup

### Issue: "Invalid X-Client-ID header" on old endpoints

**Solution:**
- Old endpoints (GET /billing/{trip_id}) still use X-Client-ID for backward compatibility
- New secure endpoints use JWT (GET /secure/billing/{trip_id})
- UI automatically uses secure endpoints

---

## Security Checklist

Before deploying to production, ensure:

- [ ] **Change JWT_SECRET** to a strong random key
- [ ] **Enable HTTPS** on FastAPI (use reverse proxy or SSL certs)
- [ ] **Set strong passwords** for all default users
- [ ] **Enable audit logging** for sensitive operations
- [ ] **Test all role combinations** manually
- [ ] **Configure rate limiting** on login endpoint
- [ ] **Set up monitoring** for failed authentication attempts
- [ ] **Use environment variables** for all secrets
- [ ] **Review CORS settings** for frontend domain
- [ ] **Test token expiration** behavior

---

## Key Implementation Files

| File | Purpose |
|------|---------|
| `Phase 3 - APIs/api_models.py` | Pydantic models (User, Token, LoginRequest) |
| `Phase 3 - APIs/auth.py` | JWT creation/validation, password hashing |
| `Phase 3 - APIs/dependencies.py` | get_current_user, require_role, connection pool |
| `Phase 3 - APIs/main_api.py` | Secured endpoints with JWT + RBAC |
| `Phase 4 - UI/app.py` | Streamlit UI with JWT token storage |

---

## Next Steps

1. **Create seed users** for different test scenarios
2. **Set up audit logging** to track all access
3. **Implement refresh tokens** for longer sessions
4. **Add MFA** for SUPER_ADMIN accounts
5. **Configure monitoring** and alerts
6. **Load test** token validation performance
7. **Document API** using OpenAPI/Swagger (auto-generated by FastAPI)

Access Swagger UI at: http://127.0.0.1:8000/docs

