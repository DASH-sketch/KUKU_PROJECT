#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v3.0 - FIXED VERSION
8 tabs (left sidebar vertical) with demand scoring and buyer intelligence
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
# STYLING - BRIGHT COLORS FOR VISIBILITY
# ============================================================================

st.markdown("""
<style>
    body { 
        background-color: #0F172A; 
        color: #E8E8E8;
    }
    
    .main { 
        background-color: #0F172A;
    }
    
    h1, h2, h3, p, span, div {
        color: #E8E8E8 !important;
    }
    
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
# PAGE STRUCTURE WITH SIDEBAR
# ============================================================================

st.sidebar.markdown("# 🐔 KUKU DASHBOARD")
st.sidebar.markdown("---")

# Tab selection in sidebar
tab_selection = st.sidebar.radio(
    "NAVIGATION",
    [
        "📊 Overview",
        "💡 Insights",
        "💰 Financial",
        "📈 Trends",
        "💵 Summary",
        "⚙️ Operations",
        "📄 Statements",
        "📊 Market Intelligence"
    ]
)

st.sidebar.markdown("---")

# Batch selector in sidebar
batches = fetch_data("SELECT batchid, batchname, quantitychicksstarted, datestarted, dateended, status FROM batches_detailed ORDER BY datestarted DESC")

if batches.empty:
    st.error("❌ No batches found. Create a batch first.")
    st.stop()

batch_names = [f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds)" for _, b in batches.iterrows()]
selected_idx = st.sidebar.selectbox("Select Batch", range(len(batches)), format_func=lambda i: batch_names[i])
selected_batch = batches.iloc[selected_idx]

batch_id = int(selected_batch['batchid'])
batch_size = int(selected_batch['quantitychicksstarted']) or 800
batch_start = selected_batch['datestarted']

# ============================================================================
# FETCH DATA
# ============================================================================

batch_sales = fetch_data("SELECT * FROM daily_sales WHERE batchid = %s ORDER BY datesold", [batch_id])
batch_expenses = fetch_data("SELECT * FROM expenses WHERE batchid = %s OR batchid IS NULL ORDER BY expensedate", [batch_id])
batch_weights = fetch_data("SELECT * FROM weight_sessions WHERE batchid = %s ORDER BY sessiondate", [batch_id])
batch_mortality = fetch_data("SELECT * FROM daily_mortality WHERE batchid = %s ORDER BY daterecorded", [batch_id])
batch_feed = fetch_data("SELECT * FROM daily_feed_log WHERE batchid = %s ORDER BY datefed", [batch_id])
batch_events = fetch_data("SELECT * FROM critical_events WHERE batchid = %s ORDER BY eventdate", [batch_id])

# ============================================================================
# CALCULATIONS
# ============================================================================

def get_metrics():
    """Calculate metrics - returns dict with all keys"""
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
    
    # Demand score
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
# HEADER
# ============================================================================

st.markdown("# 🐔 KUKU FARM DASHBOARD")
st.markdown("*Real-time farm management with demand intelligence*")
st.divider()

# ============================================================================
# TAB: OVERVIEW
# ============================================================================

if tab_selection == "📊 Overview":
    st.markdown("## 📊 Performance Overview")
    
    status_color = "🟢" if metrics['demand_score'] >= 70 else "🟡" if metrics['demand_score'] >= 60 else "🔴"
    
    st.success(f"""
    **📊 Market Demand: {metrics['demand_score']}/100 {status_color}**
    
    Outcome: {metrics['outcome']}/60 | Structure: {metrics['structure']}/40
    
    Concentration Risk: {metrics['concentration']:.1f}% (Top 3 buyers)
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

# ============================================================================
# TAB: INSIGHTS
# ============================================================================

elif tab_selection == "💡 Insights":
    st.markdown("## 💡 Actionable Insights")
    
    if metrics['concentration'] > 75:
        st.error(f"🔴 **DANGEROUS: {metrics['concentration']:.0f}% from top 3 buyers!**\n\nIf 1 buyer stops → lose 25% revenue. ACTION: Diversify immediately!")
    elif metrics['concentration'] > 60:
        st.warning(f"🟡 **HIGH CONCENTRATION: {metrics['concentration']:.0f}%**\n\nTop 3 buyers carry business. Need to diversify.")
    else:
        st.success(f"🟢 **HEALTHY: {metrics['concentration']:.0f}%**\n\nGood buyer distribution. Can scale confidently.")
    
    st.divider()
    
    if metrics['demand_score'] >= 80:
        st.success("✅ **STRONG DEMAND** — Score 80+. Market responding excellently.")
    elif metrics['demand_score'] >= 70:
        st.info("🟡 **GOOD DEMAND** — Score 70+. Market is solid.")
    else:
        st.error("🔴 **WEAK DEMAND** — Score <70. Monitor and improve before scaling.")

# ============================================================================
# TAB: FINANCIAL
# ============================================================================

elif tab_selection == "💰 Financial":
    st.markdown("## 💰 Financial-Performance Link")
    
    fcr_table = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Feed Cost/Bird': ['TZS 1,804', 'TZS 1,968', 'TZS 2,165', 'TZS 2,296', 'TZS 2,378'],
        'Total Cost/Bird': ['TZS 5,104', 'TZS 5,268', 'TZS 5,465', 'TZS 5,596', 'TZS 5,678'],
        'Profit/Bird': ['TZS 1,696', 'TZS 1,532', 'TZS 1,335', 'TZS 1,204', 'TZS 1,122'],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    st.dataframe(fcr_table, use_container_width=True, hide_index=True)
    
    st.info("**Each 0.1 FCR improvement = +TZS 197 profit per bird**\n\nOn 800 birds = TZS 157,600 extra profit per batch!")

# ============================================================================
# TAB: TRENDS
# ============================================================================

elif tab_selection == "📈 Trends":
    st.markdown("## 📈 Batch Performance Trends")
    
    if not batch_weights.empty:
        st.markdown("### Weight Sessions")
        st.dataframe(batch_weights[['sessiondate', 'dayofcycle', 'batchsize', 'samplesize']].head(10), use_container_width=True)
    else:
        st.info("No weight data yet")
    
    st.divider()
    
    if not batch_events.empty:
        st.markdown("### Critical Events Log")
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity', 'description']].head(10), use_container_width=True)
    else:
        st.info("No critical events")

# ============================================================================
# TAB: SUMMARY
# ============================================================================

elif tab_selection == "💵 Summary":
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

# ============================================================================
# TAB: OPERATIONS
# ============================================================================

elif tab_selection == "⚙️ Operations":
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
    else:
        st.info("No mortality records")

# ============================================================================
# TAB: STATEMENTS
# ============================================================================

elif tab_selection == "📄 Statements":
    st.markdown("## 📄 Financial Statements")
    
    st.success(f"""
    **INCOME STATEMENT**
    
    **REVENUE**
    - Bird Sales: TZS {metrics['total_revenue']:,}
    
    **EXPENSES**
    - Total: TZS {metrics['total_expenses']:,}
    
    **NET PROFIT: TZS {metrics['profit']:,}**
    
    **Margin: {metrics['margin']:.1f}%**
    """)

# ============================================================================
# TAB: MARKET INTELLIGENCE
# ============================================================================

elif tab_selection == "📊 Market Intelligence":
    st.markdown("## 📊 Market Intelligence - Buyer Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🧑 Active Buyers", metrics['unique_buyers'])
    with col2:
        st.metric("⚠️ Concentration", f"{metrics['concentration']:.0f}%")
    with col3:
        st.metric("📊 Demand Score", metrics['demand_score'])
    with col4:
        st.metric("📞 Reliability", "70%")
    
    st.divider()
    
    if metrics['concentration'] > 75:
        st.error(f"🔴 **CRITICAL CONCENTRATION: {metrics['concentration']:.0f}%**\n\nTop 3 buyers = your entire business. One buyer loss = collapse. URGENT ACTION NEEDED!")
    elif metrics['concentration'] > 60:
        st.warning(f"🟡 **HIGH CONCENTRATION: {metrics['concentration']:.0f}%**\n\nToo dependent on few buyers. Diversify needed.")
    else:
        st.success(f"🟢 **HEALTHY: {metrics['concentration']:.0f}%**\n\nGood distribution. You have real demand.")
    
    st.divider()
    
    st.markdown("### Buyer Summary")
    if not batch_sales.empty:
        buyer_data = batch_sales.groupby('buyername').agg({
            'quantitysold': 'sum',
            'totalrevenue': 'sum'
        }).sort_values('quantitysold', ascending=False).reset_index()
        
        buyer_data.columns = ['Buyer Name', 'Birds Sold', 'Revenue']
        st.dataframe(buyer_data, use_container_width=True, hide_index=True)
    else:
        st.info("No sales data")
    
    st.divider()
    
    st.markdown("### 🎯 Strategic Actions")
    remaining_to_target = max(0, 10 - metrics['unique_buyers'])
    st.markdown(f"""
    **BEFORE NEXT BATCH:**
    - Call top 3 buyers → confirm orders
    - Offer loyalty discount/incentive
    
    **NEXT 3 BATCHES:**
    - Find {remaining_to_target} new small buyers
    - Current: {metrics['unique_buyers']} buyers → Target: 10+ buyers
    - Reduce concentration: {metrics['concentration']:.0f}% → Target: <50%
    
    **SUCCESS METRICS:**
    - Score: 70+ (currently {metrics['demand_score']})
    - Buyers: 10+
    - Concentration: <50%
    - Then: SCALE CONFIDENTLY ✅
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#A0A0A0; font-size:12px;">
🐔 KUKU Farm Dashboard v3.0 | Real-time with demand intelligence
</p>
""", unsafe_allow_html=True)
