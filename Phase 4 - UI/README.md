# Phase 4 - Streamlit UI

## 📱 MoveInSync Client Application

This is the **Frontend/UI Layer** for the MoveInSync billing platform.

### Architecture

```
[User] → [Streamlit UI] ← HTTP Requests → [FastAPI Backend] ← [Database]
```

**Key Principle:** The UI does **NOT** talk directly to the database. All data requests go through the FastAPI backend using HTTP requests with proper authentication headers (`X-Client-ID`).

---

## 🎯 Features Implemented

### Tab 1: Billing Calculator 💰
- Input a Trip ID
- Click "Calculate Billing" to fetch the cost breakdown
- Displays:
  - Billing model (Fixed Rate, Distance-Based, Hybrid)
  - Base cost
  - Tax amount
  - Total cost
  - Full breakdown JSON

### Tab 2: Contract Viewer 📋
- Load your organization's active contract
- View:
  - Contract ID
  - Vendor ID
  - Billing model type
  - Billing rules configuration
- Demonstrates **API caching** (contract rules are cached after first fetch)

### Tab 3: Analytics Dashboard 📊
- Visual charts and metrics
- Monthly billing summary (bar chart)
- Billing model distribution
- Total billed, average, and trip statistics
- Uses **simulated data** for demonstration (real data would require more historical trips)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Streamlit installed (see `requirements.txt`)
- FastAPI backend running on `http://127.0.0.1:8000`

### Installation

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Ensure the backend is running:**
   ```powershell
   cd "Phase 3 - APIs"
   uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Run the Streamlit app:**
   ```powershell
   cd "Phase 4 - UI"
   streamlit run app.py
   ```

4. **Open your browser:**
   - Streamlit will open automatically at `http://localhost:8501`

---

## 🔐 How to Use the UI

### Step 1: Login with Client ID
1. On the left sidebar, enter a test Client ID:
   ```
   c0000000-0000-0000-0000-000000000001
   ```
2. Click **"Check API Health"** to verify the backend is running

### Step 2: Try the Billing Calculator
1. Go to the **"💰 Billing Calculator"** tab
2. Enter a Trip ID (default: `d0000000-0000-0000-0000-000000000001`)
3. Click **"Calculate Billing"**
4. View the cost breakdown

### Step 3: View Your Contract
1. Go to the **"📋 Contract Viewer"** tab
2. Click **"Load Contract"**
3. See the billing rules for your organization

### Step 4: Explore Analytics
1. Go to the **"📊 Analytics"** tab
2. View charts and metrics (simulated data for demo purposes)

---

## 📝 Test Data

**Test Client ID:**
```
c0000000-0000-0000-0000-000000000001
```

**Test Trip ID:**
```
d0000000-0000-0000-0000-000000000001
```

(These are seeded in Phase 1 Database)

---

## 🛠️ How It Works

### Session State Management
- **st.session_state.client_id**: Persists the logged-in client across page refreshes
- **st.session_state.api_connected**: Tracks whether the backend API is reachable

### API Communication
All requests include the `X-Client-ID` header for client isolation:
```python
headers = {"X-Client-ID": st.session_state.client_id}
response = requests.get(f"{API_BASE_URL}/billing/{trip_id}", headers=headers)
```

### Error Handling
- Connection errors → "Cannot connect to API"
- Invalid client ID → 400 error
- Trip not found → 404 error
- Timeout errors → "Request timeout"

---

## 📊 Demonstration of "Separation of Concerns"

This UI proves you understand **Separation of Concerns**:

| Layer | Responsibility | Technology |
|-------|-----------------|-----------|
| **Frontend** | User interaction, display | Streamlit |
| **Backend** | Business logic, validation | FastAPI |
| **Database** | Data persistence | PostgreSQL |
| **Communication** | HTTP requests with headers | REST API |

The frontend **never** directly accesses the database—everything goes through the API.

---

## 🐛 Troubleshooting

### "Cannot connect to API"
- Ensure the FastAPI backend is running: `uvicorn main_api:app --reload --port 8000`
- Check that it's on `http://127.0.0.1:8000`

### "Invalid Client ID" or "Bad Request"
- Verify the Client ID is correct (must be a UUID)
- Ensure it's in the database (seeded in Phase 1)

### "Trip not found"
- Verify the Trip ID exists in the database
- Use the test Trip ID: `d0000000-0000-0000-0000-000000000001`

### Streamlit won't start
- Install missing dependencies: `pip install streamlit requests pandas`
- Check Python version: `python --version` (must be 3.9+)

---

## 📚 Related Documentation

- **Phase 1 (Database):** See `Phase 1 - Database/README.md`
- **Phase 2 (Core Logic):** See `Phase 2 - core logic OOP/README.md`
- **Phase 3 (API):** See `Phase 3 - APIs/QUICKSTART.md` and `README.md`

---

## 🎓 Learning Outcomes

By building this UI, you've demonstrated:

1. ✅ **Frontend Development** - Streamlit UI with tabs and forms
2. ✅ **API Integration** - HTTP requests with authentication headers
3. ✅ **State Management** - Session state across page refreshes
4. ✅ **Error Handling** - Graceful error messages
5. ✅ **Separation of Concerns** - Frontend never touches database
6. ✅ **Multi-tenancy** - Client isolation via headers
7. ✅ **Caching Benefits** - Contract endpoint uses cached results
8. ✅ **Data Visualization** - Charts and metrics dashboards

---

**Last updated:** November 2025
