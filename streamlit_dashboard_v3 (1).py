#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v3.0
Icon sidebar + Multi-batch comparison + Date range selector
"""

import streamlit as st
import psycopg2
from datetime import datetime, date, timedelta
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
    body { 
        background-color: #0F172A; 
        color: #E8E8E8;
    }
    
    .main { 
        background-color: #0F172A;
    }
    
    h1, h2, h3, p, span, label, div {
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
        font-size: 28px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE
# ============================================================================

@st.cache_data(ttl=300)
def fetch_data(query, params=None):
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
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

# ============================================================================
# SIDEBAR - ICON NAVIGATION
# ============================================================================

with st.sidebar:
    st.markdown("<div style='text-align:center; margin-bottom:20px; font-size: 28px;'>🐔</div>", unsafe_allow_html=True)
    st.divider()
    
    # Navigation buttons
    nav_items = [
        ('overview', '📊 Overview'),
        ('insights', '💡 Insights'),
        ('financial', '💰 Financial'),
        ('trends', '📈 Trends'),
        ('summary', '💵 Summary'),
        ('operations', '⚙️ Operations'),
        ('statements', '📄 Statements'),
        ('intelligence', '🧠 Intelligence')
    ]
    
    for tab_id, label in nav_items:
        if st.button(label, key=f"nav_{tab_id}", use_container_width=True):
            st.session_state.current_tab = tab_id
    
    st.divider()
    
    st.markdown("### SELECT BATCHES")
    
    # Get all batches
    all_batches = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted 
        FROM batches_detailed 
        ORDER BY datestarted DESC
    """)
    
    if all_batches.empty:
        st.error("No batches found")
        st.stop()
    
    batch_options = {
        f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds)": int(b['batchid']) 
        for _, b in all_batches.iterrows()
    }
    
    selected_names = st.multiselect(
        "Batches",
        list(batch_options.keys()),
        default=list(batch_options.keys())[:1] if batch_options else [],
        label_visibility="collapsed"
    )
    
    selected_ids = [batch_options[name] for name in selected_names]
    
    st.divider()
    
    st.markdown("### DATE RANGE")
    
    selected_date = st.date_input(
        "From",
        value=datetime.now().date() - timedelta(days=30),
        min_value=datetime.now().date() - timedelta(days=365),
        max_value=datetime.now().date(),
        label_visibility="collapsed"
    )

# ============================================================================
# HEADER
# ============================================================================

st.markdown("# 🐔 KUKU FARM DASHBOARD")
st.markdown("*Real-time farm management*")
st.divider()

# ============================================================================
# CHECK SELECTION
# ============================================================================

if not selected_ids:
    st.warning("Select at least one batch in the sidebar")
    st.stop()

batch_id_str = ','.join([str(id) for id in selected_ids])

# ============================================================================
# FETCH DATA
# ============================================================================

batch_sales = fetch_data(f"""
    SELECT ds.*, b.buyername 
    FROM daily_sales ds
    LEFT JOIN buyers b ON ds.buyerid = b.buyerid
    WHERE ds.batchid IN ({batch_id_str})
    AND ds.datesold >= %s
    ORDER BY ds.datesold
""", [selected_date])

batch_expenses = fetch_data(f"""
    SELECT * FROM expenses 
    WHERE batchid IN ({batch_id_str}) OR batchid IS NULL
    AND expensedate >= %s
    ORDER BY expensedate
""", [selected_date])

batch_mortality = fetch_data(f"""
    SELECT * FROM daily_mortality 
    WHERE batchid IN ({batch_id_str})
    AND daterecorded >= %s
    ORDER BY daterecorded
""", [selected_date])

batch_events = fetch_data(f"""
    SELECT * FROM critical_events 
    WHERE batchid IN ({batch_id_str})
    AND eventdate >= %s
    ORDER BY eventdate
""", [selected_date])

# ============================================================================
# METRICS
# ============================================================================

def get_metrics():
    if batch_sales.empty:
        return {
            'total_sold': 0, 'total_revenue': 0, 'total_expenses': 0,
            'profit': 0, 'margin': 0, 'concentration': 0,
            'unique_buyers': 0, 'demand_score': 50
        }
    
    total_sold = int(batch_sales['quantitysold'].sum())
    total_revenue = int(batch_sales['totalrevenue'].sum())
    total_expenses = int(batch_expenses['amount'].sum()) if not batch_expenses.empty else 0
    unique_buyers = int(batch_sales['buyerid'].nunique())
    
    buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
    concentration = (int(buyer_sales.head(3).sum()) / total_sold * 100) if total_sold > 0 else 0
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'total_sold': total_sold, 'total_revenue': total_revenue,
        'total_expenses': total_expenses, 'profit': profit, 'margin': margin,
        'concentration': concentration, 'unique_buyers': unique_buyers,
        'demand_score': 50 + (30 if concentration < 75 else 15)
    }

metrics = get_metrics()

# ============================================================================
# TAB: OVERVIEW
# ============================================================================

if st.session_state.current_tab == 'overview':
    st.markdown("## 📊 Overview")
    
    status = "🟢 Strong" if metrics['demand_score'] >= 70 else "🟡 Moderate" if metrics['demand_score'] >= 60 else "🔴 Weak"
    
    st.info(f"**Demand Score: {metrics['demand_score']}/100 {status}** • Concentration: {metrics['concentration']:.0f}%")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("🐔 Birds Sold", f"{metrics['total_sold']:,}")
    col2.metric("💵 Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    col3.metric("💸 Expenses", f"TZS {metrics['total_expenses']/1e6:.1f}M")
    col4.metric("🟢 Profit", f"TZS {metrics['profit']/1e6:.1f}M")
    col5.metric("📊 Margin %", f"{metrics['margin']:.0f}%")
    col6.metric("👥 Buyers", metrics['unique_buyers'])

# ============================================================================
# TAB: INSIGHTS
# ============================================================================

elif st.session_state.current_tab == 'insights':
    st.markdown("## 💡 Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Concentration Alert")
        if metrics['concentration'] > 75:
            st.error(f"🔴 CRITICAL: {metrics['concentration']:.0f}% from top 3 buyers")
        elif metrics['concentration'] > 60:
            st.warning(f"🟡 HIGH: {metrics['concentration']:.0f}% concentration")
        else:
            st.success(f"🟢 HEALTHY: {metrics['concentration']:.0f}% distribution")
    
    with col2:
        st.markdown("### Demand Status")
        if metrics['demand_score'] >= 80:
            st.success("✅ STRONG DEMAND")
        elif metrics['demand_score'] >= 70:
            st.info("🟡 GOOD DEMAND")
        else:
            st.error("🔴 WEAK DEMAND")

# ============================================================================
# TAB: FINANCIAL
# ============================================================================

elif st.session_state.current_tab == 'financial':
    st.markdown("## 💰 Financial Analysis")
    
    fcr_df = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird (TZS)': [1696, 1532, 1335, 1204, 1122],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    
    st.dataframe(fcr_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB: TRENDS
# ============================================================================

elif st.session_state.current_tab == 'trends':
    st.markdown("## 📈 Trends")
    
    if not batch_sales.empty:
        st.markdown("### Sales Over Time")
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        st.line_chart(daily_sales.set_index('datesold'), use_container_width=True)
    
    if not batch_events.empty:
        st.markdown("### Critical Events")
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity']].head(10), use_container_width=True, hide_index=True)

# ============================================================================
# TAB: SUMMARY
# ============================================================================

elif st.session_state.current_tab == 'summary':
    st.markdown("## 💵 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Batches", len(selected_ids))
    col2.metric("Total Birds", metrics['total_sold'])
    col3.metric("Total Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    col4.metric("Net Profit", f"TZS {metrics['profit']/1e6:.1f}M")

# ============================================================================
# TAB: OPERATIONS
# ============================================================================

elif st.session_state.current_tab == 'operations':
    st.markdown("## ⚙️ Operations")
    
    if not batch_mortality.empty:
        st.markdown("### Mortality Records")
        mort_df = batch_mortality[['daterecorded', 'quantitydied', 'reason']].copy()
        st.dataframe(mort_df, use_container_width=True, hide_index=True)
    else:
        st.info("No mortality records")

# ============================================================================
# TAB: STATEMENTS
# ============================================================================

elif st.session_state.current_tab == 'statements':
    st.markdown("## 📄 Financial Statements")
    
    st.info(f"""
    **Income Statement**
    
    Revenue: TZS {metrics['total_revenue']:,}
    Expenses: TZS {metrics['total_expenses']:,}
    
    **Net Profit: TZS {metrics['profit']:,}**
    Margin: {metrics['margin']:.1f}%
    """)

# ============================================================================
# TAB: INTELLIGENCE
# ============================================================================

elif st.session_state.current_tab == 'intelligence':
    st.markdown("## 🧠 Market Intelligence")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Buyers", metrics['unique_buyers'])
    col2.metric("Concentration", f"{metrics['concentration']:.0f}%")
    col3.metric("Demand Score", metrics['demand_score'])
    col4.metric("Batches", len(selected_ids))
    
    st.divider()
    
    if not batch_sales.empty:
        st.markdown("### Buyer Performance")
        buyer_df = batch_sales.groupby('buyername').agg({
            'quantitysold': 'sum',
            'totalrevenue': 'sum'
        }).sort_values('quantitysold', ascending=False).reset_index()
        buyer_df.columns = ['Buyer', 'Birds', 'Revenue']
        st.dataframe(buyer_df, use_container_width=True, hide_index=True)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#A0A0A0; font-size:12px;">
🐔 KUKU Farm Dashboard v3.0 | Farm Intelligence System
</p>
""", unsafe_allow_html=True)
