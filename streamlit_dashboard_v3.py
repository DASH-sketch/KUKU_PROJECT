#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v4.0
Icon-only sidebar + Multi-batch comparison + Date range selector + No twitching
"""

import streamlit as st
import psycopg2
from datetime import datetime, date, timedelta
import pandas as pd
import os

st.set_page_config(
    page_title="KUKU Farm Dashboard",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLING - Icon Sidebar + Modern Design
# ============================================================================

st.markdown("""
<style>
    /* Main background */
    body { 
        background-color: #0F172A; 
        color: #E8E8E8;
    }
    
    .main { 
        background-color: #0F172A;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #080F1E;
        width: 100px;
    }
    
    /* Icon buttons */
    .icon-btn {
        width: 60px;
        height: 60px;
        margin: 8px auto;
        background: transparent;
        border: 1px solid #334155;
        border-radius: 12px;
        color: #E8E8E8;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .icon-btn:hover {
        border-color: #10B981;
        color: #10B981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .icon-btn.active {
        background: linear-gradient(135deg, #064E3B, #065F46);
        border-color: #10B981;
        color: #10B981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }
    
    /* Text */
    h1, h2, h3, p, span, label, div {
        color: #E8E8E8 !important;
    }
    
    /* Metrics */
    .stMetric {
        background: linear-gradient(135deg, #1E293B, #162032);
        border-radius: 12px;
        padding: 15px;
        border-left: 3px solid #10B981;
    }
    
    [data-testid="stMetricValue"] { 
        color: #10B981 !important;
        font-size: 28px !important;
    }
    
    /* Tables - prevent twitching */
    .stDataFrame {
        background: #1E293B;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* Selectbox */
    .stSelectbox, .stMultiSelect, .stSlider {
        background: #1E293B;
    }
</style>

<div style="display:none" id="icon-buttons">
    <style>
        button[kind="primary"] { background: transparent; border: none; }
        button[kind="primary"]:hover { background: transparent; }
    </style>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE
# ============================================================================

@st.cache_resource
def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def fresh_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@st.cache_data(ttl=300)
def fetch_data(query, params=None):
    try:
        conn = fresh_conn()
        cur = conn.cursor()
        if params:
            params = [int(p) if isinstance(p, (int, float)) else p for p in params]
        cur.execute(query, params or [])
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        conn.close()
        return pd.DataFrame(data, columns=columns) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# SESSION STATE
# ============================================================================

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'overview'

if 'selected_batches' not in st.session_state:
    st.session_state.selected_batches = []

# ============================================================================
# SIDEBAR - ICON NAVIGATION
# ============================================================================

with st.sidebar:
    st.markdown("<div style='text-align:center; margin-bottom:20px;'>🐔</div>", unsafe_allow_html=True)
    st.divider()
    
    # Icon buttons for navigation
    tabs = [
        ('overview', '📊'),
        ('insights', '💡'),
        ('financial', '💰'),
        ('trends', '📈'),
        ('summary', '💵'),
        ('operations', '⚙️'),
        ('statements', '📄'),
        ('intelligence', '🧠')
    ]
    
    cols = st.columns([1])
    for tab_id, icon in tabs:
        if st.button(icon, key=f"nav_{tab_id}", use_container_width=True):
            st.session_state.current_tab = tab_id

# ============================================================================
# HEADER
# ============================================================================

col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.markdown("")

with col2:
    st.markdown("# 🐔 KUKU FARM DASHBOARD")
    st.markdown("*Real-time farm management with demand intelligence*")

with col3:
    st.markdown("")

st.divider()

# ============================================================================
# CONTROLS - Multi-Batch Selection + Date Range
# ============================================================================

control_col1, control_col2 = st.columns(2)

with control_col1:
    all_batches = fetch_data("SELECT batchid, batchname, quantitychicksstarted, datestarted FROM batches_detailed ORDER BY datestarted DESC")
    
    batch_options = {f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds)": int(b['batchid']) for _, b in all_batches.iterrows()}
    
    selected_batch_names = st.multiselect(
        "📦 Compare Batches",
        list(batch_options.keys()),
        default=list(batch_options.keys())[:1] if batch_options else []
    )
    selected_batch_ids = [batch_options[name] for name in selected_batch_names]

with control_col2:
    date_range = st.slider(
        "📅 Date Range",
        value=(datetime.now() - timedelta(days=30)).date(),
        min_value=(datetime.now() - timedelta(days=365)).date(),
        max_value=datetime.now().date()
    )

st.divider()

# ============================================================================
# FETCH DATA FOR SELECTED BATCHES
# ============================================================================

if not selected_batch_ids:
    st.warning("Select at least one batch to view data")
    st.stop()

batch_id_str = ','.join([str(id) for id in selected_batch_ids])

# Get batch info
batch_info = fetch_data(f"""
    SELECT * FROM batches_detailed 
    WHERE batchid IN ({batch_id_str})
    ORDER BY datestarted DESC
""")

# Get sales for selected batches
batch_sales = fetch_data(f"""
    SELECT ds.*, b.buyername 
    FROM daily_sales ds
    LEFT JOIN buyers b ON ds.buyerid = b.buyerid
    WHERE ds.batchid IN ({batch_id_str})
    AND ds.datesold >= %s
    ORDER BY ds.datesold
""", [date_range])

# Get expenses
batch_expenses = fetch_data(f"""
    SELECT * FROM expenses 
    WHERE batchid IN ({batch_id_str}) OR batchid IS NULL
    AND expensedate >= %s
    ORDER BY expensedate
""", [date_range])

# Get other data
batch_mortality = fetch_data(f"""
    SELECT * FROM daily_mortality 
    WHERE batchid IN ({batch_id_str})
    AND daterecorded >= %s
    ORDER BY daterecorded
""", [date_range])

batch_events = fetch_data(f"""
    SELECT * FROM critical_events 
    WHERE batchid IN ({batch_id_str})
    AND eventdate >= %s
    ORDER BY eventdate
""", [date_range])

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def get_metrics():
    metrics = {}
    
    if batch_sales.empty:
        return {
            'total_sold': 0,
            'total_revenue': 0,
            'total_expenses': 0,
            'profit': 0,
            'margin': 0,
            'concentration': 0,
            'unique_buyers': 0,
            'demand_score': 50,
            'avg_fcr': 1.32
        }
    
    total_sold = int(batch_sales['quantitysold'].sum())
    total_revenue = int(batch_sales['totalrevenue'].sum())
    total_expenses = int(batch_expenses['amount'].sum()) if not batch_expenses.empty else 0
    
    unique_buyers = int(batch_sales['buyerid'].nunique())
    
    buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
    if len(buyer_sales) > 0:
        top_3 = int(buyer_sales.head(3).sum())
        concentration = (top_3 / total_sold * 100) if total_sold > 0 else 0
    else:
        concentration = 0
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit': profit,
        'margin': margin,
        'concentration': concentration,
        'unique_buyers': unique_buyers,
        'demand_score': 50 + (30 if concentration < 75 else 15),
        'avg_fcr': 1.32
    }

metrics = get_metrics()

# ============================================================================
# TAB CONTENT
# ============================================================================

# TAB: OVERVIEW
if st.session_state.current_tab == 'overview':
    st.markdown("## 📊 Overview")
    
    status = "🟢" if metrics['demand_score'] >= 70 else "🟡" if metrics['demand_score'] >= 60 else "🔴"
    
    st.info(f"**Demand Score: {metrics['demand_score']}/100 {status}** • Concentration: {metrics['concentration']:.0f}%")
    
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
    m_col1.metric("🐔 Birds Sold", f"{metrics['total_sold']:,}")
    m_col2.metric("💵 Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    m_col3.metric("💸 Expenses", f"TZS {metrics['total_expenses']/1e6:.1f}M")
    m_col4.metric("🟢 Profit", f"TZS {metrics['profit']/1e6:.1f}M")
    m_col5.metric("📊 Margin", f"{metrics['margin']:.0f}%")
    m_col6.metric("👥 Buyers", metrics['unique_buyers'])

# TAB: INSIGHTS
elif st.session_state.current_tab == 'insights':
    st.markdown("## 💡 Insights")
    
    if metrics['concentration'] > 75:
        st.error(f"🔴 **CRITICAL: {metrics['concentration']:.0f}%** from top 3 buyers")
    elif metrics['concentration'] > 60:
        st.warning(f"🟡 **HIGH: {metrics['concentration']:.0f}%** concentration")
    else:
        st.success(f"🟢 **HEALTHY: {metrics['concentration']:.0f}%** distribution")

# TAB: FINANCIAL
elif st.session_state.current_tab == 'financial':
    st.markdown("## 💰 Financial Analysis")
    
    fcr_data = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40],
        'Profit/Bird': [1696, 1532, 1335, 1204],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal']
    })
    st.dataframe(fcr_data, use_container_width=True, hide_index=True)

# TAB: TRENDS
elif st.session_state.current_tab == 'trends':
    st.markdown("## 📈 Trends")
    
    if not batch_sales.empty:
        st.markdown("### Sales Over Time")
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        st.line_chart(daily_sales.set_index('datesold'), use_container_width=True)

# TAB: SUMMARY
elif st.session_state.current_tab == 'summary':
    st.markdown("## 💵 Summary")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("Total Batches", len(selected_batch_ids))
    summary_col2.metric("Total Birds", metrics['total_sold'])
    summary_col3.metric("Total Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    summary_col4.metric("Net Profit", f"TZS {metrics['profit']/1e6:.1f}M")

# TAB: OPERATIONS
elif st.session_state.current_tab == 'operations':
    st.markdown("## ⚙️ Operations")
    
    if not batch_mortality.empty:
        st.markdown("### Mortality Records")
        # Use container to prevent twitching
        with st.container():
            mort_df = batch_mortality[['daterecorded', 'quantitydied', 'reason']].copy()
            st.dataframe(mort_df, use_container_width=True, hide_index=True)

# TAB: STATEMENTS
elif st.session_state.current_tab == 'statements':
    st.markdown("## 📄 Financial Statements")
    
    st.success(f"""
    **Income Statement**
    
    Revenue: TZS {metrics['total_revenue']:,}
    Expenses: TZS {metrics['total_expenses']:,}
    **Net Profit: TZS {metrics['profit']:,}**
    Margin: {metrics['margin']:.1f}%
    """)

# TAB: MARKET INTELLIGENCE
elif st.session_state.current_tab == 'intelligence':
    st.markdown("## 🧠 Market Intelligence")
    
    int_col1, int_col2, int_col3, int_col4 = st.columns(4)
    int_col1.metric("Active Buyers", metrics['unique_buyers'])
    int_col2.metric("Concentration", f"{metrics['concentration']:.0f}%")
    int_col3.metric("Demand Score", metrics['demand_score'])
    int_col4.metric("Avg FCR", metrics['avg_fcr'])
    
    st.divider()
    
    if not batch_sales.empty:
        st.markdown("### Buyer Performance")
        with st.container():
            buyer_perf = batch_sales.groupby('buyername').agg({
                'quantitysold': 'sum',
                'totalrevenue': 'sum'
            }).sort_values('quantitysold', ascending=False).reset_index()
            buyer_perf.columns = ['Buyer', 'Birds', 'Revenue']
            st.dataframe(buyer_perf, use_container_width=True, hide_index=True)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#A0A0A0; font-size:11px;">
🐔 KUKU Farm Dashboard v4.0 | Professional Farm Intelligence System
</p>
""", unsafe_allow_html=True)
