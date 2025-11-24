def verify_rbac_logic():
    print("Testing RBAC Logic...")
    
    # Mock st.tabs
    def mock_tabs(names):
        return [f"Tab: {name}" for name in names]
    
    class MockSt:
        def tabs(self, names):
            return mock_tabs(names)
        
    st = MockSt()
    
    # Test SUPER_ADMIN
    print("\n--- SUPER_ADMIN ---")
    user_role = "SUPER_ADMIN"
    tab_calculator = None
    tab_contract = None
    tab_analytics = None
    tab_monitor = None
    tab_admin = None
    tab_reports = None

    if user_role == "SUPER_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_admin, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "⚙️ Admin Config", "📄 Billing Reports"]
        )
    elif user_role == "CLIENT_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "📄 Billing Reports"]
        )
    else: # VIEWER
        tab_contract, tab_analytics, tab_reports = st.tabs(
            ["📋 Contract Viewer", "📊 Analytics", "📄 Billing Reports"]
        )
        
    print(f"Calculator: {tab_calculator}")
    print(f"Contract: {tab_contract}")
    print(f"Analytics: {tab_analytics}")
    print(f"Monitor: {tab_monitor}")
    print(f"Admin: {tab_admin}")
    print(f"Reports: {tab_reports}")
    
    if all([tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_admin, tab_reports]):
        print("✅ SUPER_ADMIN has all tabs")
    else:
        print("❌ SUPER_ADMIN missing tabs")

    # Test CLIENT_ADMIN
    print("\n--- CLIENT_ADMIN ---")
    user_role = "CLIENT_ADMIN"
    tab_calculator = None
    tab_contract = None
    tab_analytics = None
    tab_monitor = None
    tab_admin = None
    tab_reports = None

    if user_role == "SUPER_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_admin, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "⚙️ Admin Config", "📄 Billing Reports"]
        )
    elif user_role == "CLIENT_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "📄 Billing Reports"]
        )
    else: # VIEWER
        tab_contract, tab_analytics, tab_reports = st.tabs(
            ["📋 Contract Viewer", "📊 Analytics", "📄 Billing Reports"]
        )
        
    print(f"Calculator: {tab_calculator}")
    print(f"Contract: {tab_contract}")
    print(f"Analytics: {tab_analytics}")
    print(f"Monitor: {tab_monitor}")
    print(f"Admin: {tab_admin}")
    print(f"Reports: {tab_reports}")
    
    if all([tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_reports]) and tab_admin is None:
        print("✅ CLIENT_ADMIN has correct tabs (No Admin)")
    else:
        print("❌ CLIENT_ADMIN tab mismatch")

    # Test VIEWER
    print("\n--- VIEWER ---")
    user_role = "VIEWER"
    tab_calculator = None
    tab_contract = None
    tab_analytics = None
    tab_monitor = None
    tab_admin = None
    tab_reports = None

    if user_role == "SUPER_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_admin, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "⚙️ Admin Config", "📄 Billing Reports"]
        )
    elif user_role == "CLIENT_ADMIN":
        tab_calculator, tab_contract, tab_analytics, tab_monitor, tab_reports = st.tabs(
            ["💰 Billing Calculator", "📋 Contract Viewer", "📊 Analytics", "🖥️ System Monitor", "📄 Billing Reports"]
        )
    else: # VIEWER
        tab_contract, tab_analytics, tab_reports = st.tabs(
            ["📋 Contract Viewer", "📊 Analytics", "📄 Billing Reports"]
        )
        
    print(f"Calculator: {tab_calculator}")
    print(f"Contract: {tab_contract}")
    print(f"Analytics: {tab_analytics}")
    print(f"Monitor: {tab_monitor}")
    print(f"Admin: {tab_admin}")
    print(f"Reports: {tab_reports}")
    
    if all([tab_contract, tab_analytics, tab_reports]) and tab_calculator is None and tab_monitor is None and tab_admin is None:
        print("✅ VIEWER has correct tabs (No Calc, No Monitor, No Admin)")
    else:
        print("❌ VIEWER tab mismatch")

if __name__ == "__main__":
    verify_rbac_logic()
