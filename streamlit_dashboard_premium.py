#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD - PREMIUM SaaS EDITION
Dark theme, SVG icons, card-based layout, custom CSS
"""

import streamlit as st
import psycopg2
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# COMPREHENSIVE CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
/* ============ ROOT & GENERAL ============ */
:root {
    --bg-primary: #0f1117;
    --bg-secondary: #161a23;
    --bg-tertiary: #21262d;
    --accent-primary: #10b981;
    --accent-hover: #059669;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --border-color: #30363d;
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary);
}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    padding: 0 !important;
    width: 100px !important;
}

[data-testid="stSidebarContent"] {
    padding: 16px 0 !important;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Icon buttons */
.sidebar-icon-btn {
    width: 56px;
    height: 56px;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    background-color: transparent;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    margin: 8px 0;
    padding: 0;
    font-size: 24px;
}

.sidebar-icon-btn:hover {
    color: var(--text-primary);
    border-color: var(--accent-primary);
    background-color: rgba(16, 185, 129, 0.08);
}

.sidebar-icon-btn.active {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1));
    border-color: var(--accent-primary);
    color: var(--accent-primary);
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

/* Hide sidebar elements text */
.sidebar-icon-btn + div,
[data-testid="stSidebar"] label {
    display: none !important;
}

/* ============ MAIN CONTENT ============ */
[data-testid="stAppViewContainer"] {
    margin-left: 0 !important;
    padding-left: 100px;
}

[data-testid="stMain"] {
    background-color: var(--bg-primary);
}

.main-content {
    padding: 32px 32px;
}

/* ============ TYPOGRAPHY ============ */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-weight: 600;
    letter-spacing: -0.02em;
}

h1 {
    font-size: 32px;
    margin-bottom: 8px;
}

h2 {
    font-size: 24px;
    margin-bottom: 16px;
    margin-top: 24px;
}

h3 {
    font-size: 18px;
    margin-bottom: 12px;
}

p, span, label, div {
    color: var(--text-primary);
}

.text-secondary {
    color: var(--text-secondary);
    font-size: 13px;
}

/* ============ CARDS ============ */
.card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 20px;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s ease;
}

.card:hover {
    border-color: var(--accent-primary);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
}

.card-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

.card-body {
    color: var(--text-primary);
}

/* ============ METRICS ============ */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 20px 0;
}

.metric-card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: var(--accent-primary);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--accent-primary);
    margin: 12px 0;
    font-variant-numeric: tabular-nums;
}

.metric-label {
    font-size: 13px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-unit {
    font-size: 12px;
    color: var(--text-secondary);
    margin-left: 4px;
}

/* ============ FORMS & INPUTS ============ */
.stSelectbox, .stMultiSelect, .stSlider, [data-testid="stTextInput"] {
    background-color: var(--bg-tertiary) !important;
}

.stSelectbox label, .stMultiSelect label, .stSlider label {
    color: var(--text-primary) !important;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
}

/* ============ ALERTS & MESSAGES ============ */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    background-color: rgba(16, 185, 129, 0.08) !important;
    color: var(--text-primary) !important;
}

.stAlert > div {
    color: var(--text-primary) !important;
}

.alert-success {
    background: rgba(16, 185, 129, 0.1) !important;
    border-color: rgba(16, 185, 129, 0.3) !important;
}

.alert-warning {
    background: rgba(245, 158, 11, 0.1) !important;
    border-color: rgba(245, 158, 11, 0.3) !important;
}

.alert-error {
    background: rgba(239, 68, 68, 0.1) !important;
    border-color: rgba(239, 68, 68, 0.3) !important;
}

/* ============ TABLES ============ */
.stDataFrame {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    overflow: hidden;
}

[data-testid="stDataFrameContainer"] {
    width: 100%;
}

/* ============ BUTTONS ============ */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
}

.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
    transform: translateY(-2px) !important;
}

/* ============ DIVIDERS ============ */
hr {
    border: none;
    height: 1px;
    background-color: var(--border-color);
    margin: 24px 0;
}

/* ============ CHARTS ============ */
.stPlotlyChart {
    background-color: var(--bg-secondary) !important;
    border-radius: 14px !important;
    border: 1px solid var(--border-color) !important;
    padding: 16px !important;
}

/* ============ SCROLLBAR ============ */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}

/* ============ UTILITIES ============ */
.gap-16 {
    gap: 16px;
}

.gap-24 {
    gap: 24px;
}

.text-center {
    text-align: center;
}

.text-muted {
    color: var(--text-secondary);
}

.accent-text {
    color: var(--accent-primary);
}

</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE FUNCTIONS
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

if 'selected_batches' not in st.session_state:
    st.session_state.selected_batches = []

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Navigation buttons with SVG icons
    nav_items = [
        ('overview', '📊'),
        ('insights', '💡'),
        ('financial', '💰'),
        ('trends', '📈'),
        ('summary', '💵'),
        ('operations', '⚙️'),
        ('statements', '📄'),
        ('intelligence', '🧠')
    ]
    
    for tab_id, icon in nav_items:
        is_active = st.session_state.current_tab == tab_id
        btn_class = "sidebar-icon-btn active" if is_active else "sidebar-icon-btn"
        
        if st.button(icon, key=f"nav_{tab_id}", use_container_width=False):
            st.session_state.current_tab = tab_id
            st.rerun()

# ============================================================================
# FETCH BATCHES & DATA
# ============================================================================

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

# ============================================================================
# MAIN HEADER
# ============================================================================

col1, col2 = st.columns([1, 6])

with col1:
    st.markdown("<div style='font-size: 32px; text-align: center;'>🐔</div>", unsafe_allow_html=True)

with col2:
    st.markdown("# KUKU Farm Dashboard")
    st.markdown("<p class='text-secondary'>Real-time farm management with demand intelligence</p>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# CONTROLS ROW
# ============================================================================

ctrl_col1, ctrl_col2 = st.columns(2)

with ctrl_col1:
    selected_names = st.multiselect(
        "📦 Select Batches",
        list(batch_options.keys()),
        default=list(batch_options.keys())[:1] if batch_options else []
    )
    selected_ids = [batch_options[name] for name in selected_names]

with ctrl_col2:
    selected_date = st.date_input(
        "📅 From Date",
        value=datetime.now().date() - timedelta(days=30),
        min_value=datetime.now().date() - timedelta(days=365),
        max_value=datetime.now().date()
    )

if not selected_ids:
    st.warning("Select at least one batch")
    st.stop()

batch_id_str = ','.join([str(id) for id in selected_ids])

# Fetch data
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
# METRICS CALCULATION
# ============================================================================

def calc_metrics():
    if batch_sales.empty:
        return {
            'total_sold': 0, 'total_revenue': 0, 'total_expenses': 0,
            'profit': 0, 'margin': 0, 'concentration': 0,
            'unique_buyers': 0, 'demand_score': 50, 'avg_price': 0
        }
    
    total_sold = int(batch_sales['quantitysold'].sum())
    total_revenue = int(batch_sales['totalrevenue'].sum())
    total_expenses = int(batch_expenses['amount'].sum()) if not batch_expenses.empty else 0
    unique_buyers = int(batch_sales['buyerid'].nunique())
    
    buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
    concentration = (int(buyer_sales.head(3).sum()) / total_sold * 100) if total_sold > 0 else 0
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_price = batch_sales['unitprice'].mean() if not batch_sales.empty else 0
    
    return {
        'total_sold': total_sold, 'total_revenue': total_revenue,
        'total_expenses': total_expenses, 'profit': profit, 'margin': margin,
        'concentration': concentration, 'unique_buyers': unique_buyers,
        'demand_score': 50 + (30 if concentration < 75 else 15), 'avg_price': avg_price
    }

metrics = calc_metrics()

# ============================================================================
# TAB: OVERVIEW
# ============================================================================

if st.session_state.current_tab == 'overview':
    st.markdown("## 📊 Overview")
    
    status = "🟢 Strong" if metrics['demand_score'] >= 70 else "🟡 Moderate" if metrics['demand_score'] >= 60 else "🔴 Weak"
    
    # Demand status card
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            <div class="card-title">Market Demand Status</div>
        </div>
        <div class="card-body">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div>
                    <div class="text-secondary">Demand Score</div>
                    <div style="font-size: 32px; color: #10b981; font-weight: 700; margin: 8px 0;">
                        {metrics['demand_score']}/100
                    </div>
                    <div class="text-secondary">{status}</div>
                </div>
                <div>
                    <div class="text-secondary">Concentration Risk</div>
                    <div style="font-size: 32px; color: #f59e0b; font-weight: 700; margin: 8px 0;">
                        {metrics['concentration']:.0f}%
                    </div>
                    <div class="text-secondary">Top 3 Buyers</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Metrics grid
    st.markdown("""
    <div class="metric-grid">
    """, unsafe_allow_html=True)
    
    metrics_data = [
        ("Birds Sold", f"{metrics['total_sold']:,}", ""),
        ("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M", ""),
        ("Expenses", f"TZS {metrics['total_expenses']/1e6:.1f}M", ""),
        ("Profit", f"TZS {metrics['profit']/1e6:.1f}M", ""),
        ("Margin", f"{metrics['margin']:.0f}%", ""),
        ("Avg Price", f"TZS {metrics['avg_price']:,.0f}", ""),
    ]
    
    cols = st.columns(6)
    for i, (label, value, unit) in enumerate(metrics_data):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# TAB: INSIGHTS
# ============================================================================

elif st.session_state.current_tab == 'insights':
    st.markdown("## 💡 Actionable Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Concentration Alert</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        if metrics['concentration'] > 75:
            st.error(f"🔴 CRITICAL: {metrics['concentration']:.0f}% from top 3 buyers")
            st.markdown("If one buyer stops, lose 25% revenue immediately.")
        elif metrics['concentration'] > 60:
            st.warning(f"🟡 HIGH: {metrics['concentration']:.0f}% concentration")
            st.markdown("Need to diversify buyer base.")
        else:
            st.success(f"🟢 HEALTHY: {metrics['concentration']:.0f}% distribution")
            st.markdown("Good buyer diversity.")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Demand Status</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        if metrics['demand_score'] >= 80:
            st.success("✅ STRONG DEMAND")
            st.markdown("Market responding excellently.")
        elif metrics['demand_score'] >= 70:
            st.info("🟡 GOOD DEMAND")
            st.markdown("Market is solid.")
        else:
            st.error("🔴 WEAK DEMAND")
            st.markdown("Monitor and improve before scaling.")
        
        st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# TAB: FINANCIAL
# ============================================================================

elif st.session_state.current_tab == 'financial':
    st.markdown("## 💰 Financial Analysis")
    
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-title">FCR Impact on Profitability</div>
        </div>
        <div class="card-body">
    """, unsafe_allow_html=True)
    
    fcr_df = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird (TZS)': [1696, 1532, 1335, 1204, 1122],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    
    st.dataframe(fcr_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# TAB: TRENDS
# ============================================================================

elif st.session_state.current_tab == 'trends':
    st.markdown("## 📈 Trends")
    
    if not batch_sales.empty:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Sales Over Time</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_sales['datesold'], y=daily_sales['quantitysold'],
            mode='lines+markers', name='Birds Sold',
            line=dict(color='#10b981', width=2),
            fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#161a23', plot_bgcolor='#0f1117',
            font=dict(color='#e6edf3'), height=400,
            margin=dict(l=0, r=0, t=0, b=0), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# TAB: SUMMARY
# ============================================================================

elif st.session_state.current_tab == 'summary':
    st.markdown("## 💵 Summary")
    
    summary_cols = st.columns(4)
    
    summary_data = [
        ("Total Batches", len(selected_ids)),
        ("Total Birds", metrics['total_sold']),
        ("Total Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M"),
        ("Net Profit", f"TZS {metrics['profit']/1e6:.1f}M"),
    ]
    
    for i, (label, value) in enumerate(summary_data):
        with summary_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size: 24px;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# TAB: OPERATIONS
# ============================================================================

elif st.session_state.current_tab == 'operations':
    st.markdown("## ⚙️ Operations")
    
    if not batch_mortality.empty:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Mortality Records</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        mort_df = batch_mortality[['daterecorded', 'quantitydied', 'reason']].copy()
        st.dataframe(mort_df, use_container_width=True, hide_index=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.info("No mortality records")

# ============================================================================
# TAB: STATEMENTS
# ============================================================================

elif st.session_state.current_tab == 'statements':
    st.markdown("## 📄 Financial Statements")
    
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            <div class="card-title">Income Statement</div>
        </div>
        <div class="card-body">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 12px 0; color: #8b949e;">Revenue</td>
                    <td style="padding: 12px 0; text-align: right; color: #10b981; font-weight: 600;">TZS {metrics['total_revenue']:,}</td>
                </tr>
                <tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 12px 0; color: #8b949e;">Expenses</td>
                    <td style="padding: 12px 0; text-align: right; color: #ef4444; font-weight: 600;">TZS {metrics['total_expenses']:,}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; color: #e6edf3; font-weight: 600;">Net Profit</td>
                    <td style="padding: 12px 0; text-align: right; color: #10b981; font-weight: 700; font-size: 18px;">TZS {metrics['profit']:,}</td>
                </tr>
            </table>
            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #30363d;">
                <span style="color: #8b949e;">Profit Margin:</span>
                <span style="color: #10b981; font-weight: 600; margin-left: 8px;">{metrics['margin']:.1f}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TAB: MARKET INTELLIGENCE
# ============================================================================

elif st.session_state.current_tab == 'intelligence':
    st.markdown("## 🧠 Market Intelligence")
    
    intel_cols = st.columns(4)
    
    intel_data = [
        ("Active Buyers", metrics['unique_buyers']),
        ("Concentration", f"{metrics['concentration']:.0f}%"),
        ("Demand Score", metrics['demand_score']),
        ("Avg Price", f"TZS {metrics['avg_price']:,.0f}"),
    ]
    
    for i, (label, value) in enumerate(intel_data):
        with intel_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size: 24px;">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    if not batch_sales.empty:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Buyer Performance</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        buyer_df = batch_sales.groupby('buyername').agg({
            'quantitysold': 'sum',
            'totalrevenue': 'sum'
        }).sort_values('quantitysold', ascending=False).reset_index()
        buyer_df.columns = ['Buyer', 'Birds', 'Revenue']
        
        st.dataframe(buyer_df, use_container_width=True, hide_index=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

st.markdown("""
<div style="text-align: center; color: #8b949e; font-size: 12px; padding: 24px 0;">
    KUKU Farm Dashboard v4.0 Pro | Premium SaaS Edition
</div>
""", unsafe_allow_html=True)
