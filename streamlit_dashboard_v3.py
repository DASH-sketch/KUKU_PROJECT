#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v3.0 - Professional Left Sidebar
8 tabs with professional styling
"""

import streamlit as st
import psycopg2
from datetime import datetime, date
import pandas as pd
import os

st.set_page_config(
    page_title="KUKU Farm Dashboard",
    page_icon="🐔",
    layout="wide"
)

# ============================================================================
# STYLING
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
    
    [data-testid="stSidebar"] {
        background-color: #080F1E;
        border-right: 1px solid #1E293B;
    }
    
    /* Text colors */
    h1, h2, h3, p, span, label, div {
        color: #E8E8E8 !important;
    }
    
    /* Tab buttons styling */
    .tab-button {
        display: block;
        width: 100%;
        padding: 12px 16px;
        margin: 6px 0;
        background: linear-gradient(135deg, #1E293B, #162032);
        border: 1px solid #334155;
        border-left: 3px solid #475569;
        border-radius: 8px;
        color: #E8E8E8;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        text-align: left;
        transition: all 0.3s;
    }
    
    .tab-button:hover {
        background: linear-gradient(135deg, #1E293B, #1E293B);
        border-left-color: #10B981;
        color: #10B981;
    }
    
    .tab-button.active {
        background: linear-gradient(135deg, #064E3B, #065F46);
        border-left: 3px solid #10B981;
        color: #10B981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
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
        font-size: 32px !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #E8E8E8 !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE
# ============================================================================

def fresh_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

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
# INITIALIZE SESSION STATE
# ============================================================================

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'overview'

# ============================================================================
# SIDEBAR - TABS + BATCH SELECTOR
# ============================================================================

with st.sidebar:
    st.markdown("# 🐔 KUKU")
    st.markdown("*Farm Dashboard*")
    st.divider()
    
    # Tab navigation
    st.markdown("### NAVIGATION")
    
    tabs_config = [
        ('overview', '📊 Overview'),
        ('insights', '💡 Insights'),
        ('financial', '💰 Financial'),
        ('trends', '📈 Trends'),
        ('summary', '💵 Summary'),
        ('operations', '⚙️ Operations'),
        ('statements', '📄 Statements'),
        ('intelligence', '📊 Market Intelligence')
    ]
    
    for tab_id, tab_label in tabs_config:
        if st.button(tab_label, key=f"tab_{tab_id}", use_container_width=True):
            st.session_state.current_tab = tab_id
    
    st.divider()
    
    # Batch selector
    st.markdown("### SELECT BATCH")
    batches = fetch_data("SELECT batchid, batchname, quantitychicksstarted, datestarted, dateended, status FROM batches_detailed ORDER BY datestarted DESC")
    
    if batches.empty:
        st.error("No batches found")
        st.stop()
    
    batch_names = [f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds)" for _, b in batches.iterrows()]
    selected_idx = st.selectbox("Batch", range(len(batches)), format_func=lambda i: batch_names[i], label_visibility="collapsed")
    selected_batch = batches.iloc[selected_idx]
    
    batch_id = int(selected_batch['batchid'])
    batch_size = int(selected_batch['quantitychicksstarted']) or 800
    batch_start = selected_batch['datestarted']

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.markdown("# 🐔 KUKU FARM DASHBOARD")
st.markdown("*Real-time farm management with demand intelligence*")
st.divider()

# ============================================================================
# FETCH DATA
# ============================================================================

batch_sales = fetch_data("""
    SELECT ds.*, b.buyername 
    FROM daily_sales ds
    LEFT JOIN buyers b ON ds.buyerid = b.buyerid
    WHERE ds.batchid = %s 
    ORDER BY ds.datesold
""", [batch_id])

batch_expenses = fetch_data("SELECT * FROM expenses WHERE batchid = %s OR batchid IS NULL ORDER BY expensedate", [batch_id])
batch_weights = fetch_data("SELECT * FROM weight_sessions WHERE batchid = %s ORDER BY sessiondate", [batch_id])
batch_mortality = fetch_data("SELECT * FROM daily_mortality WHERE batchid = %s ORDER BY daterecorded", [batch_id])
batch_feed = fetch_data("SELECT * FROM daily_feed_log WHERE batchid = %s ORDER BY datefed", [batch_id])
batch_events = fetch_data("SELECT * FROM critical_events WHERE batchid = %s ORDER BY eventdate", [batch_id])

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def get_metrics():
    total_sold = 0
    total_revenue = 0
    total_expenses = 0
    concentration = 0
    unique_buyers = 0
    
    if not batch_sales.empty:
        total_sold = int(batch_sales['quantitysold'].sum())
        total_revenue = int(batch_sales['totalrevenue'].sum())
        unique_buyers = int(batch_sales['buyerid'].nunique())
        
        buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
        if len(buyer_sales) > 0:
            top_3 = int(buyer_sales.head(3).sum())
            concentration = (top_3 / total_sold * 100) if total_sold > 0 else 0
    
    if not batch_expenses.empty:
        total_expenses = int(batch_expenses['amount'].sum())
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    outcome = 50
    structure = 30 if concentration < 75 else 15
    demand_score = outcome + structure
    
    return {
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit': profit,
        'margin': margin,
        'concentration': concentration,
        'unique_buyers': unique_buyers,
        'demand_score': int(demand_score),
        'outcome': outcome,
        'structure': structure
    }

metrics = get_metrics()

# ============================================================================
# CONTENT BY TAB
# ============================================================================

# TAB: OVERVIEW
if st.session_state.current_tab == 'overview':
    st.markdown("## 📊 Performance Overview")
    
    status_color = "🟢" if metrics['demand_score'] >= 70 else "🟡" if metrics['demand_score'] >= 60 else "🔴"
    
    st.success(f"""
    **📊 Market Demand: {metrics['demand_score']}/100 {status_color}**
    
    Outcome: {metrics['outcome']}/60 | Structure: {metrics['structure']}/40
    
    Concentration Risk: {metrics['concentration']:.1f}%
    """)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("🐔 Birds Sold", f"{metrics['total_sold']:,}")
    with col2:
        st.metric("💵 Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    with col3:
        st.metric("📊 Margin %", f"{metrics['margin']:.0f}%")
    with col4:
        avg_price = batch_sales['unitprice'].mean() if not batch_sales.empty else 0
        st.metric("💰 Avg Price", f"TZS {avg_price:,.0f}")
    with col5:
        st.metric("🌾 FCR", "1.32")
    with col6:
        mort = batch_mortality['quantitydied'].sum() if not batch_mortality.empty else 0
        mort_pct = (mort / batch_size * 100) if batch_size > 0 else 0
        st.metric("💔 Mortality", f"{mort_pct:.1f}%")

# TAB: INSIGHTS
elif st.session_state.current_tab == 'insights':
    st.markdown("## 💡 Actionable Insights")
    
    if metrics['concentration'] > 75:
        st.error(f"🔴 **DANGEROUS: {metrics['concentration']:.0f}% from top 3!**\n\nIf 1 buyer stops → lose 25% revenue. URGENT ACTION!")
    elif metrics['concentration'] > 60:
        st.warning(f"🟡 **HIGH: {metrics['concentration']:.0f}%**\n\nNeed to diversify buyers.")
    else:
        st.success(f"🟢 **HEALTHY: {metrics['concentration']:.0f}%**\n\nGood distribution.")
    
    st.divider()
    
    if metrics['demand_score'] >= 80:
        st.success("✅ **STRONG DEMAND** — Score 80+")
    elif metrics['demand_score'] >= 70:
        st.info("🟡 **GOOD DEMAND** — Score 70+")
    else:
        st.error("🔴 **WEAK DEMAND** — Score <70")

# TAB: FINANCIAL
elif st.session_state.current_tab == 'financial':
    st.markdown("## 💰 Financial-Performance Link")
    
    fcr_table = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird': ['TZS 1,696', 'TZS 1,532', 'TZS 1,335', 'TZS 1,204', 'TZS 1,122'],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    st.dataframe(fcr_table, use_container_width=True, hide_index=True)

# TAB: TRENDS
elif st.session_state.current_tab == 'trends':
    st.markdown("## 📈 Batch Performance Trends")
    
    if not batch_weights.empty:
        st.markdown("### Weight Sessions")
        st.dataframe(batch_weights[['sessiondate', 'dayofcycle']].head(10), use_container_width=True)
    
    if not batch_events.empty:
        st.markdown("### Critical Events")
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity']].head(10), use_container_width=True)

# TAB: SUMMARY
elif st.session_state.current_tab == 'summary':
    st.markdown("## 💵 Financial Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💵 Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    with col2:
        st.metric("💸 Expenses", f"TZS {metrics['total_expenses']/1e6:.1f}M")
    with col3:
        st.metric("🟢 Profit", f"TZS {metrics['profit']/1e6:.1f}M")
    with col4:
        st.metric("📊 Margin", f"{metrics['margin']:.1f}%")

# TAB: OPERATIONS
elif st.session_state.current_tab == 'operations':
    st.markdown("## ⚙️ Daily Operations")
    
    st.info(f"""
    **Batch:** {selected_batch['batchname']}
    **Birds:** {batch_size:,}
    **Started:** {batch_start}
    **Status:** {selected_batch['status']}
    """)
    
    if not batch_mortality.empty:
        st.markdown("### Mortality Log")
        st.dataframe(batch_mortality[['daterecorded', 'quantitydied', 'reason']].head(20), use_container_width=True)

# TAB: STATEMENTS
elif st.session_state.current_tab == 'statements':
    st.markdown("## 📄 Financial Statements")
    
    st.success(f"""
    **INCOME STATEMENT**
    
    Revenue: TZS {metrics['total_revenue']:,}
    Expenses: TZS {metrics['total_expenses']:,}
    
    **NET PROFIT: TZS {metrics['profit']:,}**
    **Margin: {metrics['margin']:.1f}%**
    """)

# TAB: MARKET INTELLIGENCE
elif st.session_state.current_tab == 'intelligence':
    st.markdown("## 📊 Market Intelligence")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🧑 Buyers", metrics['unique_buyers'])
    with col2:
        st.metric("⚠️ Concentration", f"{metrics['concentration']:.0f}%")
    with col3:
        st.metric("📊 Score", metrics['demand_score'])
    with col4:
        st.metric("📞 Reliability", "70%")
    
    st.divider()
    
    if metrics['concentration'] > 75:
        st.error(f"🔴 **CRITICAL: {metrics['concentration']:.0f}%**\n\nOne buyer = collapse risk!")
    elif metrics['concentration'] > 60:
        st.warning(f"🟡 **HIGH: {metrics['concentration']:.0f}%**")
    else:
        st.success(f"🟢 **HEALTHY: {metrics['concentration']:.0f}%**")
    
    st.divider()
    
    st.markdown("### Buyer Summary")
    if not batch_sales.empty:
        try:
            buyer_data = batch_sales.groupby('buyername').agg({
                'quantitysold': 'sum',
                'totalrevenue': 'sum'
            }).sort_values('quantitysold', ascending=False).reset_index()
            buyer_data.columns = ['Buyer', 'Birds', 'Revenue']
            st.dataframe(buyer_data, use_container_width=True, hide_index=True)
        except:
            st.info("Buyer data unavailable")
    
    st.markdown("### 🎯 Next Steps")
    st.markdown(f"""
    **URGENT:**
    - Call top 3 buyers → confirm orders
    - Offer loyalty incentive
    
    **STRATEGIC:**
    - Find {max(0, 10-metrics['unique_buyers'])} new small buyers
    - Reduce concentration to <50%
    - Build to 10+ buyers
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#A0A0A0; font-size:12px;">
🐔 KUKU Farm Dashboard v3.0 | Professional Edition
</p>
""", unsafe_allow_html=True)
