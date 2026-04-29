#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD - SVG Icons Edition
Clean sidebar with Lucide-style SVG icons
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
# SVG ICONS (Lucide style - clean line icons)
# ============================================================================

SVG_ICONS = {
    "overview": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><polyline points='12 3 20 7.5 20 16.5 12 21 4 16.5 4 7.5 12 3'></polyline><polyline points='12 12 20 7.5'></polyline><polyline points='12 12 12 21'></polyline><polyline points='12 12 4 7.5'></polyline></svg>""",
    "insights": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><circle cx='12' cy='12' r='1'></circle><path d='M12 1v6m0 6v6'></path><path d='M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24'></path><path d='M1 12h6m6 0h6'></path><path d='M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24'></path></svg>""",
    "financial": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><line x1='12' y1='2' x2='12' y2='22'></line><path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'></path></svg>""",
    "trends": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><polyline points='23 6 13.5 15.5 8.5 10.5 1 17'></polyline><polyline points='17 6 23 6 23 12'></polyline></svg>""",
    "summary": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='9' y1='9' x2='15' y2='9'></line><line x1='9' y1='15' x2='15' y2='15'></line></svg>""",
    "operations": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><circle cx='12' cy='12' r='3'></circle><path d='M12 1v6m0 6v6M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24'></path></svg>""",
    "statements": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path><polyline points='14 2 14 8 20 8'></polyline><line x1='12' y1='19' x2='12' y2='5'></line><line x1='9' y1='19' x2='15' y2='19'></line></svg>""",
    "intelligence": """<svg width='24' height='24' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'></path><circle cx='9' cy='10' r='1'></circle><circle cx='12' cy='10' r='1'></circle><circle cx='15' cy='10' r='1'></circle></svg>"""
}

# ============================================================================
# CUSTOM CSS - SVG Icons + Sidebar
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

/* ============ SIDEBAR STYLING ============ */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    width: 90px !important;
    min-width: 90px !important;
    max-width: 90px !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebarContent"] {
    padding: 16px 8px !important;
    gap: 0 !important;
}

/* Hide default labels */
[data-testid="stSidebar"] label { display: none !important; }
[data-testid="stSidebar"] .stButton > div { width: 100% !important; }

/* Icon buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 56px !important;
    height: 56px !important;
    margin: 8px auto !important;
    padding: 0 !important;
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    color: var(--text-primary) !important;
    border-color: var(--accent-green) !important;
    background: rgba(16, 185, 129, 0.08) !important;
}

/* ============ ACTIVE STATE ============ */
[data-testid="stSidebar"] .stButton:nth-child(1) > button {
    background: rgba(16, 185, 129, 0.15) !important;
    border-color: var(--accent-green) !important;
    color: var(--accent-green) !important;
}

/* ============ MAIN CONTENT ============ */
[data-testid="stMain"] {
    background-color: var(--bg-primary) !important;
    margin-left: 0 !important;
    padding-left: 90px !important;
}

/* ============ TYPOGRAPHY ============ */
h1, h2, h3 { color: var(--text-primary) !important; }
p, span, div { color: var(--text-primary) !important; }

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

/* ============ METRICS ============ */
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

/* ============ ALERTS ============ */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
}

/* ============ TABLES ============ */
[data-testid="stDataFrame"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
}

/* ============ CHARTS ============ */
[data-testid="stPlotlyChart"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    padding: 12px !important;
}

/* ============ DIVIDER ============ */
hr { border: none !important; height: 1px !important; background-color: var(--border-color) !important; }

</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE & SIDEBAR
# ============================================================================

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'overview'

with st.sidebar:
    tabs_config = [
        ('overview', 'overview'),
        ('insights', 'insights'),
        ('financial', 'financial'),
        ('trends', 'trends'),
        ('summary', 'summary'),
        ('operations', 'operations'),
        ('statements', 'statements'),
        ('intelligence', 'intelligence')
    ]
    
    for tab_id, icon_key in tabs_config:
        col = st.columns([1])[0]
        with col:
            if st.button(SVG_ICONS[icon_key], key=f"tab_{tab_id}", help=tab_id.title()):
                st.session_state.current_tab = tab_id
                st.rerun()
    
    st.divider()
    
    # Batch selector
    all_batches = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted 
        FROM batches_detailed 
        ORDER BY datestarted DESC
    """) if 'fetch_data' in dir() else pd.DataFrame()
    
    if not all_batches.empty:
        batch_options = {
            f"{b['batchname']} ({int(b['quantitychicksstarted'])}b)": int(b['batchid']) 
            for _, b in all_batches.iterrows()
        }
        
        st.markdown("### 📦")
        selected_names = st.multiselect(
            "Batches",
            list(batch_options.keys()),
            default=list(batch_options.keys())[:1],
            label_visibility="collapsed",
            max_selections=5
        )
        selected_ids = [batch_options[name] for name in selected_names]
    
    st.divider()
    
    st.markdown("### 📅")
    selected_date = st.date_input(
        "Date",
        value=datetime.now().date() - timedelta(days=30),
        label_visibility="collapsed"
    )

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
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([0.2, 3])
with col1:
    st.markdown("<div style='font-size: 32px; margin-top: 12px;'>🐔</div>", unsafe_allow_html=True)
with col2:
    st.markdown("# KUKU Farm Dashboard")
    st.markdown("<p style='color: #8b949e; margin: 0; font-size: 13px;'>Professional farm analytics</p>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# FETCH DATA
# ============================================================================

if 'selected_ids' not in locals() or not selected_ids:
    st.warning("Select batches in sidebar →")
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
# TAB CONTENT
# ============================================================================

if st.session_state.current_tab == 'overview':
    st.markdown("## Performance Overview")
    
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
        fig.update_layout(template='plotly_dark', paper_bgcolor='#1a1f3a', plot_bgcolor='#0a0e27',
                         font=dict(color='#e6edf3'), height=300, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.current_tab == 'insights':
    st.markdown("## Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""<div class="card">
            <div style="font-weight: 600; margin-bottom: 12px;">Concentration Risk</div>""", unsafe_allow_html=True)
        if metrics['concentration'] > 75:
            st.error(f"🔴 CRITICAL: {metrics['concentration']:.0f}%")
        elif metrics['concentration'] > 60:
            st.warning(f"🟡 HIGH: {metrics['concentration']:.0f}%")
        else:
            st.success(f"🟢 HEALTHY: {metrics['concentration']:.0f}%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""<div class="card">
            <div style="font-weight: 600; margin-bottom: 12px;">Demand Status</div>""", unsafe_allow_html=True)
        if metrics['demand_score'] >= 80:
            st.success("✅ STRONG DEMAND")
        elif metrics['demand_score'] >= 70:
            st.info("🟡 GOOD DEMAND")
        else:
            st.error("🔴 WEAK DEMAND")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_tab == 'financial':
    st.markdown("## Financial Analysis")
    fcr_df = pd.DataFrame({
        'FCR': [1.10, 1.20, 1.32, 1.40, 1.45],
        'Profit/Bird': [1696, 1532, 1335, 1204, 1122],
        'Status': ['🟢 Elite', '🟢 Good', '🟡 Watch', '🟡 Marginal', '🔴 Poor']
    })
    st.dataframe(fcr_df, use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'trends':
    st.markdown("## Trends")
    if not batch_sales.empty:
        daily_sales = batch_sales.groupby('datesold')['quantitysold'].sum().reset_index()
        st.line_chart(daily_sales.set_index('datesold'), use_container_width=True, height=400)
    if not batch_events.empty:
        st.markdown("### Critical Events")
        st.dataframe(batch_events[['eventdate', 'eventtype', 'severity']].head(10), use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'summary':
    st.markdown("## Financial Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Batches", len(selected_ids))
    col2.metric("Birds", metrics['total_sold'])
    col3.metric("Revenue", f"TZS {metrics['total_revenue']/1e6:.1f}M")
    col4.metric("Profit", f"TZS {metrics['profit']/1e6:.1f}M")

elif st.session_state.current_tab == 'operations':
    st.markdown("## Operations")
    if not batch_mortality.empty:
        st.markdown("### Mortality Records")
        st.dataframe(batch_mortality[['daterecorded', 'quantitydied', 'reason']].head(20), use_container_width=True, hide_index=True)

elif st.session_state.current_tab == 'statements':
    st.markdown("## Financial Statements")
    st.markdown(f"""
    <div class="card">
        <div style="font-weight: 600; margin-bottom: 16px;">Income Statement</div>
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
KUKU Dashboard v5.0 | SVG Icons Edition
</div>
""", unsafe_allow_html=True)
