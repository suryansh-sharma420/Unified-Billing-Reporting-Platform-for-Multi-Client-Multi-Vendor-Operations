# Quick Reference Card

## 🚀 Getting Started (5 Minutes)

### Step 1: Start Backend
```bash
cd "Phase 3 - APIs"
python -m uvicorn main_api:app --reload --host 127.0.0.1 --port 8000
```
✅ See: "Started server process" and "Uvicorn running"

### Step 2: Start Frontend
```bash
cd "Phase 4 - UI"
streamlit run app.py
```
✅ See: "Local URL: http://localhost:8501"

### Step 3: Login
- Open http://localhost:8501
- Email: `admin@client.com`
- Password: `Password@123`
- Click "Sign In"

✅ See: Logged in dashboard with tabs

---

## 🔐 Test Credentials

| Email | Password | Role | Scope |
|-------|----------|------|-------|
| admin@client.com | Password@123 | CLIENT_ADMIN | c0000000-0000-0000-0000-000000000001 |

### Create More Test Users
Once logged in as CLIENT_ADMIN, use admin panel (if you create a SUPER_ADMIN account first via API):

```bash
# Create SUPER_ADMIN (as CLIENT_ADMIN, get their JWT first)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@client.com", "password": "Password@123"}'

# Get JWT from response (access_token field)
# Then create SUPER_ADMIN
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "super@moveinsync.com",
    "password": "SuperAdmin@123",
    "role": "SUPER_ADMIN",
    "client_id": null,
    "vendor_id": null
  }'
```

---

## 📊 Role Reference

```
SUPER_ADMIN     → All data, user management
CLIENT_ADMIN    → Own tenant data, no admin panel
VENDOR_ADMIN    → Own vendor data
VIEWER          → Read-only own tenant
```

---

## 🧪 Quick Tests

### Test 1: Billing Calculation ✅
1. Tab 1 → Enter Trip ID: `d0000000-0000-0000-0000-000000000001`
2. Click "Calculate Billing"
3. See: Billing breakdown with costs

### Test 2: Contract Viewing ✅
1. Tab 2 → Click "Load Contract"
2. See: Contract details and rules

### Test 3: Download Report ✅
1. Tab 3 → Click "Download CSV Report"
2. See: CSV file downloaded

### Test 4: System Logs ✅
1. Tab 4 → See last 50 log lines
2. Click "Refresh Logs"

### Test 5: Admin Panel (If SUPER_ADMIN) ✅
1. Tab 5 → "Admin Configuration"
2. Create new user:
   - Email: `test@example.com`
   - Password: `Test@123`
   - Role: CLIENT_ADMIN
3. Click "Create User"
4. See: User created message

---

## 🔑 Key API Endpoints

### Public
```
POST /auth/login
  Input:  {"email": "...", "password": "..."}
  Output: {"access_token": "...", "role": "...", ...}
```

### Secured (Requires Bearer Token)
```
GET /secure/billing/{trip_id}
GET /secure/contracts
POST /secure/trips
GET /secure/billing/export-csv
POST /admin/users (SUPER_ADMIN only)
```

### Health Check
```
GET /health
  Output: {"status": "ok", "service": "MoveInSync Billing API"}
```

---

## 🛠️ Configuration

### .env (Optional)
```bash
JWT_SECRET=your-key-here
JWT_TTL_MIN=60
DB_HOST=localhost
DB_PORT=5432
```

### Default Database
```
Host: localhost
Port: 5432
Database: moveinsync_db
User: postgres
```

---

## ❌ Troubleshooting

| Issue | Solution |
|-------|----------|
| Cannot login | Check credentials: admin@client.com / Password@123 |
| API not responding | Check backend running on http://127.0.0.1:8000 |
| Token expired | Logout and login again (TTL: 60 min) |
| Permission denied (403) | Your role lacks permission for that operation |
| Database error | Ensure PostgreSQL running and DB created |

---

## 📚 Documentation Map

```
📁 MoveInSync/
├── SECURITY_README.md                 ← START HERE
├── SECURITY_TESTING_GUIDE.md          ← Testing instructions
├── SECURITY_IMPLEMENTATION.md         ← Architecture deep-dive
├── IMPLEMENTATION_COMPLETE.md         ← Implementation details
├── VERIFICATION_CHECKLIST.md          ← Component checklist
├── ARCHITECTURE_DIAGRAMS.md           ← Visual flows
│
├── Phase 3 - APIs/
│   ├── main_api.py                    ← Backend endpoints
│   ├── auth.py                        ← JWT functions
│   ├── dependencies.py                ← Security dependencies
│   ├── api_models.py                  ← Pydantic models
│   └── moveinsync_app.log             ← Live logs
│
└── Phase 4 - UI/
    └── app.py                         ← Streamlit frontend
```

---

## ✅ Verification Checklist

- [x] Backend starts without errors
- [x] Frontend starts without errors
- [x] Login works with correct credentials
- [x] Login fails with incorrect credentials
- [x] JWT token stored in session
- [x] Billing calculation works
- [x] Contract viewer works
- [x] CSV export works
- [x] Logs visible in system monitor
- [x] No compilation errors
- [x] All endpoints accessible

---

## 🎓 Security Concepts

### JWT (JSON Web Token)
- Contains: header.payload.signature
- Signed with: HS256 algorithm
- Includes: user_id, role, client_id, expiration
- Validated: On every secure request

### RBAC (Role-Based Access Control)
- 4 roles: SUPER_ADMIN, CLIENT_ADMIN, VENDOR_ADMIN, VIEWER
- Checked: Via `require_role()` dependency
- Denied: Returns 403 Forbidden

### Multi-Tenancy
- Isolation: Via client_id/vendor_id
- Checked: In endpoint logic
- Denied: Returns 403 Forbidden

### Password Security
- Hashed: Using bcrypt
- Salted: Automatically by bcrypt
- Verified: On login with verify_password()

---

## 💡 Pro Tips

### Tip 1: Check Token Contents
```bash
# Decode JWT at https://jwt.io (for inspection only)
# Paste your access_token there to see payload
```

### Tip 2: Test RBAC
```bash
# Try creating trip as VIEWER (should fail)
# Try accessing admin endpoint as CLIENT_ADMIN (should fail)
```

### Tip 3: Monitor Logs
```bash
# Check Phase 3 - APIs/moveinsync_app.log
# Refresh in Tab 4 to see real-time logs
```

### Tip 4: Token Expiration
```bash
# Edit JWT_TTL_MIN=1 to test 1-minute tokens
# Wait 1+ minute and try accessing endpoint
# Should get 401 Unauthorized
```

### Tip 5: Database Queries
```bash
# psql -U postgres -d moveinsync_db
# SELECT * FROM users;  -- View created users
# SELECT * FROM trips;  -- View trips
```

---

## 🚨 Important Notes

### ⚠️ Development Only
- JWT_SECRET in code (change in production)
- HTTP only (use HTTPS in production)
- No rate limiting on auth (add in production)

### 🔒 Production Requirements
- Change JWT_SECRET to strong random key
- Enable HTTPS (TLS 1.3)
- Configure CORS for frontend domain
- Set strong database password
- Enable audit logging
- Configure monitoring/alerting
- Set rate limiting on /auth/login

### 📝 Before Deploying
- [ ] Update JWT_SECRET
- [ ] Enable HTTPS
- [ ] Configure database credentials
- [ ] Run full security audit
- [ ] Load test endpoints
- [ ] Test all role combinations

---

## 📞 Need Help?

1. **See errors?** Check SECURITY_TESTING_GUIDE.md troubleshooting section
2. **Want to test?** Follow SECURITY_TESTING_GUIDE.md step-by-step
3. **Need architecture?** Read SECURITY_IMPLEMENTATION.md
4. **Check verification?** See VERIFICATION_CHECKLIST.md
5. **View flows?** Read ARCHITECTURE_DIAGRAMS.md

---

## 🎯 Next Steps

1. ✅ Start both services (backend + frontend)
2. ✅ Test login with provided credentials
3. ✅ Run through all manual tests
4. ✅ Create additional test users
5. ✅ Test each role independently
6. ✅ Review documentation
7. ✅ Plan deployment configuration
8. ✅ Schedule security review

---

## 📊 System Health

### Backend Health Check
```bash
curl http://127.0.0.1:8000/health
```
Expected: `{"status": "ok", "service": "MoveInSync Billing API"}`

### Database Connection
```bash
psql -U postgres -d moveinsync_db -c "SELECT 1;"
```
Expected: `1` (successful connection)

### API Documentation
Visit: http://127.0.0.1:8000/docs

---

**Status: ✅ READY TO USE**

**Last Updated: November 24, 2025**

For detailed information, see the comprehensive documentation files listed above.

