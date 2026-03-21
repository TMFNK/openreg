"""
OpenReg Regulatory Dashboard
Run: streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import bcrypt

# Authentication Configuration
st.set_page_config(page_title="OpenReg Dashboard", layout="wide")

# User database
USERS = {
    'regulator': {
        'password_hash': bcrypt.hashpw('regulator2024'.encode(), bcrypt.gensalt()).decode(),
        'name': 'European Central Bank Regulator',
        'role': 'regulator'
    },
    'controller': {
        'password_hash': bcrypt.hashpw('controller2024'.encode(), bcrypt.gensalt()).decode(),
        'name': 'Finance Controller',
        'role': 'controlling'
    },
    'risk_officer': {
        'password_hash': bcrypt.hashpw('risk2024'.encode(), bcrypt.gensalt()).decode(),
        'name': 'Chief Risk Officer',
        'role': 'risk'
    }
}

# Authentication function
def authenticate(username, password):
    if username in USERS:
        user = USERS[username]
        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return user['name'], user['role']
    return None, None

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_name = None

st.title("🏦 OpenReg: Regulatory & Controlling Dashboard")

# Authentication section
if not st.session_state.authenticated:
    st.header("🔐 Login Required")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            name, role = authenticate(username, password)
            if name and role:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_role = role
                st.session_state.user_name = name
                st.success(f"Welcome {name} ({role.title()})!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # Show default credentials in development
    if st.checkbox("Show default credentials (Development Only)"):
        st.write("**Default Users:**")
        st.write("- regulator / regulator2024 (Full access)")
        st.write("- controller / controller2024 (Controlling views)")
        st.write("- risk_officer / risk2024 (Risk views only)")

    st.stop()  # Stop execution if not authenticated

# Authenticated user section
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"Welcome *{st.session_state.user_name}* ({st.session_state.user_role.title() if st.session_state.user_role else 'Unknown'})")
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.session_state.user_name = None
            st.rerun()

# Connect to database
@st.cache_data
def load_data(query):
    conn = sqlite3.connect('data/processed/openreg.db')
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load KPIs
npl_ratio = load_data("SELECT * FROM kpi_npl_ratio")['npl_ratio'].iloc[0]
finrep_data = load_data("SELECT * FROM finrep_f18_credit_quality")
corep_data = load_data("SELECT * FROM corep_cr_sa_exposure")
controlling_data = load_data("SELECT * FROM controlling_cost_center_profit")

# Dashboard
col1, col2, col3 = st.columns(3)
col1.metric("NPL Ratio", f"{npl_ratio:.2%}", delta="0.2%")
col2.metric("Total RWA", f"€{corep_data['rwa'].sum()/1e9:.1f}B")
col3.metric("Active Loans", f"{len(load_data('SELECT * FROM v_loans_regulator')):,}")

# Role-based access control for views
user_role = st.session_state.user_role

# Define available tabs based on user role
available_tabs = []

if user_role == 'regulator':
    # Regulators get full access
    available_tabs = ["FINREP", "COREP", "Controlling", "Risk"]
elif user_role == 'controlling':
    # Controllers see controlling and partially regulated views
    available_tabs = ["FINREP", "Controlling"]
else:  # risk role
    # Risk officers see only risk-related views
    available_tabs = ["Risk"]

# Create tabs dynamically based on role
tabs = st.tabs(available_tabs)

tab_index = 0

# Regulator and Controlling can see FINREP
if "FINREP" in available_tabs:
    with tabs[tab_index]:
        st.subheader("🏛️ FINREP F18: Credit Quality Analysis")
        fig = px.bar(finrep_data, x='sector', y='exposure_amount', color='credit_quality_bucket',
                     title="Credit Quality by Sector", barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

        # Additional FINREP metrics
        if user_role == 'regulator':
            with st.expander("📊 Detailed FINREP Metrics"):
                st.dataframe(finrep_data.style.format({
                    'exposure_amount': '{:,.0f}',
                    'avg_ltv': '{:.1%}',
                    'rwa': '{:,.0f}'
                }))
    tab_index += 1

# Regulators see COREP
if "COREP" in available_tabs and user_role == 'regulator':
    with tabs[tab_index]:
        st.subheader("🏦 COREP CR SA: Risk-Weighted Assets")
        fig = px.sunburst(corep_data, path=['sector', 'risk_weight'], values='rwa',
                         title="RWA Distribution by Sector and Risk Weight")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📈 RWA Breakdown"):
            st.dataframe(corep_data.style.format({
                'ead_pre_crm': '{:,.0f}',
                'ead_post_crm': '{:,.0f}',
                'rwa': '{:,.0f}'
            }))
    tab_index += 1

# Controlling and Regulators see Controlling views
if "Controlling" in available_tabs:
    with tabs[tab_index]:
        st.subheader("💼 Cost Center Controlling")
        fig = px.bar(controlling_data, x='cost_center', y='net_contribution_margin',
                     color='net_contribution_margin',
                     title="Cost Center Profitability",
                     color_continuous_scale=['red', 'yellow', 'green'])
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📊 Cost Center Details"):
            def get_style(v):
                if not isinstance(v, str):
                    return ''
                try:
                    cleaned = v.replace(',', '').replace('€', '').replace('%', '')
                    if cleaned:  # Check if non-empty after cleaning
                        return 'background-color: #ffcccc' if float(cleaned) < 0 else ''
                except (ValueError, TypeError):
                    pass
                return ''

            st.dataframe(controlling_data.style.format({
                'loan_volume': '{:,.0f}',
                'interest_income': '{:,.0f}',
                'expected_loss': '{:,.0f}',
                'net_contribution_margin': '{:,.0f}'
            }).apply(lambda x: [get_style(v) for v in x], axis=1))
    tab_index += 1

# Risk officers and Regulators get risk-specific views
if "Risk" in available_tabs:
    with tabs[tab_index]:
        st.subheader("⚠️ Risk Management Dashboard")

        # NPL Analysis
        st.metric("Non-Performing Loan Ratio", f"{npl_ratio:.2%}")

        # Risk-sensitive metrics
        risk_data = load_data("""
            SELECT sector,
                   AVG(pd_rating) as avg_pd,
                   AVG(lgd) as avg_lgd,
                   SUM(ead * risk_weight) / SUM(ead) as weighted_avg_risk_weight
            FROM v_loans_regulator
            GROUP BY sector
            ORDER BY weighted_avg_risk_weight DESC
        """)

        fig_risk = px.bar(risk_data, x='sector', y='weighted_avg_risk_weight',
                         title="Risk Weight by Sector",
                         color='avg_pd', color_continuous_scale='Reds')
        st.plotly_chart(fig_risk, use_container_width=True)

        if user_role == 'regulator':
            with st.expander("🔍 Detailed Risk Metrics"):
                st.dataframe(risk_data.style.format({
                    'avg_pd': '{:.1%}',
                    'avg_lgd': '{:.1%}',
                    'weighted_avg_risk_weight': '{:.1%}'
                }))
