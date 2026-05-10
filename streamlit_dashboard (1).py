#!/usr/bin/env python3
"""
KUKU FARM DASHBOARD v7.0
Fixes: CSS broad selector, expense query NULL batchid, all tabs built out, error boundaries
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
# CSS — fixed: removed broad "p, span, div" selector that broke Streamlit internals
# ============================================================================

st.markdown("""
<style>
:root {
    --bg-primary:    #0a0e27;
    --bg-secondary:  #1a1f3a;
    --accent-green:  #10b981;
    --accent-hover:  #059669;
    --text-primary:  #e6edf3;
    --text-secondary:#8b949e;
    --border-color:  #2d333b;
    --red:           #ef4444;
    --yellow:        #f59e0b;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

/* Sidebar nav buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    margin: 3px 0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(16,185,129,0.08) !important;
    border-color: var(--accent-green) !important;
    color: var(--text-primary) !important;
}

/* Page headings only — NOT broad div/span */
h1, h2, h3, h4 { color: var(--text-primary) !important; }

/* Metric cards */
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
    box-shadow: 0 4px 12px rgba(16,185,129,0.15);
    transform: translateY(-2px);
}
.metric-value {
    font-size: 22px;
    font-weight: 700;
    color: var(--accent-green);
    margin: 6px 0 2px;
}
.metric-label {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.metric-sub {
    font-size: 11px;
    color: var(--text-secondary);
}

/* Content cards */
.card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.card:hover {
    border-color: var(--accent-green);
    box-shadow: 0 4px 16px rgba(16,185,129,0.12);
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
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.card-body { padding: 4px 0; }

/* Alert badges */
.badge-red    { background:rgba(239,68,68,0.15);  color:#ef4444; border:1px solid rgba(239,68,68,0.3);  border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }
.badge-yellow { background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }
.badge-green  { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }

/* Plotly charts */
[data-testid="stPlotlyChart"] {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    padding: 8px !important;
}

/* Divider */
hr { border:none !important; height:1px !important; background-color:var(--border-color) !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PLOTLY THEME DEFAULTS
# ============================================================================

PLOT_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='#1a1f3a',
    plot_bgcolor='#0a0e27',
    font=dict(color='#e6edf3', size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#2d333b'),
    colorway=['#10b981','#f59e0b','#ef4444','#3b82f6','#8b5cf6','#ec4899'],
)

def plotly_chart(fig, height=320):
    fig.update_layout(**PLOT_LAYOUT, height=height)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# DATABASE
# ============================================================================

@st.cache_data(ttl=300)
def fetch_data(query):
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur  = conn.cursor()
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        conn.close()
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
    except Exception as e:
        st.error(f"DB Error: {e}")
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
    st.markdown("## 🐔 KUKU")
    st.markdown("<p style='color:#8b949e; font-size:12px; margin:0;'>Farm Dashboard</p>",
                unsafe_allow_html=True)
    st.divider()

    st.markdown("<p style='color:#8b949e; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;'>Navigation</p>",
                unsafe_allow_html=True)

    NAV = [
        ('overview',     '📊 Overview'),
        ('insights',     '💡 Insights'),
        ('financial',    '💰 Financial'),
        ('trends',       '📈 Trends'),
        ('summary',      '💵 Summary'),
        ('operations',   '⚙️ Operations'),
        ('statements',   '📄 Statements'),
        ('intelligence', '🧠 Intelligence'),
    ]
    for tab_id, label in NAV:
        if st.button(label, key=f"nav_{tab_id}", use_container_width=True):
            st.session_state.current_tab = tab_id

    st.divider()
    st.markdown("<p style='color:#8b949e; font-size:11px; text-transform:uppercase; letter-spacing:0.08em;'>Filters</p>",
                unsafe_allow_html=True)

    # ── Load all batches ──
    all_batches = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted, dateended, status
        FROM public.batches_detailed
        ORDER BY datestarted DESC
    """)

    if all_batches.empty:
        st.error("No batches found")
        st.stop()

    batch_map = {}
    for _, b in all_batches.iterrows():
        label = f"{b['batchname']} ({int(b['quantitychicksstarted'])} birds)"
        batch_map[label] = {
            'id':    int(b['batchid']),
            'start': pd.to_datetime(b['datestarted']).date(),
            'end':   pd.to_datetime(b['dateended']).date() if pd.notna(b['dateended']) else date.today()
        }

    st.markdown("<p style='color:#e6edf3; font-size:12px; margin-bottom:4px;'>📦 Batch (optional)</p>",
                unsafe_allow_html=True)
    selected_names = st.multiselect(
        "Batches", list(batch_map.keys()), default=[],
        label_visibility="collapsed", max_selections=5
    )
    selected_ids = [batch_map[n]['id'] for n in selected_names]

    # ── Date filter logic ──
    if selected_ids:
        dates      = [batch_map[n] for n in selected_names]
        auto_start = min(d['start'] for d in dates)
        auto_end   = max(d['end']   for d in dates)

        st.markdown(f"<p style='color:#8b949e; font-size:11px;'>Batch range: {auto_start} → {auto_end}</p>",
                    unsafe_allow_html=True)

        override = st.checkbox("📝 Custom date range?", value=False)
        if override:
            date_start = st.date_input("From", value=auto_start,
                                       min_value=auto_start, max_value=auto_end)
            date_end   = st.date_input("To",   value=auto_end,
                                       min_value=auto_start, max_value=auto_end)
        else:
            date_start, date_end = auto_start, auto_end
            st.success("✅ Using batch date range")
    else:
        st.markdown("<p style='color:#e6edf3; font-size:12px; margin-bottom:4px;'>📅 Date range</p>",
                    unsafe_allow_html=True)
        date_start = st.date_input("From", value=date.today() - timedelta(days=90),
                                   label_visibility="collapsed")
        date_end   = st.date_input("To",   value=date.today(),
                                   label_visibility="collapsed")
        if date_start and date_end:
            st.info("📌 All batches in this date range")
        else:
            st.warning("⚠️ Select a batch or date range")

# ============================================================================
# HEADER
# ============================================================================

c1, c2 = st.columns([0.06, 1])
with c1:
    st.markdown("<div style='font-size:40px;margin-top:4px;'>🐔</div>", unsafe_allow_html=True)
with c2:
    st.markdown("# KUKU Farm Dashboard")
    st.markdown(
        f"<p style='color:#8b949e;font-size:12px;margin:0;'>"
        f"{'Batches: ' + ', '.join(selected_names) if selected_names else 'All batches'}"
        f" &nbsp;|&nbsp; {date_start} → {date_end}</p>",
        unsafe_allow_html=True
    )

st.divider()

# ── No filter warning ──
if not selected_ids and not (date_start and date_end):
    st.warning("👈 Select a batch or date range to view data")
    st.stop()

# ============================================================================
# BUILD SQL FILTERS
# ============================================================================

if selected_ids:
    ids_str       = ','.join(str(i) for i in selected_ids)
    sales_filter  = f"AND ds.batchid IN ({ids_str})"
    # For expenses/feed/mortality: include batch-specific AND NULL batchid (farm-wide)
    batch_filter  = f"AND (batchid IN ({ids_str}) OR batchid IS NULL)"
    # For feed log and mortality: batch-specific only (no NULL batchid concept)
    strict_filter = f"AND batchid IN ({ids_str})"
else:
    sales_filter  = ""
    batch_filter  = ""
    strict_filter = ""

ds = f"'{date_start}'"
de = f"'{date_end}'"

# ============================================================================
# FETCH DATA
# ============================================================================

sales_df = fetch_data(f"""
    SELECT ds.saleid, ds.batchid, ds.datesold, ds.quantitysold,
           ds.unitprice, ds.totalrevenue, ds.salestatus, ds.notes,
           b.buyername
    FROM public.daily_sales ds
    LEFT JOIN public.buyers b ON ds.buyerid = b.buyerid
    WHERE 1=1 {sales_filter}
    AND ds.datesold BETWEEN {ds} AND {de}
    ORDER BY ds.datesold
""")

# Expenses: batch-specific + farm-wide (NULL batchid), exclude Feed Purchase
expenses_df = fetch_data(f"""
    SELECT expense_id, expensedate, category, description, amount, batchid
    FROM public.expenses
    WHERE category != 'Feed Purchase'
    {batch_filter}
    AND expensedate BETWEEN {ds} AND {de}
""")

# Feed log: actual costs from daily feed log (strict batch only)
feed_log_df = fetch_data(f"""
    SELECT fl.feedlogid, fl.batchid, fl.datefed, fl.quantitykg,
           fl.feedcost, f.feedtype
    FROM public.daily_feed_log fl
    LEFT JOIN public.feeds f ON fl.feedtypeid = f.feedid
    WHERE 1=1 {strict_filter}
    AND fl.datefed BETWEEN {ds} AND {de}
""")

mortality_df = fetch_data(f"""
    SELECT mortalityid, batchid, daterecorded, quantitydied, reason
    FROM public.daily_mortality
    WHERE 1=1 {strict_filter}
    AND daterecorded BETWEEN {ds} AND {de}
""")

events_df = fetch_data(f"""
    SELECT eventid, batchid, eventdate, eventtype, severity, description
    FROM public.critical_events
    WHERE 1=1 {strict_filter}
    AND eventdate BETWEEN {ds} AND {de}
    ORDER BY eventdate DESC
""")

weight_df = fetch_data(f"""
    SELECT ws.sessionid, ws.batchid, ws.sessiondate, ws.dayofcycle,
           ws.averageweightperbird, ws.samplesize
    FROM public.weight_sessions ws
    WHERE 1=1 {strict_filter}
    AND ws.sessiondate BETWEEN {ds} AND {de}
    ORDER BY ws.sessiondate
""")

# ============================================================================
# METRICS
# ============================================================================

def safe_int(val):
    try: return int(val) if pd.notna(val) else 0
    except: return 0

def get_metrics():
    empty = dict(total_sold=0, total_revenue=0, feed_cost=0,
                 other_expenses=0, op_expenses=0, total_expenses=0, chick_cost=0,
                 profit=0, gross_profit=0, gross_margin=0, margin=0,
                 unique_buyers=0, concentration=0, avg_price=0, demand_score=50)
    if sales_df.empty:
        return empty

    total_sold    = safe_int(sales_df['quantitysold'].sum())
    total_revenue = safe_int(sales_df['totalrevenue'].sum())
    feed_cost     = safe_int(feed_log_df['feedcost'].sum()) if not feed_log_df.empty else 0

    # Split other expenses: chick purchases are COGS, rest are operating
    chick_cost    = 0
    op_expenses   = 0
    if not expenses_df.empty:
        chick_mask  = expenses_df['category'].str.lower().str.contains('chick', na=False)
        chick_cost  = safe_int(expenses_df.loc[chick_mask, 'amount'].sum())
        op_expenses = safe_int(expenses_df.loc[~chick_mask, 'amount'].sum())

    other_expenses  = safe_int(expenses_df['amount'].sum()) if not expenses_df.empty else 0
    total_expenses  = feed_cost + other_expenses

    gross_profit  = total_revenue - feed_cost - chick_cost
    gross_margin  = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    profit        = total_revenue - total_expenses
    margin        = (profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_price     = float(sales_df['unitprice'].mean()) if not sales_df.empty else 0

    unique_buyers = safe_int(sales_df['batchid'].nunique()) if 'buyername' in sales_df else 0
    try:
        buyer_q   = sales_df.groupby('buyername')['quantitysold'].sum().sort_values(ascending=False)
        top3      = safe_int(buyer_q.head(3).sum())
        concentration = (top3 / total_sold * 100) if total_sold > 0 else 0
        unique_buyers = len(buyer_q)
    except:
        concentration = 0

    demand_score = 85 if concentration < 40 else 75 if concentration < 60 else 60 if concentration < 75 else 45

    return dict(
        total_sold=total_sold, total_revenue=total_revenue,
        feed_cost=feed_cost, chick_cost=chick_cost,
        other_expenses=other_expenses, op_expenses=op_expenses,
        total_expenses=total_expenses,
        gross_profit=gross_profit, gross_margin=gross_margin,
        profit=profit, margin=margin,
        unique_buyers=unique_buyers, concentration=concentration,
        avg_price=avg_price, demand_score=demand_score
    )

M = get_metrics()
birds = M['total_sold'] if M['total_sold'] > 0 else 1

# ============================================================================
# HELPER: metric card HTML
# ============================================================================

def mcard(label, value, sub="", color="var(--accent-green)"):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>"""

# ============================================================================
# TAB: OVERVIEW
# ============================================================================

if st.session_state.current_tab == 'overview':
    try:
        st.markdown("## 📊 Overview")

        cols = st.columns(6)
        cards = [
            ("Birds Sold",   f"{M['total_sold']:,}",                  f"Avg TZS {M['avg_price']:,.0f}/bird"),
            ("Revenue",      f"TZS {M['total_revenue']/1e6:.2f}M",    "Gross revenue"),
            ("Feed Cost",    f"TZS {M['feed_cost']/1e6:.2f}M",        f"TZS {M['feed_cost']//birds:,}/bird", "#f59e0b"),
            ("Other Costs",  f"TZS {M['other_expenses']/1e6:.2f}M",   "Operating"),
            ("Net Profit",   f"TZS {M['profit']/1e6:.2f}M",           f"Margin {M['margin']:.1f}%",
             "#10b981" if M['profit'] >= 0 else "#ef4444"),
            ("Buyers",       str(M['unique_buyers']),                  f"Conc. {M['concentration']:.0f}%"),
        ]
        for col, card in zip(cols, cards):
            with col:
                st.markdown(mcard(*card), unsafe_allow_html=True)

        if not sales_df.empty:
            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown("### Sales Trend")
                daily = sales_df.groupby('datesold').agg(
                    birds=('quantitysold','sum'),
                    revenue=('totalrevenue','sum')
                ).reset_index()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily['datesold'], y=daily['birds'],
                    name='Birds Sold', mode='lines+markers', fill='tozeroy',
                    line=dict(color='#10b981', width=2),
                    fillcolor='rgba(16,185,129,0.08)'
                ))
                fig.update_layout(**PLOT_LAYOUT, height=280,
                                  xaxis_title="", yaxis_title="Birds",
                                  margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("### Cost Breakdown")
                if M['total_expenses'] > 0:
                    labels = ['Feed', 'Chicks', 'Operating']
                    values = [M['feed_cost'], M['chick_cost'], M['op_expenses']]
                    colors = ['#10b981', '#3b82f6', '#f59e0b']
                    fig2 = go.Figure(go.Pie(
                        labels=labels, values=values,
                        hole=0.55, marker_colors=colors,
                        textinfo='percent', textfont_size=12
                    ))
                    fig2.update_layout(**PLOT_LAYOUT, height=280,
                                       margin=dict(l=10,r=10,t=10,b=10),
                                       showlegend=True)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No expense data yet")

            if not mortality_df.empty:
                st.markdown("### Mortality Trend")
                daily_m = mortality_df.groupby('daterecorded')['quantitydied'].sum().reset_index()
                fig3 = go.Figure(go.Bar(
                    x=daily_m['daterecorded'], y=daily_m['quantitydied'],
                    marker_color='#ef4444', opacity=0.7
                ))
                fig3.update_layout(**PLOT_LAYOUT, height=180,
                                   margin=dict(l=10,r=10,t=10,b=10),
                                   xaxis_title="", yaxis_title="Deaths")
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No sales data for the selected filters")
    except Exception as e:
        st.error(f"Overview error: {e}")

# ============================================================================
# TAB: INSIGHTS
# ============================================================================

elif st.session_state.current_tab == 'insights':
    try:
        st.markdown("## 💡 Insights")

        # ── Alert badges ──
        alerts = []
        if M['concentration'] > 75:
            alerts.append(("🔴 CRITICAL: Buyer concentration " + f"{M['concentration']:.0f}%", "red"))
        elif M['concentration'] > 60:
            alerts.append((f"🟡 HIGH: Buyer concentration {M['concentration']:.0f}%", "yellow"))

        total_dead = safe_int(mortality_df['quantitydied'].sum()) if not mortality_df.empty else 0
        if selected_ids and not all_batches.empty:
            total_started = safe_int(
                all_batches.loc[all_batches['batchid'].isin(selected_ids), 'quantitychicksstarted'].sum()
            )
            mortality_rate = (total_dead / total_started * 100) if total_started > 0 else 0
            if mortality_rate >= 5:
                alerts.append((f"🔴 Mortality rate {mortality_rate:.1f}% — above 5% threshold", "red"))
            elif mortality_rate >= 3:
                alerts.append((f"🟡 Mortality rate {mortality_rate:.1f}% — watch closely", "yellow"))

        if M['margin'] < 10:
            alerts.append((f"🔴 Net margin {M['margin']:.1f}% — critically low", "red"))
        elif M['margin'] < 20:
            alerts.append((f"🟡 Net margin {M['margin']:.1f}% — below target", "yellow"))

        if alerts:
            st.markdown("### ⚠️ Active Alerts")
            for msg, color in alerts:
                st.markdown(f'<span class="badge-{color}">{msg}</span><br>', unsafe_allow_html=True)
            st.markdown("")
        else:
            st.success("✅ No critical alerts for the selected period")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Buyer Concentration")
            if not sales_df.empty:
                buyer_vol = sales_df.groupby('buyername')['quantitysold'].sum().sort_values(ascending=False).head(8)
                fig = go.Figure(go.Bar(
                    x=buyer_vol.values, y=buyer_vol.index,
                    orientation='h',
                    marker_color=['#ef4444' if i == 0 else '#f59e0b' if i < 3 else '#10b981'
                                  for i in range(len(buyer_vol))]
                ))
                fig.update_layout(**PLOT_LAYOUT, height=300,
                                  xaxis_title="Birds Sold",
                                  margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

                top3_pct = M['concentration']
                color = "badge-red" if top3_pct > 75 else "badge-yellow" if top3_pct > 60 else "badge-green"
                st.markdown(
                    f'Top 3 buyers: <span class="{color}">{top3_pct:.0f}% of volume</span>',
                    unsafe_allow_html=True
                )

        with c2:
            st.markdown("### Demand Score")
            score = M['demand_score']
            color = '#10b981' if score >= 80 else '#f59e0b' if score >= 60 else '#ef4444'
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                gauge=dict(
                    axis=dict(range=[0,100], tickcolor='#e6edf3'),
                    bar=dict(color=color),
                    steps=[
                        dict(range=[0,60],  color='rgba(239,68,68,0.15)'),
                        dict(range=[60,80], color='rgba(245,158,11,0.15)'),
                        dict(range=[80,100],color='rgba(16,185,129,0.15)'),
                    ],
                    threshold=dict(line=dict(color=color,width=3), value=score)
                ),
                number=dict(font=dict(color=color, size=36)),
                title=dict(text="Demand Score", font=dict(color='#8b949e'))
            ))
            fig2.update_layout(**PLOT_LAYOUT, height=300,
                               margin=dict(l=20,r=20,t=30,b=10))
            st.plotly_chart(fig2, use_container_width=True)

            label = "🟢 Scale up" if score >= 85 else "🟡 Normal" if score >= 70 else "🟠 Reduce" if score >= 60 else "🔴 Don't place"
            st.markdown(f"**Recommendation:** {label}")

    except Exception as e:
        st.error(f"Insights error: {e}")

# ============================================================================
# TAB: FINANCIAL
# ============================================================================

elif st.session_state.current_tab == 'financial':
    try:
        st.markdown("## 💰 Financial Analysis")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(mcard("Revenue/Bird", f"TZS {M['total_revenue']//birds:,}", "Avg selling price"), unsafe_allow_html=True)
        with c2:
            st.markdown(mcard("Cost/Bird", f"TZS {M['total_expenses']//birds:,}", "Total cost per bird", "#f59e0b"), unsafe_allow_html=True)
        with c3:
            st.markdown(mcard("Profit/Bird", f"TZS {M['profit']//birds:,}", f"Margin {M['margin']:.1f}%",
                              "#10b981" if M['profit']//birds >= 0 else "#ef4444"), unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Revenue vs Cost Over Time")
            if not sales_df.empty:
                daily_rev = sales_df.groupby('datesold')['totalrevenue'].sum().reset_index()
                daily_rev.columns = ['date', 'revenue']

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_rev['date'], y=daily_rev['revenue'],
                    name='Revenue', mode='lines+markers', fill='tozeroy',
                    line=dict(color='#10b981', width=2),
                    fillcolor='rgba(16,185,129,0.08)'
                ))

                if not feed_log_df.empty:
                    daily_feed = feed_log_df.groupby('datefed')['feedcost'].sum().reset_index()
                    daily_feed.columns = ['date','cost']
                    fig.add_trace(go.Scatter(
                        x=daily_feed['date'], y=daily_feed['cost'],
                        name='Feed Cost', mode='lines+markers',
                        line=dict(color='#f59e0b', width=2, dash='dot')
                    ))

                fig.update_layout(**PLOT_LAYOUT, height=300,
                                  xaxis_title="", yaxis_title="TZS")
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("### Expense Categories")
            if not expenses_df.empty:
                cat_df = expenses_df.groupby('category')['amount'].sum().reset_index()
                cat_df = cat_df.sort_values('amount', ascending=True)
                fig2 = go.Figure(go.Bar(
                    x=cat_df['amount'], y=cat_df['category'],
                    orientation='h', marker_color='#3b82f6'
                ))
                fig2.update_layout(**PLOT_LAYOUT, height=300,
                                   xaxis_title="TZS", margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No expense data for this period")

        # ── FCR Table ──
        st.markdown("### FCR Benchmarks")
        fcr_df = pd.DataFrame({
            'FCR':        [1.10, 1.20, 1.32, 1.40, 1.45],
            'Profit/Bird':[1696, 1532, 1335, 1204, 1122],
            'Feed Cost/Bird':['TZS 1,815','TZS 1,980','TZS 2,178','TZS 2,310','TZS 2,393'],
            'Status':     ['🟢 Elite','🟢 Good','🟡 Watch','🟡 Marginal','🔴 Poor']
        })
        st.dataframe(fcr_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Financial error: {e}")

# ============================================================================
# TAB: TRENDS
# ============================================================================

elif st.session_state.current_tab == 'trends':
    try:
        st.markdown("## 📈 Trends")

        if not sales_df.empty:
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("### Daily Birds Sold")
                daily = sales_df.groupby('datesold')['quantitysold'].sum().reset_index()
                fig = go.Figure(go.Scatter(
                    x=daily['datesold'], y=daily['quantitysold'],
                    mode='lines+markers', fill='tozeroy',
                    line=dict(color='#10b981', width=2),
                    fillcolor='rgba(16,185,129,0.08)'
                ))
                fig.update_layout(**PLOT_LAYOUT, height=260,
                                  margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("### Daily Revenue")
                daily_r = sales_df.groupby('datesold')['totalrevenue'].sum().reset_index()
                fig2 = go.Figure(go.Scatter(
                    x=daily_r['datesold'], y=daily_r['totalrevenue'],
                    mode='lines+markers', fill='tozeroy',
                    line=dict(color='#3b82f6', width=2),
                    fillcolor='rgba(59,130,246,0.08)'
                ))
                fig2.update_layout(**PLOT_LAYOUT, height=260,
                                   margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig2, use_container_width=True)

        if not feed_log_df.empty:
            st.markdown("### Feed Consumption & Cost")
            c1, c2 = st.columns(2)
            with c1:
                daily_feed = feed_log_df.groupby('datefed')['quantitykg'].sum().reset_index()
                fig3 = go.Figure(go.Bar(
                    x=daily_feed['datefed'], y=daily_feed['quantitykg'],
                    marker_color='#f59e0b', opacity=0.8
                ))
                fig3.update_layout(**PLOT_LAYOUT, height=220,
                                   yaxis_title="kg",
                                   margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig3, use_container_width=True)
            with c2:
                daily_fc = feed_log_df.groupby('datefed')['feedcost'].sum().reset_index()
                fig4 = go.Figure(go.Bar(
                    x=daily_fc['datefed'], y=daily_fc['feedcost'],
                    marker_color='#8b5cf6', opacity=0.8
                ))
                fig4.update_layout(**PLOT_LAYOUT, height=220,
                                   yaxis_title="TZS",
                                   margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig4, use_container_width=True)

        if not mortality_df.empty:
            st.markdown("### Mortality Trend")
            daily_m = mortality_df.groupby('daterecorded')['quantitydied'].sum().reset_index()
            fig5 = go.Figure(go.Bar(
                x=daily_m['daterecorded'], y=daily_m['quantitydied'],
                marker_color='#ef4444', opacity=0.7
            ))
            fig5.update_layout(**PLOT_LAYOUT, height=200,
                               yaxis_title="Deaths",
                               margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig5, use_container_width=True)

        if not weight_df.empty:
            st.markdown("### Average Weight Progress")
            fig6 = go.Figure()
            fig6.add_trace(go.Scatter(
                x=weight_df['sessiondate'], y=weight_df['averageweightperbird'],
                mode='lines+markers',
                line=dict(color='#10b981', width=2),
                marker=dict(size=7)
            ))
            # Target reference line
            for day, target in [(7, 200), (14, 550), (21, 1250)]:
                fig6.add_hline(y=target, line_dash="dot", line_color="#8b949e",
                               annotation_text=f"Day {day} target: {target}g")
            fig6.update_layout(**PLOT_LAYOUT, height=250,
                               yaxis_title="Grams",
                               margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig6, use_container_width=True)

        if sales_df.empty and feed_log_df.empty and mortality_df.empty:
            st.info("No trend data for the selected filters")

        if not events_df.empty:
            st.markdown("### Critical Events")
            st.dataframe(
                events_df[['eventdate','eventtype','severity','description']],
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Trends error: {e}")

# ============================================================================
# TAB: SUMMARY
# ============================================================================

elif st.session_state.current_tab == 'summary':
    try:
        st.markdown("## 💵 Batch Summary")

        # ── Top-line metrics ──
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(mcard("Batches", len(selected_ids) if selected_ids else "All", "selected"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Birds Sold", f"{M['total_sold']:,}", f"@ TZS {M['avg_price']:,.0f}"), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Revenue", f"TZS {M['total_revenue']/1e6:.2f}M", "gross"), unsafe_allow_html=True)
        with c4: st.markdown(mcard("Expenses", f"TZS {M['total_expenses']/1e6:.2f}M", "all costs"), unsafe_allow_html=True)
        with c5: st.markdown(mcard("Net Profit", f"TZS {M['profit']/1e6:.2f}M",
                                   f"Margin {M['margin']:.1f}%",
                                   "#10b981" if M['profit'] >= 0 else "#ef4444"), unsafe_allow_html=True)

        st.divider()

        # ── Per-batch breakdown table ──
        if selected_ids and not sales_df.empty:
            st.markdown("### Per-Batch Performance")
            rows = []
            for bid in selected_ids:
                batch_info = all_batches[all_batches['batchid'] == bid].iloc[0]
                s = sales_df[sales_df['batchid'] == bid]
                f = feed_log_df[feed_log_df['batchid'] == bid] if not feed_log_df.empty else pd.DataFrame()
                e = expenses_df[expenses_df['batchid'] == bid] if not expenses_df.empty else pd.DataFrame()

                rev  = safe_int(s['totalrevenue'].sum())
                sold = safe_int(s['quantitysold'].sum())
                fc   = safe_int(f['feedcost'].sum()) if not f.empty else 0
                oe   = safe_int(e['amount'].sum()) if not e.empty else 0
                prof = rev - fc - oe
                rows.append({
                    'Batch':    batch_info['batchname'],
                    'Birds':    sold,
                    'Revenue':  f"TZS {rev:,}",
                    'Feed':     f"TZS {fc:,}",
                    'Other':    f"TZS {oe:,}",
                    'Profit':   f"TZS {prof:,}",
                    'Margin':   f"{(prof/rev*100):.1f}%" if rev > 0 else "—",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Summary error: {e}")

# ============================================================================
# TAB: OPERATIONS
# ============================================================================

elif st.session_state.current_tab == 'operations':
    try:
        st.markdown("## ⚙️ Operations")

        total_dead    = safe_int(mortality_df['quantitydied'].sum()) if not mortality_df.empty else 0
        total_started = 0
        if selected_ids and not all_batches.empty:
            total_started = safe_int(
                all_batches.loc[all_batches['batchid'].isin(selected_ids), 'quantitychicksstarted'].sum()
            )
        mortality_rate = (total_dead / total_started * 100) if total_started > 0 else 0
        mort_color = "#ef4444" if mortality_rate >= 5 else "#f59e0b" if mortality_rate >= 3 else "#10b981"

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(mcard("Total Deaths", f"{total_dead:,}", f"of {total_started:,} started"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Mortality Rate", f"{mortality_rate:.2f}%", "Target < 3%", mort_color), unsafe_allow_html=True)
        with c3:
            avg_weight = float(weight_df['averageweightperbird'].mean()) if not weight_df.empty else 0
            st.markdown(mcard("Avg Weight", f"{avg_weight:.0f}g" if avg_weight > 0 else "—", "Latest session avg"), unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Mortality by Reason")
            if not mortality_df.empty:
                reason_df = mortality_df.groupby('reason')['quantitydied'].sum().reset_index()
                fig = go.Figure(go.Pie(
                    labels=reason_df['reason'], values=reason_df['quantitydied'],
                    hole=0.5, textinfo='percent+label'
                ))
                fig.update_layout(**PLOT_LAYOUT, height=280,
                                  margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No mortality records")

        with c2:
            st.markdown("### Weight Sessions")
            if not weight_df.empty:
                targets = {7: 200, 14: 550, 21: 1250}
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=weight_df['sessiondate'], y=weight_df['averageweightperbird'],
                    name='Actual', mode='lines+markers',
                    line=dict(color='#10b981', width=2), marker=dict(size=7)
                ))
                for day, tgt in targets.items():
                    fig2.add_hline(y=tgt, line_dash="dot", line_color="#f59e0b",
                                   annotation_text=f"D{day}:{tgt}g")
                fig2.update_layout(**PLOT_LAYOUT, height=280,
                                   yaxis_title="grams",
                                   margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No weight sessions")

        if not mortality_df.empty:
            st.markdown("### Mortality Records")
            st.dataframe(
                mortality_df[['daterecorded','batchid','quantitydied','reason']].sort_values('daterecorded', ascending=False),
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Operations error: {e}")

# ============================================================================
# TAB: STATEMENTS
# ============================================================================

elif st.session_state.current_tab == 'statements':
    try:
        st.markdown("## 📄 Financial Statements")

        gross_profit  = M['total_revenue'] - M['feed_cost'] - M['chick_cost']
        gross_margin  = (gross_profit / M['total_revenue'] * 100) if M['total_revenue'] > 0 else 0
        batch_label   = f"{len(selected_ids)} batch(es)" if selected_ids else "All batches"
        net_color_hex = '#10b981' if M['profit'] >= 0 else '#ef4444'
        gp_color_hex  = '#10b981' if gross_profit >= 0 else '#ef4444'

        # ── Income Statement as Plotly Table (always renders reliably) ──
        labels  = [
            'REVENUE',
            'Bird Sales',
            'GROSS REVENUE',
            '',
            'COST OF PRODUCTION',
            'Chick Purchase',
            'Feed Costs',
            'GROSS PROFIT',
            '',
            'OPERATING EXPENSES',
            'Other Expenses',
            'Total Expenses',
            '',
            'NET PROFIT',
            'Net Margin',
        ]
        amounts = [
            '',
            f"TZS {M['total_revenue']:,}",
            f"TZS {M['total_revenue']:,}",
            '',
            '',
            f"TZS {M['chick_cost']:,}",
            f"TZS {M['feed_cost']:,}",
            f"TZS {gross_profit:,}",
            '',
            '',
            f"TZS {M['op_expenses']:,}",
            f"TZS {M['total_expenses']:,}",
            '',
            f"TZS {M['profit']:,}",
            f"{M['margin']:.1f}%",
        ]
        per_bird = [
            '',
            f"TZS {M['total_revenue']//birds:,}/bird",
            '',
            '',
            '',
            f"TZS {M['chick_cost']//birds:,}/bird",
            f"TZS {M['feed_cost']//birds:,}/bird",
            f"Margin: {gross_margin:.1f}%",
            '',
            '',
            f"TZS {M['op_expenses']//birds:,}/bird",
            '',
            '',
            f"TZS {M['profit']//birds:,}/bird",
            '',
        ]

        # Row colours
        section_rows  = {0, 4, 9}    # section headers — subtle gray
        total_rows    = {2, 7, 11}   # subtotals — slightly lighter
        net_row       = {13, 14}     # net profit rows

        row_fill  = []
        font_cols = []
        for i, lbl in enumerate(labels):
            if i in section_rows:
                row_fill.append('#0f1427')
                font_cols.append('#8b949e')
            elif i in net_row:
                row_fill.append('#0d2e1f')
                font_cols.append(net_color_hex)
            elif i in total_rows:
                row_fill.append('#131b35')
                font_cols.append('#e6edf3')
            elif lbl == '':
                row_fill.append('#0a0e27')
                font_cols.append('#0a0e27')
            else:
                row_fill.append('#1a1f3a')
                font_cols.append('#e6edf3')

        fig = go.Figure(go.Table(
            columnwidth=[3, 2, 2],
            header=dict(
                values=[
                    f'<b>{batch_label} | {M["total_sold"]:,} birds | {date_start} → {date_end}</b>',
                    '<b>Amount (TZS)</b>',
                    '<b>Per Bird</b>'
                ],
                fill_color='#0f1427',
                font=dict(color=['#10b981','#8b949e','#8b949e'], size=[13,12,12]),
                line_color='#2d333b',
                align=['left','right','right'],
                height=36
            ),
            cells=dict(
                values=[labels, amounts, per_bird],
                fill_color=[row_fill, row_fill, row_fill],
                font=dict(color=[font_cols, font_cols, font_cols], size=13),
                line_color='#2d333b',
                align=['left','right','right'],
                height=32
            )
        ))
        fig.update_layout(
            paper_bgcolor='#1a1f3a',
            margin=dict(l=0, r=0, t=0, b=0),
            height=580
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Expense breakdown bars ──
        if M['total_expenses'] > 0:
            st.markdown("### Expense Breakdown")
            items = [
                ("Chick Purchase", M['chick_cost'],   '#3b82f6'),
                ("Feed Costs",     M['feed_cost'],     '#10b981'),
                ("Operating",      M['op_expenses'],   '#f59e0b'),
            ]
            for name, amt, col in items:
                if amt > 0:
                    pct = amt / M['total_expenses'] * 100
                    c1, c2, c3 = st.columns([2, 4, 1])
                    with c1:
                        st.markdown(
                            f"<p style='color:#e6edf3;font-size:13px;margin:6px 0;'>{name}</p>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        st.progress(int(pct))
                    with c3:
                        st.markdown(
                            f"<p style='color:#8b949e;font-size:12px;margin:6px 0;'>{pct:.0f}%</p>",
                            unsafe_allow_html=True
                        )

        # ── Expense detail table ──
        if not expenses_df.empty:
            st.markdown("### Expense Detail")
            disp = expenses_df[['expensedate','category','description','amount']].copy()
            disp = disp.sort_values('expensedate', ascending=False)
            disp['amount'] = disp['amount'].apply(lambda x: f"TZS {int(x):,}")
            st.dataframe(disp, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Statements error: {e}")

elif st.session_state.current_tab == 'intelligence':
    try:
        st.markdown("## 🧠 Market Intelligence")

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(mcard("Unique Buyers", M['unique_buyers'], "active"), unsafe_allow_html=True)
        with c2:
            cc = "#ef4444" if M['concentration'] > 75 else "#f59e0b" if M['concentration'] > 60 else "#10b981"
            st.markdown(mcard("Concentration", f"{M['concentration']:.0f}%", "Top 3 buyers", cc), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Avg Price", f"TZS {M['avg_price']:,.0f}", "per bird"), unsafe_allow_html=True)
        with c4:
            sc = "#10b981" if M['demand_score'] >= 80 else "#f59e0b" if M['demand_score'] >= 60 else "#ef4444"
            st.markdown(mcard("Demand Score", M['demand_score'], "/100", sc), unsafe_allow_html=True)

        if not sales_df.empty:
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("### Buyer Volume Ranking")
                buyer_df = sales_df.groupby('buyername').agg(
                    birds=('quantitysold','sum'),
                    revenue=('totalrevenue','sum'),
                    transactions=('saleid','count')
                ).sort_values('birds', ascending=False).reset_index()

                fig = go.Figure(go.Bar(
                    x=buyer_df['birds'].head(10),
                    y=buyer_df['buyername'].head(10),
                    orientation='h',
                    marker_color=['#ef4444' if i == 0 else '#f59e0b' if i < 3 else '#10b981'
                                  for i in range(min(10, len(buyer_df)))],
                    text=[f"TZS {r/1e6:.1f}M" for r in buyer_df['revenue'].head(10)],
                    textposition='outside'
                ))
                fig.update_layout(**PLOT_LAYOUT, height=320,
                                  xaxis_title="Birds Sold",
                                  margin=dict(l=10,r=80,t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown("### Revenue Share")
                top_buyers = buyer_df.head(6)
                if len(buyer_df) > 6:
                    others_rev = buyer_df.iloc[6:]['revenue'].sum()
                    others_row = pd.DataFrame([{'buyername': 'Others', 'revenue': others_rev}])
                    top_buyers = pd.concat([top_buyers, others_row], ignore_index=True)

                fig2 = go.Figure(go.Pie(
                    labels=top_buyers['buyername'],
                    values=top_buyers['revenue'],
                    hole=0.5, textinfo='percent',
                ))
                fig2.update_layout(**PLOT_LAYOUT, height=320,
                                   margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### Buyer Detail")
            buyer_df['Revenue'] = buyer_df['revenue'].apply(lambda x: f"TZS {x:,}")
            buyer_df['Avg Price/Bird'] = (buyer_df['revenue'] / buyer_df['birds']).apply(lambda x: f"TZS {x:,.0f}")
            buyer_df = buyer_df.rename(columns={'buyername':'Buyer','birds':'Birds','transactions':'Transactions'})
            st.dataframe(buyer_df[['Buyer','Birds','Revenue','Transactions','Avg Price/Bird']],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No sales data for the selected filters")

    except Exception as e:
        st.error(f"Intelligence error: {e}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    "<p style='text-align:center;color:#8b949e;font-size:11px;padding:8px 0;'>"
    "KUKU Dashboard v7.0 | All tabs active | Actual feed costs</p>",
    unsafe_allow_html=True
)
