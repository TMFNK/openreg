"""
OpenReg Regulatory Dashboard
Run: streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="OpenReg Dashboard", layout="wide")
st.title("🏦 OpenReg: Regulatory & Controlling Dashboard")

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

# Charts
tab1, tab2, tab3 = st.tabs(["FINREP", "COREP", "Controlling"])

with tab1:
    fig = px.bar(finrep_data, x='sector', y='exposure_amount', color='credit_quality_bucket',
                 title="FINREP F18: Credit Quality by Sector")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.sunburst(corep_data, path=['sector', 'risk_weight'], values='rwa',
                     title="COREP: Risk-Weighted Assets Distribution")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.bar(controlling_data, x='cost_center', y='net_contribution_margin',
                 color='net_contribution_margin', title="Cost Center Profitability")
    st.plotly_chart(fig, use_container_width=True)