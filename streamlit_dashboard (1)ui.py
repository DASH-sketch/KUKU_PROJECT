#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD - OPTIMIZED FOR STREAMLIT
Best visual design achievable within Streamlit constraints
Icon-only sidebar, circular demand score, improved cards
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
# AGGRESSIVE CSS OVERRIDES - Working within Streamlit constraints
# ============================================================================

st.markdown("""
<style>
/* ============ ROOT VARIABLES ============ */
:root {
    --bg-primary: #0a0e27;
    --bg-secondary: #1a1f3a;
    --accent-green: #10b981;
    --accent-hover: #059669;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --border-color: #2d333b;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ============ HIDE STREAMLIT DEFAULTS ============ */
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }

/* ============ AGGRESSIVE SIDEBAR STYLING ============ */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    width: 90px !important;
    min-width: 90px !important;
    max-width: 90px !important;
    border-right: 1px solid var(--border-color) !important;
    padding: 0 !important;
}

[data-testid="stSidebarContent"] {
    padding: 12px 6px !important;
    gap: 2px !important;
}

/* Hide sidebar labels and text */
[data-testid="stSidebar"] label { display: none !important; }
[data-testid="stSidebar"] > div > div:first-child > div:first-child { display: none !important; }

/* Sidebar button styling - Icon only */
[data-testid="stSidebar"] .stButton > button {
    width: 64px !important;
    height: 64px !important;
    margin: 6px auto !important;
    padding: 0 !important;
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 14px !important;
    color: var(--text-primary) !important;
    font-size: 24px !important;
    font-weight: 400 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.3s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(16, 185, 129, 0.1) !important;
    border-color: var(--accent-green) !important;
    color: var(--accent-green) !important;
}

/* Active button styling */
[data-testid="stSidebar"] .stButton:nth-of-type(1) > button {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05)) !important;
    border-color: var(--accent-green) !important;
    color: var(--accent-green) !important;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.2) !important;
}

/* ============ MAIN CONTENT ============ */
[data-testid="stMain"] {
    background-color: var(--bg-primary) !important;
    margin-left: 0 !important;
    padding-left: 90px !important;
    padding-top: 24px !important;
    padding-right: 32px !important;
    padding-bottom: 32px !important;
}

/* ============ TYPOGRAPHY ============ */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}

h1 { font-size: 32px !important; margin-bottom: 8px !important; }
h2 { font-size: 22px !important; margin-bottom: 20px !important; }
h3 { font-size: 16px !important; margin-bottom: 12px !important; }

p, span, label, div { color: var(--text-primary) !important; }

.text-secondary { color: var(--text-secondary) !important; font-size: 13px !important; }

/* ============ CARDS ============ */
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

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
}

.card-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }

/* ============ METRICS & CARDS ============ */
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
    font-weight: 500;
}

/* ============ METRIC GRID ============ */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin: 16px 0;
}

/* ============ ALERTS ============ */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    background-color: rgba(16, 185, 129, 0.08) !important;
    padding: 16px !important;
}

/* ============ TABLES ============ */
[data-testid="stDataFrame"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    overflow: hidden !important;
}

/* ============ FORMS ============ */
.stSelectbox, .stMultiSelect, .stSlider, .stDateInput {
    margin-bottom: 12px !important;
}

.stSelectbox label, .stMultiSelect label, .stSlider label, .stDateInput label {
    color: var(--text-primary) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ============ DIVIDER ============ */
hr {
    border: none !important;
    height: 1px !important;
    background-color: var(--border-color) !important;
    margin: 20px 0 !important;
}

/* ============ CHARTS ============ */
[data-testid="stPlotlyChart"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    padding: 12px !important;
}

/* ============ SCROLLBAR ============ */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* ============ UTILITY ============ */
.accent-text { color: var(--accent-green) !important; }
.text-muted { color: var(--text-secondary) !important; font-size: 12px !important; }

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
# SIDEBAR
# ============================================================================

with st.sidebar:
    # Icon buttons for navigation
    nav_icons = ['📊', '💡', '💰', '📈', '💵', '⚙️', '📄', '🧠']
    nav_ids = ['overview', 'insights', 'financial', 'trends', 'summary', 'operations', 'statements', 'intelligence']
    
    for icon, tab_id in zip(nav_icons, nav_ids):
        if st.button(icon, key=f"nav_{tab_id}", use_container_width=False):
            st.session_state.current_tab = tab_id
            st.rerun()
    
    st.divider()
    
    # Batch selector
    all_batches = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted 
        FROM batches_detailed 
        ORDER BY datestarted DESC
    """)
    
    if all_batches.empty:
        st.error("No batches")
        st.stop()
    
    batch_options = {
        f"{b['batchname']} ({int(b['quantitychicksstarted'])}b)": int(b['batchid']) 
        for _, b in all_batches.iterrows()
    }
    
    selected_names = st.multiselect(
        "📦",
        list(batch_options.keys()),
        default=list(batch_options.keys())[:1],
        label_visibility="collapsed",
        max_selections=5
    )
    
    selected_ids = [batch_options[name] for name in selected_names]
    
    st.divider()
    
    # Date picker
    selected_date = st.date_input(
        "📅",
        value=datetime.now().date() - timedelta(days=30),
        label_visibility="collapsed"
    )

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([0.3, 4])
with col1:
    st.markdown("<div style='font-size: 28px; text-align: center; margin-top: 8px;'>🐔</div>", unsafe_allow_html=True)
with col2:
    st.markdown("# KUKU Farm Dashboard")
    st.markdown("<p style='color: #8b949e; margin: 0; font-size: 13px;'>Real-time farm management with demand intelligence</p>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# DATA FETCH
# ============================================================================

if not selected_ids:
    st.warning("Select batches in sidebar")
    st.stop()

batch_id_str = ','.join([str(id) for id in selected_ids])

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
""", [selected_date])

batch_mortality = fetch_data(f"""
    SELECT * FROM daily_mortality 
    WHERE batchid IN ({batch_id_str})
    AND daterecorded >= %s
""", [selected_date])

batch_events = fetch_data(f"""
    SELECT * FROM critical_events 
    WHERE batchid IN ({batch_id_str})
    AND eventdate >= %s
""", [selected_date])

# ============================================================================
# METRICS
# ============================================================================

def get_metrics():
    if batch_sales.empty:
        return {'total_sold': 0, 'total_revenue': 0, 'total_expenses': 0, 'profit': 0, 'margin': 0,
                'concentration': 0, 'unique_buyers': 0, 'demand_score': 50, 'avg_price': 0}
    
    total_sold = int(batch_sales['quantitysold'].sum())
    total_revenue = int(batch_sales['totalrevenue'].sum())
    total_expenses = int(batch_expenses['amount'].sum()) if not batch_expenses.empty else 0
    unique_buyers = int(batch_sales['buyerid'].nunique())
    
    buyer_sales = batch_sales.groupby('buyerid')['quantitysold'].sum().sort_values(ascending=False)
    concentration = (int(buyer_sales.head(3).sum()) / total_sold * 100) if total_sold > 0 else 0
    
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_price = batch_sales['unitprice'].mean() if not batch_sales.empty else 0
    
    return {'total_sold': total_sold, 'total_revenue': total_revenue, 'total_expenses': total_expenses,
            'profit': profit, 'margin': margin, 'concentration': concentration, 'unique_buyers': unique_buyers,
            'demand_score': 50 + (30 if concentration < 75 else 15), 'avg_price': avg_price}

metrics = get_metrics()

# ============================================================================
# TAB: OVERVIEW
# ============================================================================

if st.session_state.current_tab == 'overview':
    st.markdown("## Performance Overview")
    
    # Key metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics_data = [("Birds Sold", f"{metrics['total_sold']:,}"),
                    ("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M"),
                    ("Expenses", f"TZS {metrics['total_expenses']/1e6:.1f}M"),
                    ("Profit", f"TZS {metrics['profit']/1e6:.1f}M"),
                    ("Margin", f"{metrics['margin']:.0f}%"),
                    ("Buyers", metrics['unique_buyers'])]
    
    for col, (label, value) in zip([col1, col2, col3, col4, col5, col6], metrics_data):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Performance Overview Card
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-title">Monthly Performance</div>
            <span style="font-size: 12px; color: #8b949e;">📊</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not batch_sales.empty:
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_sales['datesold'], y=daily_sales['quantitysold'],
            mode='lines+markers', fill='tozeroy',
            line=dict(color='#10b981', width=2),
            fillcolor='rgba(16, 185, 129, 0.1)',
            marker=dict(size=5)
        ))
        fig.update_layout(template='plotly_dark', paper_bgcolor='#1a1f3a', plot_bgcolor='#0a0e27',
                         font=dict(color='#e6edf3'), height=300, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Circular demand score
    st.markdown("### Market Demand Score")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        score = metrics['demand_score']
        color = '#10b981' if score >= 70 else '#f59e0b' if score >= 60 else '#ef4444'
        
        fig = go.Figure(data=[go.Pie(
            values=[score, 100-score],
            marker=dict(colors=[color, '#21262d']),
            hole=0.7,
            hoverinfo='skip',
            textinfo='none'
        )])
        fig.add_annotation(text=f"{score}/100", x=0.5, y=0.5, font=dict(size=32, color=color), showarrow=False)
        fig.update_layout(template='plotly_dark', paper_bgcolor='#1a1f3a', plot_bgcolor='#0a0e27',
                         margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB: INSIGHTS
# ============================================================================

elif st.session_state.current_tab == 'insights':
    st.markdown("## Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-title">Concentration Risk</div>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)
        
        if metrics['concentration'] > 75:
            st.error(f"🔴 CRITICAL: {metrics['concentration']:.0f}%")
        elif metrics['concentration'] > 60:
            st.warning(f"🟡 HIGH: {metrics['concentration']:.0f}%")
        else:
            st.success(f"🟢 HEALTHY: {metrics['concentration']:.0f}%")
        
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
            st.success("✅ STRONG")
        elif metrics['demand_score'] >= 70:
            st.info("🟡 GOOD")
        else:
            st.error("🔴 WEAK")
        
        st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# TAB: FINANCIAL
# ============================================================================

elif st.session_state.current_tab == 'financial':
    st.markdown("## Financial Analysis")
    fcr_df = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird': [1696, 1532, 1335, 1204, 1122],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    st.dataframe(fcr_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB: TRENDS
# ============================================================================

elif st.session_state.current_tab == 'trends':
    st.markdown("## Trends")
    if not batch_sales.empty:
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        st.line_chart(daily_sales.set_index('datesold'), use_container_width=True, height=400)
    if not batch_events.empty:
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity']].head(10), use_container_width=True, hide_index=True)

# ============================================================================
# TAB: SUMMARY
# ============================================================================

elif st.session_state.current_tab == 'summary':
    st.markdown("## Financial Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Batches", len(selected_ids))
    col2.metric("Birds", metrics['total_sold'])
    col3.metric("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    col4.metric("Profit", f"TZS {metrics['profit']/1e6:.1f}M")

# ============================================================================
# TAB: OPERATIONS
# ============================================================================

elif st.session_state.current_tab == 'operations':
    st.markdown("## Operations")
    if not batch_mortality.empty:
        st.dataframe(batch_mortality[['daterecorded', 'quantitydied', 'reason']].head(20), use_container_width=True, hide_index=True)

# ============================================================================
# TAB: STATEMENTS
# ============================================================================

elif st.session_state.current_tab == 'statements':
    st.markdown("## Financial Statements")
    st.markdown(f"""
    <div class="card">
        <div class="card-title" style="margin-bottom: 16px;">Income Statement</div>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #2d333b;">
                <td style="padding: 12px 0; color: #8b949e;">Revenue</td>
                <td style="padding: 12px 0; text-align: right; color: #10b981; font-weight: 600;">TZS {metrics['total_revenue']:,}</td>
            </tr>
            <tr style="border-bottom: 1px solid #2d333b;">
                <td style="padding: 12px 0; color: #8b949e;">Expenses</td>
                <td style="padding: 12px 0; text-align: right; color: #ef4444; font-weight: 600;">TZS {metrics['total_expenses']:,}</td>
            </tr>
            <tr>
                <td style="padding: 12px 0; color: #e6edf3; font-weight: 600;">Net Profit</td>
                <td style="padding: 12px 0; text-align: right; color: #10b981; font-weight: 700; font-size: 18px;">TZS {metrics['profit']:,}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TAB: INTELLIGENCE
# ============================================================================

elif st.session_state.current_tab == 'intelligence':
    st.markdown("## Market Intelligence")
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
KUKU Dashboard v4.0 | Optimized for Streamlit
</div>
""", unsafe_allow_html=True)
