#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v6.0
Flexible date filter (4 scenarios) + batch-linked actual feed costs
"""

import streamlit as st
import psycopg2
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS
# ============================================================================

st.markdown("""
<style>
:root {
    --bg-primary: #0a0e27;
    --bg-secondary: #1a1f3a;
    --accent-green: #10b981;
    --accent-hover: #059669;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --border-color: #2d333b;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    margin: 4px 0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(16, 185, 129, 0.08) !important;
    border-color: var(--accent-green) !important;
    color: var(--text-primary) !important;
}

/* Typography */
h1, h2, h3 { color: var(--text-primary) !important; }
p, span, div { color: var(--text-primary) !important; }

/* Cards */
.card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.card:hover {
    border-color: var(--accent-green);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
}

/* Metrics */
.metric-card {
    background: linear-gradient(135deg, var(--bg-secondary), #0f1729);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: var(--accent-green);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
    transform: translateY(-2px);
}

.metric-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent-green);
    margin: 8px 0;
}

.metric-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Alerts */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
}

/* Tables */
[data-testid="stDataFrame"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
}

/* Charts */
[data-testid="stPlotlyChart"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    padding: 12px !important;
}

/* Divider */
hr { border: none !important; height: 1px !important; background-color: var(--border-color) !important; }
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
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# SESSION STATE
# ============================================================================

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'overview'

# ============================================================================
# SIDEBAR - FLEXIBLE DATE FILTER
# ============================================================================

with st.sidebar:
    st.markdown("## 🐔 KUKU")
    st.markdown("*Farm Dashboard*")
    st.divider()
    
    st.markdown("### NAVIGATION")
    
    tabs_nav = [
        ('overview', '📊 Overview'),
        ('insights', '💡 Insights'),
        ('financial', '💰 Financial'),
        ('trends', '📈 Trends'),
        ('summary', '💵 Summary'),
        ('operations', '⚙️ Operations'),
        ('statements', '📄 Statements'),
        ('intelligence', '🧠 Intelligence')
    ]
    
    for tab_id, label in tabs_nav:
        if st.button(label, key=f"tab_{tab_id}", use_container_width=True):
            st.session_state.current_tab = tab_id
    
    st.divider()
    
    st.markdown("### FILTERS")
    
    # Get all available batches
    all_batches_data = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted, dateended, status
        FROM public.batches_detailed
        ORDER BY datestarted DESC
    """)
    
    if all_batches_data.empty:
        st.error("No batches found")
        st.stop()
    
    batch_options = {
        f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds) - {b['status']}": {
            'id': int(b['batchid']),
            'start': pd.to_datetime(b['datestarted']).date(),
            'end': pd.to_datetime(b['dateended']).date() if b['dateended'] else date.today()
        }
        for _, b in all_batches_data.iterrows()
    }
    
    st.markdown("**📦 Batch Selection** (optional)")
    selected_batch_names = st.multiselect(
        "Batches",
        list(batch_options.keys()),
        default=[],
        label_visibility="collapsed",
        max_selections=5
    )
    
    selected_batch_ids = [batch_options[name]['id'] for name in selected_batch_names]
    
    # ========== SCENARIO LOGIC ==========
    
    if selected_batch_ids:
        # SCENARIO A/B: Batch selected
        batch_dates = [batch_options[name] for name in selected_batch_names]
        min_date = min([b['start'] for b in batch_dates])
        max_date = max([b['end'] for b in batch_dates])
        
        st.markdown(f"**📅 Date Range**")
        st.info(f"Batch date range: {min_date} → {max_date}")
        
        # Option to override
        custom_date_override = st.checkbox("📝 Use custom date range?", value=False)
        
        if custom_date_override:
            # SCENARIO B: Override enabled
            date_start = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
            date_end = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
            filter_type = "batch_custom"
        else:
            # SCENARIO A: Use batch dates
            date_start = min_date
            date_end = max_date
            filter_type = "batch_only"
            st.success(f"✅ Using batch date range")
    
    else:
        # SCENARIO C/D: No batch selected
        st.markdown(f"**📅 Date Range** (all batches)")
        
        date_start = st.date_input(
            "From",
            value=date.today() - timedelta(days=90),
            label_visibility="collapsed"
        )
        date_end = st.date_input(
            "To",
            value=date.today(),
            label_visibility="collapsed"
        )
        
        if date_start and date_end:
            filter_type = "date_only"
            st.info(f"📌 Showing all batches: {date_start} → {date_end}")
        else:
            filter_type = "all"
            st.warning("No filters applied - showing all data")

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([0.15, 3])
with col1:
    st.markdown("<div style='font-size: 36px; margin-top: 8px;'>🐔</div>", unsafe_allow_html=True)
with col2:
    st.markdown("# KUKU Farm Dashboard")
    st.markdown("<p style='color: #8b949e; margin: 0; font-size: 13px;'>Flexible filtering + actual feed costs</p>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# BUILD FILTER QUERIES
# ============================================================================

# Build batch filter
if selected_batch_ids:
    batch_id_str = ','.join([str(id) for id in selected_batch_ids])
    batch_where = f"AND ds.batchid IN ({batch_id_str})"
else:
    batch_where = ""

# Build date filter
date_where = f"AND ds.datesold BETWEEN '{date_start}' AND '{date_end}'"

# ============================================================================
# FETCH DATA
# ============================================================================

batch_sales = fetch_data(f"""
    SELECT ds.*, b.buyername 
    FROM public.daily_sales ds
    LEFT JOIN public.buyers b ON ds.buyerid = b.buyerid
    WHERE 1=1 {batch_where} {date_where}
    ORDER BY ds.datesold
""")

batch_expenses = fetch_data(f"""
    SELECT * FROM public.expenses 
    WHERE category != 'Feed Purchase'
    {batch_where} {date_where}
""")

# Feed costs (actual from daily_feed_log)
batch_feed_log = fetch_data(f"""
    SELECT * FROM public.daily_feed_log
    WHERE 1=1 {batch_where}
    AND datefed BETWEEN '{date_start}' AND '{date_end}'
""")

batch_mortality = fetch_data(f"""
    SELECT * FROM public.daily_mortality
    WHERE 1=1 {batch_where}
    AND daterecorded BETWEEN '{date_start}' AND '{date_end}'
""")

batch_events = fetch_data(f"""
    SELECT * FROM public.critical_events
    WHERE 1=1 {batch_where}
    AND eventdate BETWEEN '{date_start}' AND '{date_end}'
""")

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def get_metrics():
    if batch_sales.empty:
        return {
            'total_sold': 0, 'total_revenue': 0, 'total_expenses': 0, 'total_feed_cost': 0,
            'other_expenses': 0, 'profit': 0, 'margin': 0, 'concentration': 0, 'unique_buyers': 0,
            'demand_score': 50, 'avg_price': 0
        }
    
    total_sold = int(batch_sales['quantitysold'].sum())
    total_revenue = int(batch_sales['totalrevenue'].sum())
    
    # Use actual feed costs from daily_feed_log (not 1640 * qty)
    total_feed_cost = int(batch_feed_log['feedcost'].sum()) if not batch_feed_log.empty else 0
    
    # Other expenses (non-feed)
    other_expenses = int(batch_expenses['amount'].sum()) if not batch_expenses.empty else 0
    
    total_expenses = total_feed_cost + other_expenses
    
    unique_buyers = int(batch_sales['buyerid'].nunique())
    
    buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
    concentration = (int(buyer_sales.head(3).sum()) / total_sold * 100) if total_sold > 0 else 0
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_price = batch_sales['unitprice'].mean() if not batch_sales.empty else 0
    
    return {
        'total_sold': total_sold, 'total_revenue': total_revenue,
        'total_expenses': total_expenses, 'total_feed_cost': total_feed_cost,
        'other_expenses': other_expenses, 'profit': profit, 'margin': margin,
        'concentration': concentration, 'unique_buyers': unique_buyers,
        'demand_score': 50 + (30 if concentration < 75 else 15), 'avg_price': avg_price
    }

metrics = get_metrics()

# ============================================================================
# TABS
# ============================================================================

if st.session_state.current_tab == 'overview':
    st.markdown("## 📊 Overview")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics_data = [
        ("Birds Sold", f"{metrics['total_sold']:,}"),
        ("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M"),
        ("Feed Cost", f"TZS {metrics['total_feed_cost']/1e6:.2f}M"),
        ("Other Costs", f"TZS {metrics['other_expenses']/1e6:.2f}M"),
        ("Profit", f"TZS {metrics['profit']/1e6:.1f}M"),
        ("Margin", f"{metrics['margin']:.0f}%"),
    ]
    
    for col, (label, value) in zip([col1, col2, col3, col4, col5, col6], metrics_data):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    if not batch_sales.empty:
        st.markdown("### Sales Trend")
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_sales['datesold'], y=daily_sales['quantitysold'],
            mode='lines+markers', fill='tozeroy',
            line=dict(color='#10b981', width=2),
            fillcolor='rgba(16, 185, 129, 0.1)',
            marker=dict(size=5)
        ))
        fig.update_layout(
            template='plotly_dark', paper_bgcolor='#1a1f3a', plot_bgcolor='#0a0e27',
            font=dict(color='#e6edf3'), height=300, margin=dict(l=0, r=0, t=0, b=0), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.current_tab == 'insights':
    st.markdown("## 💡 Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Concentration Risk")
        if metrics['concentration'] > 75:
            st.error(f"🔴 CRITICAL: {metrics['concentration']:.0f}%")
        elif metrics['concentration'] > 60:
            st.warning(f"🟡 HIGH: {metrics['concentration']:.0f}%")
        else:
            st.success(f"🟢 HEALTHY: {metrics['concentration']:.0f}%")
    
    with col2:
        st.markdown("### Demand Status")
        if metrics['demand_score'] >= 80:
            st.success("✅ STRONG")
        elif metrics['demand_score'] >= 70:
            st.info("🟡 GOOD")
        else:
            st.error("🔴 WEAK")

elif st.session_state.current_tab == 'financial':
    st.markdown("## 💰 Financial Analysis")
    fcr_df = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird': [1696, 1532, 1335, 1204, 1122],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    st.dataframe(fcr_df, use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'trends':
    st.markdown("## 📈 Trends")
    if not batch_sales.empty:
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        st.line_chart(daily_sales.set_index('datesold'), use_container_width=True, height=400)
    if not batch_events.empty:
        st.markdown("### Critical Events")
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity']].head(10), use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'summary':
    st.markdown("## 💵 Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Batches", len(selected_batch_ids) if selected_batch_ids else "All")
    col2.metric("Birds", metrics['total_sold'])
    col3.metric("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    col4.metric("Profit", f"TZS {metrics['profit']/1e6:.1f}M")

elif st.session_state.current_tab == 'operations':
    st.markdown("## ⚙️ Operations")
    if not batch_mortality.empty:
        st.markdown("### Mortality Records")
        st.dataframe(batch_mortality[['daterecorded', 'quantitydied', 'reason']].head(20), use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'statements':
    st.markdown("## 📄 Financial Statements")
    st.markdown(f"""
    **Income Statement**
    
    Revenue: TZS {metrics['total_revenue']:,}
    
    Feed Cost: TZS {metrics['total_feed_cost']:,}
    Other Expenses: TZS {metrics['other_expenses']:,}
    **Total Expenses: TZS {metrics['total_expenses']:,}**
    
    **Net Profit: TZS {metrics['profit']:,}**
    Margin: {metrics['margin']:.1f}%
    """)

elif st.session_state.current_tab == 'intelligence':
    st.markdown("## 🧠 Market Intelligence")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Buyers", metrics['unique_buyers'])
    col2.metric("Concentration", f"{metrics['concentration']:.0f}%")
    col3.metric("Score", metrics['demand_score'])
    col4.metric("Avg Price", f"TZS {metrics['avg_price']:,.0f}")
    
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
<div style="text-align: center; color: #8b949e; font-size: 11px; padding: 16px 0;">
KUKU Dashboard v6.0 | Flexible filtering + actual feed costs
</div>
""", unsafe_allow_html=True)
