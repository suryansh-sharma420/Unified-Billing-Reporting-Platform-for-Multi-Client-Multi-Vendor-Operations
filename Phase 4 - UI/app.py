"""
Phase 4 - Streamlit UI for MoveInSync Billing Platform

Architecture:
[User] → [Streamlit UI] → (HTTP Requests) → [FastAPI Backend] → [Database]

This UI is NOT allowed to talk to the database directly.
All communication goes through the FastAPI backend via HTTP requests.
"""

import streamlit as st
import pandas as pd
import requests
import jwt
from datetime import datetime
from pathlib import Path
import time
import psutil # Added for system metrics

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://127.0.0.1:8000"
PAGE_TITLE = "MoveInSync Billing Platform"

# Set page config
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Session State Initialization
# ============================================================================

if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = ""

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_role" not in st.session_state:
    st.session_state.user_role = ""

if "client_id" not in st.session_state:
    st.session_state.client_id = ""

if "vendor_id" not in st.session_state:
    st.session_state.vendor_id = ""

if "api_connected" not in st.session_state:
    st.session_state.api_connected = False

# ============================================================================
# Sidebar: JWT Login (Email/Password)
# ============================================================================

st.sidebar.markdown("## 🔐 Secure Login")

if not st.session_state.jwt_token:
    st.sidebar.write("Sign in with your credentials")
    
    email_input = st.sidebar.text_input(
        "Email",
        value="",
        placeholder="admin@client.com",
        type="default"
    )
    
    password_input = st.sidebar.text_input(
        "Password",
        value="",
        placeholder="Enter your password",
        type="password"
    )
    
    if st.sidebar.button("Sign In", use_container_width=True, type="primary"):
        if email_input and password_input:
            with st.spinner("Authenticating..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/auth/login",
                        json={"email": email_input, "password": password_input},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state.jwt_token = token_data["access_token"]
                        st.session_state.user_email = email_input
                        st.session_state.user_role = token_data["role"]
                        st.session_state.client_id = token_data.get("client_id", "")
                        st.session_state.vendor_id = token_data.get("vendor_id", "")
                        st.sidebar.success(f"✅ Logged in as {token_data['role']}")
                        st.rerun()
                    elif response.status_code == 401:
                        st.sidebar.error("❌ Invalid email or password")
                    else:
                        st.sidebar.error(f"❌ Login failed (Status: {response.status_code})")
                except requests.exceptions.ConnectionError:
                    st.sidebar.error("❌ Cannot connect to API")
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
        else:
            st.sidebar.warning("Please enter email and password")
else:
    # User is logged in
    st.sidebar.markdown(f"**👤 {st.session_state.user_email}**")
    st.sidebar.write(f"Role: `{st.session_state.user_role}`")
    if st.session_state.client_id:
        st.sidebar.write(f"Client ID: `{st.session_state.client_id[:8]}...`")
    
    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.jwt_token = ""
        st.session_state.user_email = ""
        st.session_state.user_role = ""
        st.session_state.client_id = ""
        st.session_state.vendor_id = ""
        st.sidebar.success("✅ Signed out")
        st.rerun()

# ============================================================================
# Sidebar: API Health Check
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏥 API Health")

if st.sidebar.button("Check API Health", use_container_width=True):
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            st.session_state.api_connected = True
            st.sidebar.success(f"✅ API Connected\n{health_data['service']}")
        else:
            st.session_state.api_connected = False
            st.sidebar.error(f"❌ API Error (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        st.session_state.api_connected = False
        st.sidebar.error("❌ Cannot connect to API\nEnsure backend is running on port 8000")
    except Exception as e:
        st.session_state.api_connected = False
        st.sidebar.error(f"❌ Error: {str(e)}")

# Display current status
if st.session_state.api_connected:
    st.sidebar.info("🟢 API is reachable")
else:
    st.sidebar.warning("🔴 API status unknown (click Check API Health)")

# ============================================================================
# Main Header
# ============================================================================

st.title(f"🚗 {PAGE_TITLE}")
st.write("A multi-tenant billing platform for fleet management")

# ============================================================================
# Authentication Check
# ============================================================================

if not st.session_state.jwt_token:
    st.warning("⚠️ Please sign in using your email and password in the sidebar.")
    st.stop()

st.success(f"✅ Logged in as: **{st.session_state.user_email}** | Role: **{st.session_state.user_role}**")

# ============================================================================
# Tab Navigation
# ============================================================================

# Initialize tab variables to None
tab_calculator = None
tab_contract = None
tab_analytics = None
tab_monitor = None
tab_admin = None
tab_reports = None

if st.session_state.user_role == "SUPER_ADMIN":
    tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_admin, tab_reports = st.tabs(
        ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "⚙️ Admin Config", "📄 Billing Reports"]
    )
elif st.session_state.user_role == "CLIENT_ADMIN":
    tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_reports = st.tabs(
        ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "📄 Billing Reports"]
    )
else: # VIEWER
    tab_contract, tab_analytics, tab_reports = st.tabs(
        ["📋 Contract Viewer", "📊 Analytics", "📄 Billing Reports"]
    )

# ============================================================================
# TAB 1: Billing Calculator
# ============================================================================

if tab_calculator:
    with tab_calculator:
        st.header("💰 Billing Calculator")
        st.write("Enter a Trip ID to calculate the billing cost based on your contract.")
        
        trip_id_input = st.text_input(
            "Trip ID",
            value="d0000000-0000-0000-0000-000000000001",
            placeholder="Enter the trip UUID",
            key="trip_id_input"
        )
        # Carpool checkbox
        carpool_checked = st.checkbox("Is Carpool?", value=False, key="carpool")

        if st.button("Calculate Billing", type="primary", use_container_width=True, key="calc_button"):
            if not trip_id_input:
                st.error("Please enter a Trip ID")
            elif not st.session_state.api_connected:
                st.error("❌ API is not connected. Please check API Health first.")
            else:
                is_carpool_flag = st.session_state.get('carpool', False)

                with st.spinner("Fetching billing data..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                        response = requests.get(
                            f"{API_BASE_URL}/secure/billing/{trip_id_input}",
                            headers=headers,
                            params={"is_carpool": str(is_carpool_flag).lower()},
                            timeout=5
                        )

                        if response.status_code == 200:
                            billing_data = response.json()

                            # Display results (metrics)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Billing Model", billing_data.get("billing_model", "N/A"))
                            with col2:
                                st.metric("Base Cost", f"₹{billing_data.get('base_cost', 0):.2f}")
                            with col3:
                                st.metric("Total Cost", f"₹{billing_data.get('total_cost', 0):.2f}",
                                          delta=f"Tax: ₹{billing_data.get('tax_amount', 0):.2f}")

                            # Employee incentive metric
                            emp_earnings = billing_data.get('employee_incentive', 0.0)
                            st.metric("Employee Earnings", f"₹{emp_earnings:.2f}")

                            # Full breakdown
                            st.subheader("Billing Breakdown")
                            st.json(billing_data)
                            
                        elif response.status_code == 400:
                            st.error("❌ Bad Request: Invalid Client ID or Trip ID")
                        elif response.status_code == 404:
                            st.error("❌ Trip not found in database")
                        else:
                            st.error(f"❌ API Error (Status: {response.status_code})\n{response.text}")
                            
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timeout. Backend may be slow.")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to API")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: Contract Viewer
# ============================================================================

if tab_contract:
    with tab_contract:
        st.header("📋 Contract Viewer")
        st.write("View the billing rules and contract details for your organization.")
        
        if st.button("Load Contract", type="primary", use_container_width=True, key="contract_button"):
            if not st.session_state.api_connected:
                st.error("❌ API is not connected. Please check API Health first.")
            else:
                with st.spinner("Fetching contract..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                        response = requests.get(
                            f"{API_BASE_URL}/secure/contracts",
                            headers=headers,
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            contract_data = response.json()
                            
                            # Display key information
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Contract ID", contract_data.get("contract_id", "N/A")[:8] + "...")
                            
                            with col2:
                                st.metric("Vendor ID", contract_data.get("vendor_id", "N/A")[:8] + "...")
                            
                            st.subheader("Billing Model")
                            st.info(contract_data.get("billing_model", "N/A"))
                            
                            st.subheader("Billing Rules Configuration")
                            st.json(contract_data.get("rules_config", {}))
                            
                        elif response.status_code == 400:
                            st.error("❌ Invalid Client ID")
                        else:
                            st.error(f"❌ API Error (Status: {response.status_code})\n{response.text}")
                            
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timeout.")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to API")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 3: Analytics & Visuals
# ============================================================================

if tab_analytics:
    with tab_analytics:
        st.header("📊 Analytics Dashboard")
        st.write("Billing insights and trends for your organization.")
        
        if not st.session_state.api_connected:
            st.error("❌ API is not connected. Please check API Health first.")
        else:
            with st.spinner("Fetching analytics data..."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                    response = requests.get(
                        f"{API_BASE_URL}/secure/billing/stats",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        raw_data = response.json()
                        if not raw_data:
                            st.info("No trip data available yet.")
                        else:
                            df = pd.DataFrame(raw_data)
                            
                            # Filter out error rows
                            df = df[df['status'] == 'SUCCESS']
                            
                            if df.empty:
                                st.warning("No successful trips to analyze.")
                            else:
                                # Convert columns
                                df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0)
                                df['distance_km'] = pd.to_numeric(df['distance_km'], errors='coerce').fillna(0)
                                df['start_time'] = pd.to_datetime(df['start_time'], format='ISO8601')
                                df['date'] = df['start_time'].dt.date

                                # KPI Metrics
                                total_spend = df['total_cost'].sum()
                                avg_cost = df['total_cost'].mean()
                                total_trips = len(df)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Spend", f"₹{total_spend:,.2f}")
                                with col2:
                                    st.metric("Avg Cost / Trip", f"₹{avg_cost:,.2f}")
                                with col3:
                                    st.metric("Total Trips", total_trips)
                                
                                st.divider()
                                
                                # Charts
                                col_chart1, col_chart2 = st.columns(2)
                                
                                with col_chart1:
                                    st.subheader("Daily Spend")
                                    daily_spend = df.groupby('date')['total_cost'].sum()
                                    st.bar_chart(daily_spend)
                                    
                                with col_chart2:
                                    st.subheader("Billing Model Distribution")
                                    model_counts = df['billing_model'].value_counts()
                                    st.bar_chart(model_counts)

                                st.divider()
                                st.subheader("Recent Trips")
                                st.dataframe(
                                    df[['trip_id', 'start_time', 'distance_km', 'billing_model', 'total_cost']]
                                    .sort_values('start_time', ascending=False)
                                    .head(50),
                                    use_container_width=True
                                )

                    else:
                        st.error(f"❌ Failed to fetch stats (Status: {response.status_code})")
                        
                except Exception as e:
                    st.error(f"❌ Error fetching analytics: {str(e)}")


# ============================================================================
# TAB: Billing Reports
# ============================================================================

if tab_reports:
    with tab_reports:
        st.header("📄 Billing Reports")
        st.write("Generate and download detailed billing reports for your organization.")
        
        st.info("This report includes all trips for your client account, calculated with your specific contract rules.")

        st.subheader("Download Client Report")
        st.write("Generate a CSV of all trips for your client. This uses the same billing logic as the single-trip calculator.")

        if st.button("Download CSV Report", use_container_width=True):
            if not st.session_state.api_connected:
                st.error("❌ API is not connected. Please check API Health first.")
            else:
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                    resp = requests.get(f"{API_BASE_URL}/secure/billing/export-csv", headers=headers, timeout=30)
                    if resp.status_code == 200:
                        csv_bytes = resp.content
                        
                        # Extract filename from Content-Disposition header if available
                        content_disposition = resp.headers.get("Content-Disposition", "")
                        if "filename=" in content_disposition:
                            filename = content_disposition.split("filename=")[1].strip('"')
                        else:
                            # Fallback if header missing
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"billing_report_{st.session_state.client_id}_{timestamp}.csv"

                        st.download_button(
                            label="Click to save CSV", 
                            data=csv_bytes, 
                            file_name=filename,
                            mime="text/csv"
                        )
                    else:
                        st.error(f"Failed to generate report (status {resp.status_code}): {resp.text}")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. Generating the report may take too long.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 4: System Monitor
# ============================================================================

if tab_monitor:
    with tab_monitor:
        # Render counter to verify refresh executions
        render_counter = st.session_state.get("render_cnt", 0) + 1
        st.session_state.render_cnt = render_counter
        st.caption(f"🔄 render #{render_counter} at {datetime.now():%H:%M:%S}")
        st.header("🖥️ System Monitor")
        st.write("Real-time system performance metrics.")
        
        # System Metrics
        col1, col2 = st.columns(2)
        with col1:
            cpu_usage = psutil.cpu_percent(interval=1)
            st.metric("CPU Usage", f"{cpu_usage}%")
            st.progress(cpu_usage / 100)
            
        with col2:
            mem = psutil.virtual_memory()
            st.metric("RAM Usage", f"{mem.percent}%")
            st.progress(mem.percent / 100)
        
        # Refresh button
        if st.button("🔄 Refresh Metrics", use_container_width=True):
            st.rerun()
        
        st.info("💡 Click 'Refresh Metrics' to update CPU and RAM usage.")
            
        st.divider()
        st.subheader("Backend Logs")
        
        log_file_path = Path(__file__).resolve().parent.parent / "Phase 3 - APIs" / "moveinsync_app.log"
        
        try:
            if not log_file_path.exists():
                st.warning(f"Log file not found: {log_file_path}")
            else:
                # Read the entire log file
                raw_text = log_file_path.read_text(encoding="utf-8", errors="ignore")
                lines = raw_text.splitlines()
                
                # Always show the last 150 log lines
                last_n = 150
                last_lines = lines[-last_n:] if lines else ["(Log is empty)"]
                
                # File info
                stats = log_file_path.stat()
                st.caption(
                    f"Showing last {len(last_lines)} log lines (auto-updated on tab load) | "
                    f"File size: {stats.st_size:,} bytes | "
                    f"Modified: {datetime.fromtimestamp(stats.st_mtime):%Y-%m-%d %H:%M:%S}"
                )
                
                # Display logs
                st.text_area(
                    "Log Output",
                    value="\n".join(last_lines),
                    height=400
                )
                
        except Exception as e:
            st.error(f"Unable to read log file: {e}")

# ============================================================================
# TAB 5: Admin Config (SUPER_ADMIN only)
# ============================================================================

if st.session_state.user_role == "SUPER_ADMIN" and tab_admin:
    with tab_admin:
        st.header("⚙️ Admin Configuration")
        st.write("Super Admin panel for system configuration and user management.")
        
        st.subheader("📝 Create New User")
        st.write("Add a new user to the system with specific role and tenant assignment.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", placeholder="user@example.com")
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
            new_role = st.selectbox(
                "Role",
                ["SUPER_ADMIN", "CLIENT_ADMIN", "VENDOR_ADMIN", "VIEWER"],
                index=1
            )
        
        with col2:
            new_client_id = st.text_input(
                "Client ID (Optional)",
                placeholder="c0000000-0000-0000-0000-000000000001",
                help="Leave empty for SUPER_ADMIN"
            )
            new_vendor_id = st.text_input(
                "Vendor ID (Optional)",
                placeholder="v0000000-0000-0000-0000-000000000001",
                help="Only for VENDOR_ADMIN"
            )
        
        if st.button("Create User", type="primary", use_container_width=True):
            if not new_email or not new_password:
                st.error("Email and password are required")
            else:
                with st.spinner("Creating user..."):
                    try:
                        user_data = {
                            "email": new_email,
                            "password": new_password,
                            "role": new_role,
                            "client_id": new_client_id if new_client_id else None,
                            "vendor_id": new_vendor_id if new_vendor_id else None,
                        }
                        
                        headers = {"Authorization": f"Bearer {st.session_state.jwt_token}"}
                        response = requests.post(
                            f"{API_BASE_URL}/admin/users",
                            json=user_data,
                            headers=headers,
                            timeout=5
                        )
                        
                        if response.status_code == 201:
                            st.success(f"✅ User created: {new_email}")
                        elif response.status_code == 403:
                            st.error("❌ Forbidden: Only SUPER_ADMIN can create users")
                        elif response.status_code == 400:
                            st.error(f"❌ Invalid input: {response.json().get('detail', '')}")
                        else:
                            st.error(f"❌ Failed to create user (Status: {response.status_code})")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to API")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        st.subheader("📊 System Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Your Role", st.session_state.user_role)
        
        with col2:
            st.metric("Logged In As", st.session_state.user_email)
        
        with col3:
            st.metric("Scope", "System-Wide")
        
        st.info("💡 As a SUPER_ADMIN, you have access to all tenant data and can configure the system globally.")

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown(
    """
    **MoveInSync Billing Platform** | Phase 4 UI
    
    Built with Streamlit | Connected to FastAPI Backend
    """
)
