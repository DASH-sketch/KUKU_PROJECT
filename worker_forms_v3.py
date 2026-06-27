#!/usr/bin/env python3
"""
KUKU PROJECT - Worker Forms v3.0
Changes from v2:
1. Weight tab: wrapped in st.form() (no reload per entry), blank fields, stats shown after submit
2. Expenses tab: universal quantity + unit + unit_price fields (optional), auto-calculates amount
3. Feed Log tab: auto-calculates cost from batch's feed purchase in expenses table, warns if missing
4. CSS: form label visibility fixed (bright white labels)
"""

import streamlit as st
import psycopg2
import os
from datetime import datetime, date

st.set_page_config(
    page_title="KUKU Worker Forms",
    page_icon="🐔",
    layout="wide"
)

# Edit mode session state keys
for _k in ['edit_sale_id','edit_sale_date','edit_sale_batch','edit_sale_buyer',
           'edit_sale_qty','edit_sale_price','edit_sale_status','edit_sale_notes',
           'edit_feed_id','edit_feed_date','edit_feed_batch','edit_feed_type',
           'edit_feed_qty','edit_feed_notes',
           'edit_mort_id','edit_mort_date','edit_mort_batch','edit_mort_qty',
           'edit_mort_reason','edit_mort_notes',
           'edit_exp_id','edit_exp_date','edit_exp_batch','edit_exp_cat',
           'edit_exp_desc','edit_exp_qty','edit_exp_uprice','edit_exp_notes']:
    if _k not in st.session_state:
        st.session_state[_k] = None

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    body { background-color: #0F172A; color: #F1F5F9; }

    /* ── FIX: Make ALL form labels bright and readable ── */
    label, label p,
    .stSelectbox label, .stSelectbox label p,
    .stNumberInput label, .stNumberInput label p,
    .stTextInput label, .stTextInput label p,
    .stDateInput label, .stDateInput label p,
    .stTextArea label, .stTextArea label p,
    .stCheckbox label, .stCheckbox label p,
    div[data-testid="stWidgetLabel"] p {
        color: #E8E8E8 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    .stSelectbox > div, .stNumberInput > div, .stTextInput > div {
        background-color: #1E293B;
    }

    .form-header {
        background: linear-gradient(135deg, #064E3B, #065F46);
        padding: 20px 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        border-left: 5px solid #10B981;
    }

    .form-header h2 {
        color: #10B981;
        margin: 0;
        font-size: 22px;
    }

    .form-header p {
        color: #94A3B8;
        margin: 5px 0 0 0;
        font-size: 13px;
    }

    .stat-box {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }

    .stat-label {
        color: #94A3B8;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stat-value {
        font-size: 22px;
        font-weight: 700;
        margin-top: 5px;
    }

    .status-green { color: #10B981; }
    .status-yellow { color: #F59E0B; }
    .status-red { color: #EF4444; }

    .recent-entries {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-top: 24px;
    }
    .recent-title {
        color: #94A3B8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .success-box {
        background: #064E3B;
        border: 1px solid #10B981;
        border-radius: 10px;
        padding: 15px 20px;
        color: #10B981;
        font-weight: 600;
    }

    .warn-box {
        background: #1c1a07;
        border: 1px solid #F59E0B;
        border-radius: 10px;
        padding: 15px 20px;
        color: #F59E0B;
        font-weight: 500;
    }

    div[data-testid="stForm"] {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 25px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 25px;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #059669, #047857);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE
# ============================================================================

def fresh_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@st.cache_data(ttl=30)
def fetch_recent(query):
    """
    Fetch recent records with 30-second cache.
    Without caching, all 7 tab queries fired on every keystroke causing page unresponsive errors.
    30s TTL means new entries appear within 30 seconds of saving - acceptable for recent history.
    """
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        c.close()
        import pandas as pd
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
    except:
        return None

def get_active_batches():
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("""
            SELECT batchid, batchname, quantitychicksstarted, datestarted
            FROM public.batches_detailed
            ORDER BY datestarted DESC
        """)
        rows = cur.fetchall()
        c.close()
        return rows
    except:
        return []

def get_expense_categories():
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("SELECT category_name FROM public.expense_categories ORDER BY category_name")
        rows = [r[0] for r in cur.fetchall()]
        c.close()
        return rows if rows else ['Feed Purchase', 'Salaries', 'Transport',
                                   'Medicines', 'Equipment', 'Electricity Bill',
                                   'Construction', 'Miscellaneous']
    except:
        return ['Feed Purchase', 'Salaries', 'Transport', 'Medicines',
                'Equipment', 'Electricity Bill', 'Construction', 'Miscellaneous']

def get_buyers():
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("""
            SELECT buyerid, buyername, location
            FROM public.buyers
            WHERE status = 'Active' OR status IS NULL
            ORDER BY buyername ASC
        """)
        rows = cur.fetchall()
        c.close()
        return rows
    except:
        return []

def get_feed_types():
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("SELECT feedid, feedtype FROM public.feeds ORDER BY feedtype")
        rows = cur.fetchall()
        c.close()
        return rows if rows else [(1, 'Starter'), (2, 'Grower'), (3, 'Finisher')]
    except:
        return [(1, 'Starter'), (2, 'Grower'), (3, 'Finisher')]

def get_batch_feed_unit_cost(batchid, feedid):
    """
    Fetch most recent feed purchase price for this batch + feed type
    from batch_feed_prices table (populated when feed purchase is recorded).
    Returns dict with unit_cost_per_kg and purchase info, or None.
    """
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("""
            SELECT
                bfp.unit_cost_per_kg,
                bfp.purchase_date,
                e.quantity   AS bags,
                e.unit_price AS price_per_bag,
                e.amount     AS total_cost
            FROM public.batch_feed_prices bfp
            LEFT JOIN public.expenses e ON bfp.expense_id = e.expense_id
            WHERE bfp.batchid = %s
            AND   bfp.feedid  = %s
            ORDER BY bfp.purchase_date DESC
            LIMIT 1
        """, [batchid, feedid])
        row = cur.fetchone()
        c.close()
        if row:
            return {
                'unit_cost_per_kg': int(row[0]),
                'purchase_date':    row[1],
                'bags':             int(row[2]) if row[2] else None,
                'price_per_bag':    int(row[3]) if row[3] else None,
                'total_cost':       int(row[4]) if row[4] else None,
            }
        return None
    except:
        return None

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("# 🐔")
with col2:
    st.markdown("# KUKU Worker Forms")
    st.markdown("*Daily farm data entry system*")

st.divider()

# ============================================================================
# TAB NAVIGATION
# ============================================================================

tabs = st.tabs([
    "⚖️ Weight Check",
    "💰 Daily Sales",
    "🌾 Feed Log",
    "💔 Mortality",
    "💸 Expenses",
    "⚠️ Critical Event",
    "✅ Daily Checklist"
])

# ============================================================================
# TAB 1: WEIGHT CHECK
# CHANGES FROM v2:
#   - Wrapped entire grid in st.form() → zero page reloads while entering weights
#   - value=None on all weight inputs → fields start blank (no annoying zero)
#   - Stats calculated and shown AFTER submit using session_state
# ============================================================================

with tabs[0]:
    st.markdown("""
    <div class="form-header">
        <h2>⚖️ Weight Check Form</h2>
        <p>Record individual bird weights — 10% sample of batch</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    if not batches:
        st.error("❌ No batches found. Please add a batch first.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            batch_options_w = {f"{b[1]} ({b[2]} birds)": b for b in batches}
            selected_batch_label = st.selectbox("Select Batch", list(batch_options_w.keys()), key="w_batch")
            selected_batch = batch_options_w[selected_batch_label]
            batch_id_w = selected_batch[0]
            batch_size_w = selected_batch[2] or 500

        with col2:
            weigh_date = st.date_input("Weighing Date", value=date.today(), key="w_date")

        with col3:
            day_of_cycle = st.selectbox("Day of Cycle", [7, 14, 21], key="w_day",
                                        help="Which weighing day is this?")

        sample_size = max(10, round(batch_size_w * 0.10))

        targets = {7: 200, 14: 550, 21: 1250}
        danger  = {7: 180, 14: 520, 21: 1200}
        elite   = {7: 220, 14: 650, 21: 1400}

        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                    padding:15px; margin:15px 0; display:flex; gap:30px;">
            <div>
                <span style="color:#94A3B8; font-size:12px;">BATCH SIZE</span><br>
                <span style="color:#F1F5F9; font-size:20px; font-weight:700;">{batch_size_w} birds</span>
            </div>
            <div>
                <span style="color:#94A3B8; font-size:12px;">SAMPLE SIZE (10%)</span><br>
                <span style="color:#10B981; font-size:20px; font-weight:700;">{sample_size} birds</span>
            </div>
            <div>
                <span style="color:#94A3B8; font-size:12px;">DAY TARGET</span><br>
                <span style="color:#F59E0B; font-size:20px; font-weight:700;">
                    {targets[day_of_cycle]}g
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### Enter Individual Bird Weights (grams) — {sample_size} birds")
        st.caption("Type each bird's weight in grams. Fields start blank — no need to clear zeros.")

        # ── ALL inputs inside st.form() → no reload until submit ──
        with st.form("weight_form"):
            rows_needed = (sample_size + 9) // 10
            weight_inputs = []

            for row in range(rows_needed):
                cols = st.columns(10)
                for col_idx in range(10):
                    bird_num = row * 10 + col_idx + 1
                    if bird_num <= sample_size:
                        with cols[col_idx]:
                            w = st.number_input(
                                f"#{bird_num}",
                                min_value=0,
                                max_value=5000,
                                value=None,      # ← blank, not 0
                                step=1,
                                key=f"wf_{bird_num}",
                                placeholder="g"
                            )
                            weight_inputs.append((bird_num, w))

            st.markdown("---")
            recorded_by_w = st.text_input("Recorded By (Your name)", placeholder="e.g. Juma", key="w_by")
            notes_w = st.text_area("Notes (optional)", placeholder="Any observations about the birds today...", key="w_notes")

            submitted_w = st.form_submit_button("💾 SAVE WEIGHT SESSION", use_container_width=True)

        # ── Stats and save logic runs AFTER submit, outside the form ──
        if submitted_w:
            valid_weights = [(n, int(w)) for n, w in weight_inputs if w is not None and w > 0]

            if len(valid_weights) < 5:
                st.error("❌ Please enter at least 5 bird weights!")
            elif not recorded_by_w:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    cur.execute("""
                        INSERT INTO public.weight_sessions
                        (batchid, sessiondate, dayofcycle, batchsize, samplesize, recordedby, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING sessionid
                    """, (batch_id_w, weigh_date, day_of_cycle,
                          batch_size_w, sample_size, recorded_by_w, notes_w))

                    session_id = cur.fetchone()[0]

                    for bird_num, weight in valid_weights:
                        cur.execute("""
                            INSERT INTO public.weight_records (sessionid, birdnumber, weightgrams)
                            VALUES (%s, %s, %s)
                        """, (session_id, bird_num, weight))

                    c.commit()
                    c.close()

                    # ── Calculate and display stats AFTER save ──
                    entered_weights = [w for _, w in valid_weights]
                    avg_w   = sum(entered_weights) / len(entered_weights)
                    min_w   = min(entered_weights)
                    max_w   = max(entered_weights)
                    lower   = avg_w * 0.90
                    upper   = avg_w * 1.10
                    uniform_count = sum(1 for w in entered_weights if lower <= w <= upper)
                    uniformity    = (uniform_count / len(entered_weights)) * 100
                    deviation     = ((avg_w - targets[day_of_cycle]) / targets[day_of_cycle]) * 100

                    if avg_w >= elite[day_of_cycle]:
                        status, status_color = "🟢 ELITE", "status-green"
                    elif avg_w >= targets[day_of_cycle]:
                        status, status_color = "🟢 ON TARGET", "status-green"
                    elif avg_w >= danger[day_of_cycle]:
                        status, status_color = "🟡 BELOW TARGET", "status-yellow"
                    else:
                        status, status_color = "🔴 DANGER", "status-red"

                    uni_color = "status-green" if uniformity >= 85 else "status-yellow" if uniformity >= 80 else "status-red"

                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Weight session saved! {len(valid_weights)}/{sample_size} birds weighed
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### 📊 Session Results")
                    c1, c2, c3, c4, c5, c6 = st.columns(6)

                    with c1:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">Birds Weighed</div>
                            <div class="stat-value status-green">{len(valid_weights)}/{sample_size}</div>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">Average Weight</div>
                            <div class="stat-value {status_color}">{avg_w:.0f}g</div>
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">vs Target ({targets[day_of_cycle]}g)</div>
                            <div class="stat-value {status_color}">{deviation:+.1f}%</div>
                        </div>""", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">Min / Max</div>
                            <div class="stat-value" style="font-size:16px; color:#F1F5F9;">
                                {min_w}g / {max_w}g
                            </div>
                        </div>""", unsafe_allow_html=True)
                    with c5:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">Uniformity</div>
                            <div class="stat-value {uni_color}">{uniformity:.0f}%</div>
                        </div>""", unsafe_allow_html=True)
                    with c6:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-label">Status</div>
                            <div class="stat-value {status_color}" style="font-size:14px;">{status}</div>
                        </div>""", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error saving: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Weight Sessions", expanded=False):
        _q = "SELECT ws.sessiondate, b.batchname, ws.dayofcycle, ws.averageweightperbird, ws.samplesize, ws.recordedby FROM public.weight_sessions ws JOIN public.batches_detailed b ON ws.batchid = b.batchid ORDER BY ws.sessiondate DESC, ws.sessionid DESC LIMIT 5"
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            _df.columns = ['Date','Batch','Day of Cycle','Avg Weight (g)','Sample','Recorded By']
            st.table(_df)
        else:
            st.caption("No weight sessions recorded yet")

# TAB 2: DAILY SALES (unchanged from v2)
# ============================================================================

with tabs[1]:
    st.markdown("""
    <div class="form-header">
        <h2>💰 Daily Sales Form</h2>
        <p>Record bird sales transactions</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    # Load buyers OUTSIDE form — dropdown populated from buyers table
    existing_buyers = get_buyers()
    # Pair name with location to avoid confusion between same-named buyers
    def buyer_label(b):
        name, location = b[1], b[2] if len(b) > 2 else None
        return f"{name} — {location}" if location else name

    buyer_labels = [buyer_label(b) for b in existing_buyers]
    # Map label → buyerid for fast lookup
    buyer_map    = {buyer_label(b): b[0] for b in existing_buyers}
    NEW_BUYER    = "➕ Add new customer"
    # "Add new customer" is FIRST in the list
    buyer_choices = [NEW_BUYER] + buyer_labels

    s_buyer_choice = st.selectbox(
        "Customer / Buyer",
        buyer_choices,
        key="s_buyer_select",
        help="Name shown with location to avoid confusion. Select '➕ Add new customer' to register a new buyer."
    )

    s_new_buyer_name = ""
    if s_buyer_choice == NEW_BUYER:
        s_new_buyer_name = st.text_input(
            "New Customer Name",
            placeholder="Type the full name of the new customer",
            key="s_new_buyer"
        )

    # Edit mode banner
    _s_edit_id = st.session_state.get('edit_sale_id')
    if _s_edit_id:
        st.markdown(f"""
        <div style="background:#1c1a07;border:1px solid #f59e0b;border-radius:8px;
                    padding:10px 14px;margin-bottom:8px;">
        ✏️ <strong style="color:#f59e0b;">EDITING RECORD #{_s_edit_id}</strong>
        &nbsp;—&nbsp; <span style="color:#94A3B8;">Make changes below then click Update</span>
        </div>""", unsafe_allow_html=True)
        if st.button("✕ Cancel edit — return to new entry", key="cancel_sale_edit"):
            for _k in ['edit_sale_id','edit_sale_date','edit_sale_batch','edit_sale_buyer',
                       'edit_sale_qty','edit_sale_price','edit_sale_status','edit_sale_notes']:
                st.session_state[_k] = None
            st.rerun()

    with st.form("sales_form"):
        col1, col2 = st.columns(2)

        _s_batch_default = st.session_state.get('edit_sale_batch') or list(batch_options.keys())[0]
        _s_batch_idx     = list(batch_options.keys()).index(_s_batch_default) if _s_batch_default in batch_options else 0

        with col1:
            s_batch = st.selectbox("Batch", list(batch_options.keys()), index=_s_batch_idx)
            s_date  = st.date_input("Sale Date",
                value=st.session_state.get('edit_sale_date') or date.today())

        with col2:
            s_qty   = st.number_input("Birds Sold (Quantity)", min_value=1,
                value=st.session_state.get('edit_sale_qty') or 50)
            s_price = st.number_input("Price per Bird (TZS)", min_value=0,
                value=st.session_state.get('edit_sale_price') or 4000)
            s_total = s_qty * s_price
            st.metric("Total Revenue", f"TZS {s_total:,}")

        _statuses = ["Paid", "Credit - Pending", "Partial Payment"]
        _s_status_default = st.session_state.get('edit_sale_status') or "Paid"
        _s_status_idx = _statuses.index(_s_status_default) if _s_status_default in _statuses else 0
        s_status = st.selectbox("Payment Status", _statuses, index=_s_status_idx)
        s_notes = st.text_area("Notes",
            value=st.session_state.get('edit_sale_notes') or "",
            placeholder="Any details about this sale...")
        s_by    = st.text_input("Recorded By", placeholder="Your name")

        _s_btn_label = f"✏️ UPDATE SALE #{_s_edit_id}" if _s_edit_id else "💾 SAVE SALE"
        if st.form_submit_button(_s_btn_label, use_container_width=True):
            resolved_buyer = s_new_buyer_name.strip() if s_buyer_choice == NEW_BUYER else s_buyer_choice

            if not resolved_buyer:
                st.error("❌ Please select or enter a buyer name!")
            elif not s_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()

                    if s_buyer_choice != NEW_BUYER and s_buyer_choice in buyer_map:
                        buyer_id = buyer_map[s_buyer_choice]
                    else:
                        cur.execute("SELECT buyerid FROM public.buyers WHERE buyername = %s", (resolved_buyer,))
                        result = cur.fetchone()
                        if result:
                            buyer_id = result[0]
                        else:
                            cur.execute(
                                "INSERT INTO public.buyers (buyername) VALUES (%s) RETURNING buyerid",
                                (resolved_buyer,)
                            )
                            buyer_id = cur.fetchone()[0]

                    if _s_edit_id:
                        # UPDATE — recalculates totalrevenue
                        cur.execute("""
                            UPDATE public.daily_sales
                            SET datesold=%s, batchid=%s, quantitysold=%s, buyerid=%s,
                                unitprice=%s, totalrevenue=%s, salestatus=%s, notes=%s
                            WHERE saleid=%s
                        """, (s_date, batch_options[s_batch], s_qty, buyer_id,
                              s_price, s_total, s_status, s_notes, _s_edit_id))
                        msg = f"✅ Sale #{_s_edit_id} updated!<br>{s_qty} birds → {resolved_buyer} @ TZS {s_price:,} = TZS {s_total:,}"
                        for _k in ['edit_sale_id','edit_sale_date','edit_sale_batch','edit_sale_buyer',
                                   'edit_sale_qty','edit_sale_price','edit_sale_status','edit_sale_notes']:
                            st.session_state[_k] = None
                    else:
                        # INSERT new record
                        cur.execute("""
                            INSERT INTO public.daily_sales
                            (batchid, datesold, quantitysold, buyerid, unitprice, totalrevenue, salestatus, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (batch_options[s_batch], s_date, s_qty,
                              buyer_id, s_price, s_total, s_status, s_notes))
                        msg = f"✅ Sale recorded!<br>{s_qty} birds → {resolved_buyer} @ TZS {s_price:,} = TZS {s_total:,}"

                    c.commit()
                    c.close()
                    st.markdown(f'<div class="success-box">{msg}</div>', unsafe_allow_html=True)
                    fetch_recent.clear()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Sales  — click a record to load it for editing", expanded=False):
        _q = """SELECT ds.saleid, ds.datesold, b.batchname, b.batchid,
                       bu.buyername, bu.buyerid, ds.quantitysold, ds.unitprice,
                       ds.totalrevenue, ds.salestatus, ds.notes
                FROM public.daily_sales ds
                JOIN public.batches_detailed b ON ds.batchid = b.batchid
                JOIN public.buyers bu ON ds.buyerid = bu.buyerid
                ORDER BY ds.datesold DESC, ds.saleid DESC LIMIT 5"""
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            for _, row in _df.iterrows():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{row['datesold']}** | {row['batchname']} | "
                        f"{row['buyername']} | {row['quantitysold']} birds | "
                        f"TZS {int(row['unitprice']):,}/bird | {row['salestatus']}",
                        unsafe_allow_html=False
                    )
                with c2:
                    if st.button("📂 Load", key=f"load_sale_{row['saleid']}"):
                        st.session_state.edit_sale_id     = int(row['saleid'])
                        st.session_state.edit_sale_date   = row['datesold']
                        st.session_state.edit_sale_batch  = row['batchname']
                        st.session_state.edit_sale_buyer  = row['buyername']
                        st.session_state.edit_sale_qty    = int(row['quantitysold'])
                        st.session_state.edit_sale_price  = int(row['unitprice'])
                        st.session_state.edit_sale_status = row['salestatus']
                        st.session_state.edit_sale_notes  = row['notes'] or ""
                        st.rerun()
                st.divider()
        else:
            st.caption("No sales recorded yet")

# TAB 3: FEED LOG
# CHANGES FROM v2:
#   - Auto-fetches unit cost from this batch's feed purchase in expenses table
#   - Warns and blocks submission if no feed purchase recorded for batch
#   - Removes hardcoded 1640 cost
# ============================================================================

with tabs[2]:
    st.markdown("""
    <div class="form-header">
        <h2>🌾 Daily Feed Log</h2>
        <p>Record daily feed consumption — cost auto-calculated from batch purchase</p>
    </div>
    """, unsafe_allow_html=True)

    batches      = get_active_batches()
    batch_options_f = {f"{b[1]}": b[0] for b in batches}
    feed_types   = get_feed_types()
    feed_options = {f[1]: f[0] for f in feed_types}

    # Pre-check: fetch cost before showing form
    fl_batch_label = st.selectbox("Batch", list(batch_options_f.keys()), key="fl_batch_select")
    fl_batch_id    = batch_options_f[fl_batch_label]

    # Feed type chosen OUTSIDE form so we can fetch price before showing the form
    f_type = st.selectbox("Feed Type", list(feed_options.keys()), key="fl_feed_type")
    f_feedid = feed_options[f_type]

    feed_cost_info = get_batch_feed_unit_cost(fl_batch_id, f_feedid)

    if not feed_cost_info:
        st.markdown(f"""
        <div class="warn-box">
        ⚠️ <strong>No {f_type} purchase found for {fl_batch_label}</strong><br><br>
        To record daily feed you must first record a feed purchase for this batch and feed type.<br>
        Go to the <strong>💸 Expenses</strong> tab → Category: <strong>Feed Purchase</strong>
        → Feed Type: <strong>{f_type}</strong> → enter bags and price per bag.
        </div>
        """, unsafe_allow_html=True)
    else:
        unit_cost  = feed_cost_info['unit_cost_per_kg']
        bags_info  = f"{feed_cost_info['bags']} bags @ TZS {feed_cost_info['price_per_bag']:,}/bag — " if feed_cost_info['bags'] else ""
        st.markdown(f"""
        <div style="background:#0d2e1f;border:1px solid #10B981;border-radius:8px;padding:12px;margin-bottom:12px;">
            <span style="color:#94A3B8;font-size:12px;">PRICE SOURCE</span><br>
            <span style="color:#10B981;font-weight:600;">{f_type} for {fl_batch_label.split('(')[0].strip()}</span>
            <span style="color:#94A3B8;font-size:13px;"> — {bags_info}TZS {unit_cost:,}/kg (purchased {feed_cost_info['purchase_date']})</span>
        </div>
        """, unsafe_allow_html=True)

        _f_edit_id = st.session_state.get('edit_feed_id')
        if _f_edit_id:
            st.markdown(f"""
            <div style="background:#1c1a07;border:1px solid #f59e0b;border-radius:8px;
                        padding:10px 14px;margin-bottom:8px;">
            ✏️ <strong style="color:#f59e0b;">EDITING FEED LOG #{_f_edit_id}</strong>
            </div>""", unsafe_allow_html=True)
            if st.button("✕ Cancel edit", key="cancel_feed_edit"):
                for _k in ['edit_feed_id','edit_feed_date','edit_feed_batch',
                           'edit_feed_type','edit_feed_qty','edit_feed_notes']:
                    st.session_state[_k] = None
                st.rerun()

        with st.form("feed_form"):
            col1, col2 = st.columns(2)

            with col1:
                f_date = st.date_input("Date",
                    value=st.session_state.get('edit_feed_date') or date.today())

            with col2:
                f_qty  = st.number_input("Quantity (kg)", min_value=0.1,
                    value=st.session_state.get('edit_feed_qty') or 25.0, step=0.5)
                f_by   = st.text_input("Recorded By", placeholder="Your name")

            f_notes = st.text_area("Notes",
                value=st.session_state.get('edit_feed_notes') or "",
                placeholder="Any issues with feed quality, delivery, etc...")

            f_calculated_cost = f_qty * unit_cost
            st.markdown(f"""
            <div style="background:#0d2e1f;border:1px solid #10B981;border-radius:8px;padding:12px;margin-top:8px;">
                <span style="color:#94A3B8;font-size:12px;">AUTO-CALCULATED COST</span><br>
                <span style="color:#10B981;font-size:20px;font-weight:700;">
                    {f_qty:.1f}kg × TZS {unit_cost:,} = TZS {f_calculated_cost:,.0f}
                </span>
            </div>
            """, unsafe_allow_html=True)

            _f_btn = f"✏️ UPDATE FEED LOG #{_f_edit_id}" if _f_edit_id else "💾 SAVE FEED LOG"
            if st.form_submit_button(_f_btn, use_container_width=True):
                if not f_by:
                    st.error("❌ Please enter your name!")
                else:
                    try:
                        c   = fresh_conn()
                        cur = c.cursor()
                        if _f_edit_id:
                            cur.execute("""
                                UPDATE public.daily_feed_log
                                SET datefed=%s, feedtypeid=%s, quantitykg=%s, feedcost=%s, notes=%s
                                WHERE feedlogid=%s
                            """, (f_date, f_feedid, f_qty, int(f_calculated_cost), f_notes, _f_edit_id))
                            msg = f"✅ Feed log #{_f_edit_id} updated!<br>{f_qty}kg {f_type} → TZS {f_calculated_cost:,.0f}"
                            for _k in ['edit_feed_id','edit_feed_date','edit_feed_batch',
                                       'edit_feed_type','edit_feed_qty','edit_feed_notes']:
                                st.session_state[_k] = None
                        else:
                            cur.execute("""
                                INSERT INTO public.daily_feed_log
                                (batchid, datefed, feedtypeid, quantitykg, feedcost, notes)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (fl_batch_id, f_date, f_feedid, f_qty, int(f_calculated_cost), f_notes))
                            msg = f"✅ Feed log saved!<br>{f_qty}kg {f_type} → TZS {f_calculated_cost:,.0f}"
                        c.commit()
                        c.close()
                        st.markdown(f'<div class="success-box">{msg}</div>', unsafe_allow_html=True)
                        fetch_recent.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Feed Log Entries — click a record to load for editing", expanded=False):
        _q = """SELECT fl.feedlogid, fl.datefed, b.batchname, b.batchid,
                       f.feedtype, f.feedid, fl.quantitykg, fl.feedcost, fl.notes
                FROM public.daily_feed_log fl
                JOIN public.batches_detailed b ON fl.batchid = b.batchid
                JOIN public.feeds f ON fl.feedtypeid = f.feedid
                ORDER BY fl.datefed DESC, fl.feedlogid DESC LIMIT 5"""
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            for _, row in _df.iterrows():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{row['datefed']}** | {row['batchname']} | "
                        f"{row['feedtype']} | {float(row['quantitykg']):.1f}kg | "
                        f"TZS {int(row['feedcost']):,}" if row['feedcost'] else
                        f"**{row['datefed']}** | {row['batchname']} | {row['feedtype']} | {float(row['quantitykg']):.1f}kg"
                    )
                with c2:
                    if st.button("📂 Load", key=f"load_feed_{row['feedlogid']}"):
                        st.session_state.edit_feed_id    = int(row['feedlogid'])
                        st.session_state.edit_feed_date  = row['datefed']
                        st.session_state.edit_feed_batch = row['batchname']
                        st.session_state.edit_feed_type  = row['feedtype']
                        st.session_state.edit_feed_qty   = float(row['quantitykg'])
                        st.session_state.edit_feed_notes = row['notes'] or ""
                        st.rerun()
                st.divider()
        else:
            st.caption("No feed log entries yet")

# TAB 4: MORTALITY (unchanged from v2)
# ============================================================================

with tabs[3]:
    st.markdown("""
    <div class="form-header">
        <h2>💔 Mortality Report</h2>
        <p>Record bird deaths</p>
    </div>
    """, unsafe_allow_html=True)

    batches      = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    _m_edit_id = st.session_state.get('edit_mort_id')
    if _m_edit_id:
        st.markdown(f"""
        <div style="background:#1c1a07;border:1px solid #f59e0b;border-radius:8px;
                    padding:10px 14px;margin-bottom:8px;">
        ✏️ <strong style="color:#f59e0b;">EDITING MORTALITY RECORD #{_m_edit_id}</strong>
        </div>""", unsafe_allow_html=True)
        if st.button("✕ Cancel edit", key="cancel_mort_edit"):
            for _k in ['edit_mort_id','edit_mort_date','edit_mort_batch',
                       'edit_mort_qty','edit_mort_reason','edit_mort_notes']:
                st.session_state[_k] = None
            st.rerun()

    _reasons = ["Disease", "Accident", "Starvation", "Dehydration", "Unknown", "Other"]
    _m_batch_default = st.session_state.get('edit_mort_batch') or list(batch_options.keys())[0]
    _m_batch_idx     = list(batch_options.keys()).index(_m_batch_default) if _m_batch_default in batch_options else 0
    _m_reason_default = st.session_state.get('edit_mort_reason') or "Unknown"
    _m_reason_idx     = _reasons.index(_m_reason_default) if _m_reason_default in _reasons else 4

    with st.form("mortality_form"):
        col1, col2 = st.columns(2)

        with col1:
            m_batch = st.selectbox("Batch", list(batch_options.keys()), index=_m_batch_idx)
            m_date  = st.date_input("Date",
                value=st.session_state.get('edit_mort_date') or date.today())
            m_qty   = st.number_input("Number of Deaths", min_value=1,
                value=st.session_state.get('edit_mort_qty') or 1)

        with col2:
            m_reason = st.selectbox("Reason", _reasons, index=_m_reason_idx)
            m_by     = st.text_input("Recorded By", placeholder="Your name")

        m_notes = st.text_area("Notes",
            value=st.session_state.get('edit_mort_notes') or "",
            placeholder="Describe symptoms, location of deaths, any pattern...")

        _m_btn = f"✏️ UPDATE RECORD #{_m_edit_id}" if _m_edit_id else "💾 SAVE MORTALITY REPORT"
        if st.form_submit_button(_m_btn, use_container_width=True):
            if not m_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()
                    if _m_edit_id:
                        cur.execute("""
                            UPDATE public.daily_mortality
                            SET daterecorded=%s, batchid=%s, quantitydied=%s, reason=%s, notes=%s
                            WHERE mortalityid=%s
                        """, (m_date, batch_options[m_batch], m_qty, m_reason, m_notes, _m_edit_id))
                        msg = f"✅ Record #{_m_edit_id} updated!<br>{m_qty} birds | {m_reason}"
                        for _k in ['edit_mort_id','edit_mort_date','edit_mort_batch',
                                   'edit_mort_qty','edit_mort_reason','edit_mort_notes']:
                            st.session_state[_k] = None
                    else:
                        cur.execute("""
                            INSERT INTO public.daily_mortality
                            (batchid, daterecorded, quantitydied, reason, notes)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (batch_options[m_batch], m_date, m_qty, m_reason, m_notes))
                        msg = f"✅ Mortality recorded!<br>{m_qty} birds | Reason: {m_reason}"
                    c.commit()
                    c.close()
                    st.markdown(f'<div class="success-box">{msg}</div>', unsafe_allow_html=True)
                    fetch_recent.clear()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Mortality Records — click a record to load for editing", expanded=False):
        _q = """SELECT dm.mortalityid, dm.daterecorded, b.batchname, b.batchid,
                       dm.quantitydied, dm.reason, dm.notes
                FROM public.daily_mortality dm
                JOIN public.batches_detailed b ON dm.batchid = b.batchid
                ORDER BY dm.daterecorded DESC, dm.mortalityid DESC LIMIT 5"""
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            for _, row in _df.iterrows():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{row['daterecorded']}** | {row['batchname']} | "
                        f"{row['quantitydied']} birds | {row['reason'] or 'Unknown'}"
                    )
                with c2:
                    if st.button("📂 Load", key=f"load_mort_{row['mortalityid']}"):
                        st.session_state.edit_mort_id     = int(row['mortalityid'])
                        st.session_state.edit_mort_date   = row['daterecorded']
                        st.session_state.edit_mort_batch  = row['batchname']
                        st.session_state.edit_mort_qty    = int(row['quantitydied'])
                        st.session_state.edit_mort_reason = row['reason'] or "Unknown"
                        st.session_state.edit_mort_notes  = row['notes'] or ""
                        st.rerun()
                st.divider()
        else:
            st.caption("No mortality records yet")

# TAB 5: EXPENSES
# CHANGES FROM v2:
#   - Added optional Quantity + Unit + Unit Price fields (work for ALL categories)
#   - Amount auto-calculates from Quantity × Unit Price if both are filled
#   - If not filled, user enters Amount manually (minority case)
#   - Feed Purchase category shows 50kg bag note for context
# ============================================================================

with tabs[4]:
    st.markdown("""
    <div class="form-header">
        <h2>💸 Expense Entry</h2>
        <p>Record farm expenses — for Feed Purchase, select feed type to auto-save price per kg</p>
    </div>
    """, unsafe_allow_html=True)

    batches          = get_active_batches()
    batch_options_ex = {"No specific batch": None}
    batch_options_ex.update({f"{b[1]}": b[0] for b in batches})
    categories       = get_expense_categories()
    feed_types_ex    = get_feed_types()
    feed_options_ex  = {f[1]: f[0] for f in feed_types_ex}

    # Category + feed type selectors OUTSIDE form so feed type reacts to category change
    e_category_pre = st.selectbox(
        "Category",
        categories,
        key="e_cat_pre"
    )

    e_feedtype_id   = None
    e_feedtype_name = None
    if e_category_pre == "Feed Purchase":
        e_feedtype_name = st.selectbox(
            "Feed Type",
            list(feed_options_ex.keys()),
            key="e_feedtype_pre",
            help="Which feed type was purchased? Price per kg will be saved to batch_feed_prices."
        )
        e_feedtype_id = feed_options_ex[e_feedtype_name]

    _e_edit_id_pre = st.session_state.get('edit_exp_id')
    if _e_edit_id_pre:
        st.markdown(f"""
        <div style="background:#1c1a07;border:1px solid #f59e0b;border-radius:8px;
                    padding:10px 14px;margin-bottom:8px;">
        ✏️ <strong style="color:#f59e0b;">EDITING EXPENSE #{_e_edit_id_pre}</strong>
        &nbsp;—&nbsp;<span style="color:#94A3B8;">Make changes and click Update</span>
        </div>""", unsafe_allow_html=True)
        if st.button("✕ Cancel edit", key="cancel_exp_edit"):
            for _k in ['edit_exp_id','edit_exp_date','edit_exp_batch','edit_exp_cat',
                       'edit_exp_desc','edit_exp_qty','edit_exp_uprice','edit_exp_notes']:
                st.session_state[_k] = None
            st.rerun()

    with st.form("expense_form"):
        col1, col2 = st.columns(2)

        _e_batch_default = st.session_state.get('edit_exp_batch') or "No specific batch"
        _e_batch_idx     = list(batch_options_ex.keys()).index(_e_batch_default) if _e_batch_default in batch_options_ex else 0

        with col1:
            e_date  = st.date_input("Expense Date",
                value=st.session_state.get('edit_exp_date') or date.today())
            e_batch = st.selectbox(
                "Related Batch" + (" (Required for Feed Purchase)" if e_category_pre == "Feed Purchase" else " (Optional)"),
                list(batch_options_ex.keys()), index=_e_batch_idx
            )

        with col2:
            e_vendor = st.text_input("Vendor / Supplier", placeholder="Who received the money?")
            e_by     = st.text_input("Recorded By", placeholder="Your name")

        desc_hint = f"e.g. 10 bags {e_feedtype_name}" if e_category_pre == "Feed Purchase" and e_feedtype_name else "e.g. Vaccines 3 packages, Labor 5 days"
        e_desc = st.text_input("Description",
            value=st.session_state.get('edit_exp_desc') or "",
            placeholder=desc_hint)

        st.markdown("---")
        st.markdown("**Quantity & Pricing** *(optional — fill for auto-calculation)*")

        col1, col2, col3 = st.columns(3)

        with col1:
            e_qty = st.number_input(
                "Quantity",
                min_value=0.0, value=None, step=1.0,
                placeholder="e.g. 10"
            )
        with col2:
            unit_hint = "bags (50kg each)" if e_category_pre == "Feed Purchase" else "bags, pcs, days..."
            e_unit = st.text_input("Unit", placeholder=unit_hint)
        with col3:
            e_unit_price = st.number_input(
                "Unit Price (TZS)",
                min_value=0.0, value=None, step=100.0,
                placeholder="e.g. 16600"
            )

        # Auto-calculate amount
        if e_qty and e_qty > 0 and e_unit_price and e_unit_price > 0:
            auto_amount = int(e_qty * e_unit_price)
            extra_info  = ""
            if e_category_pre == "Feed Purchase":
                kg_total     = int(e_qty * 50)
                cost_per_kg  = int(e_unit_price / 50)
                extra_info   = f"<br><span style='color:#94A3B8;font-size:11px;'>{int(e_qty)} bags × 50kg = {kg_total}kg &nbsp;|&nbsp; TZS {cost_per_kg:,}/kg saved to {e_feedtype_name} price</span>"
            st.markdown(f"""
            <div style="background:#0d2e1f;border:1px solid #10B981;border-radius:8px;padding:12px;margin:8px 0;">
                <span style="color:#94A3B8;font-size:12px;">AUTO-CALCULATED AMOUNT</span><br>
                <span style="color:#10B981;font-size:20px;font-weight:700;">
                    {e_qty:.0f} × TZS {e_unit_price:,.0f} = TZS {auto_amount:,}
                </span>{extra_info}
            </div>
            """, unsafe_allow_html=True)
            e_amount_final = auto_amount
            st.number_input("Amount (TZS)", value=auto_amount, disabled=True)
        else:
            e_amount_final = None
            e_amount_manual = st.number_input("Amount (TZS)", min_value=0, value=0, step=500)
            if e_amount_manual > 0:
                e_amount_final = e_amount_manual

        e_notes = st.text_area("Notes", placeholder="Any additional details...")

        _e_edit_id  = st.session_state.get('edit_exp_id')
        _e_btn      = f"✏️ UPDATE EXPENSE #{_e_edit_id}" if _e_edit_id else "💾 SAVE EXPENSE"
        if st.form_submit_button(_e_btn, use_container_width=True):
            batch_id_ex = batch_options_ex[e_batch]
            if not e_desc:
                st.error("❌ Please enter a description!")
            elif not e_amount_final or e_amount_final <= 0:
                st.error("❌ Please enter a valid amount!")
            elif not e_by:
                st.error("❌ Please enter your name!")
            elif e_category_pre == "Feed Purchase" and batch_id_ex is None:
                st.error("❌ Feed Purchase must be linked to a batch!")
            elif e_category_pre == "Feed Purchase" and not e_feedtype_id:
                st.error("❌ Please select a feed type!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()

                    if _e_edit_id:
                        # UPDATE existing expense
                        cur.execute("""
                            UPDATE public.expenses
                            SET expensedate=%s, category=%s, description=%s, amount=%s,
                                quantity=%s, unit_price=%s, batchid=%s, notes=%s
                            WHERE expense_id=%s
                        """, (
                            e_date, e_category_pre, e_desc, e_amount_final,
                            float(e_qty) if e_qty else None,
                            float(e_unit_price) if e_unit_price else None,
                            batch_id_ex, e_notes, _e_edit_id
                        ))
                        # Feed Purchase: update batch_feed_prices too
                        if e_category_pre == "Feed Purchase" and e_feedtype_id and e_qty and e_unit_price:
                            unit_cost_kg = round(float(e_unit_price) / 50, 2)
                            cur.execute("""
                                UPDATE public.batch_feed_prices
                                SET unit_cost_per_kg=%s, purchase_date=%s, feedid=%s
                                WHERE expense_id=%s
                            """, (unit_cost_kg, e_date, e_feedtype_id, _e_edit_id))
                        msg = f"✅ Expense #{_e_edit_id} updated!<br>{e_category_pre}: {e_desc} → TZS {e_amount_final:,}"
                        for _k in ['edit_exp_id','edit_exp_date','edit_exp_batch','edit_exp_cat',
                                   'edit_exp_desc','edit_exp_qty','edit_exp_uprice','edit_exp_notes']:
                            st.session_state[_k] = None
                    else:
                        # INSERT new expense
                        cur.execute("""
                            INSERT INTO public.expenses
                            (expensedate, category, description, amount,
                             quantity, unit_price, receivedfrom, batchid, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING expense_id
                        """, (
                            e_date, e_category_pre, e_desc, e_amount_final,
                            float(e_qty) if e_qty else None,
                            float(e_unit_price) if e_unit_price else None,
                            e_vendor, batch_id_ex, e_notes
                        ))
                        new_expense_id = cur.fetchone()[0]
                        if e_category_pre == "Feed Purchase" and e_feedtype_id and e_qty and e_unit_price:
                            unit_cost_kg = round(float(e_unit_price) / 50, 2)
                            cur.execute("""
                                INSERT INTO public.batch_feed_prices
                                (batchid, feedid, unit_cost_per_kg, purchase_date, expense_id)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (batch_id_ex, e_feedtype_id, unit_cost_kg, e_date, new_expense_id))
                        extra = f"<br>📊 {e_feedtype_name} price saved: TZS {int(e_unit_price/50):,}/kg" if e_category_pre == "Feed Purchase" and e_qty and e_unit_price else ""
                        msg = f"✅ Expense saved!<br>{e_category_pre}: {e_desc} → TZS {e_amount_final:,}{extra}"

                    c.commit()
                    c.close()
                    st.markdown(f'<div class="success-box">{msg}</div>', unsafe_allow_html=True)
                    fetch_recent.clear()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Expenses — click a record to load for editing", expanded=False):
        _q = """SELECT e.expense_id, e.expensedate, e.category, e.description,
                       e.quantity, e.unit_price, e.amount, b.batchname, e.batchid, e.notes
                FROM public.expenses e
                LEFT JOIN public.batches_detailed b ON e.batchid = b.batchid
                ORDER BY e.expensedate DESC, e.expense_id DESC LIMIT 5"""
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            for _, row in _df.iterrows():
                c1, c2 = st.columns([4, 1])
                with c1:
                    amt_str = f"TZS {int(row['amount']):,}"
                    batch_str = row['batchname'] or 'No batch'
                    st.markdown(
                        f"**{row['expensedate']}** | {row['category']} | "
                        f"{row['description']} | {amt_str} | {batch_str}"
                    )
                with c2:
                    if st.button("📂 Load", key=f"load_exp_{row['expense_id']}"):
                        st.session_state.edit_exp_id     = int(row['expense_id'])
                        st.session_state.edit_exp_date   = row['expensedate']
                        st.session_state.edit_exp_batch  = row['batchname'] or "No specific batch"
                        st.session_state.edit_exp_cat    = row['category']
                        st.session_state.edit_exp_desc   = row['description'] or ""
                        st.session_state.edit_exp_qty    = float(row['quantity']) if row['quantity'] else None
                        st.session_state.edit_exp_uprice = float(row['unit_price']) if row['unit_price'] else None
                        st.session_state.edit_exp_notes  = row['notes'] or ""
                        st.rerun()
                st.divider()
        else:
            st.caption("No expenses yet")

# TAB 6: CRITICAL EVENT (unchanged from v2)
# ============================================================================

with tabs[5]:
    st.markdown("""
    <div class="form-header">
        <h2>⚠️ Critical Event Log</h2>
        <p>Record any problems or important events that happened today</p>
    </div>
    """, unsafe_allow_html=True)

    batches      = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    with st.form("event_form"):
        col1, col2 = st.columns(2)

        with col1:
            ev_batch = st.selectbox("Batch", list(batch_options.keys()))
            ev_date  = st.date_input("Event Date", value=date.today())
            ev_day   = st.number_input("Day of Cycle", min_value=1, max_value=21, value=1)

        with col2:
            ev_type = st.selectbox("Event Type", [
                "Light Failure", "Feed Shortage", "Water Supply Issue",
                "Mortality Spike", "Disease Outbreak", "Equipment Failure",
                "Power Outage", "Temperature Problem", "Feed Quality Issue", "Other"
            ])
            ev_severity = st.selectbox("Severity", [
                "⚪ Low", "🟡 Medium", "🟠 High", "🔴 Critical"
            ])

        ev_desc   = st.text_area("What Happened?",
            placeholder="Describe exactly what happened in detail...")
        ev_action = st.text_area("Action Taken",
            placeholder="What did you do about it?")
        ev_by     = st.text_input("Recorded By", placeholder="Your name")

        if st.form_submit_button("💾 SAVE EVENT LOG", use_container_width=True):
            if not ev_desc:
                st.error("❌ Please describe what happened!")
            elif not ev_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()
                    cur.execute("""
                        INSERT INTO public.critical_events
                        (batchid, eventdate, dayofcycle, eventtype,
                         severity, description, actiontaken, recordedby)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (batch_options[ev_batch], ev_date, ev_day,
                          ev_type, ev_severity, ev_desc, ev_action, ev_by))
                    c.commit()
                    c.close()

                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Event logged!<br>
                        {ev_type} | Severity: {ev_severity}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Critical Events", expanded=False):
        _q = "SELECT ce.eventdate, b.batchname, ce.eventtype, ce.severity, LEFT(ce.description, 60) FROM public.critical_events ce LEFT JOIN public.batches_detailed b ON ce.batchid = b.batchid ORDER BY ce.eventdate DESC, ce.eventid DESC LIMIT 5"
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            _df.columns = ['Date','Batch','Type','Severity','Description']
            st.table(_df)
        else:
            st.caption("No critical events yet")

# TAB 7: DAILY CHECKLIST (unchanged from v2)
# ============================================================================

with tabs[6]:
    st.markdown("""
    <div class="form-header">
        <h2>✅ Daily Checklist</h2>
        <p>End of shift checklist — confirm all tasks completed</p>
    </div>
    """, unsafe_allow_html=True)

    batches      = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    with st.form("checklist_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            cl_batch = st.selectbox("Batch", list(batch_options.keys()))
            cl_date  = st.date_input("Date", value=date.today())

        with col2:
            cl_shift = st.selectbox("Shift", ["Morning", "Afternoon", "Evening"])
            cl_by    = st.text_input("Your Name", placeholder="Worker name")

        st.markdown("---")
        st.markdown("### ✅ Task Completion")

        col1, col2 = st.columns(2)

        with col1:
            cl_feed       = st.checkbox("🌾 Feed Refilled")
            cl_feed_times = st.number_input("How many times refilled?",
                min_value=0, max_value=10, value=0, disabled=not cl_feed)
            cl_water  = st.checkbox("💧 Water Supply Checked & Refilled")
            cl_lights = st.checkbox("💡 Lights Checked (all working)")

        with col2:
            cl_temp     = st.checkbox("🌡️ Temperature Checked")
            cl_temp_val = st.number_input("Temperature Reading (°C)",
                min_value=0.0, max_value=50.0, value=28.0, step=0.5,
                disabled=not cl_temp)
            cl_vent     = st.checkbox("💨 Ventilation Checked")
            cl_mortality= st.checkbox("💔 Checked for Dead Birds")

        st.markdown("---")
        cl_notes = st.text_area("Any Issues or Observations?",
            placeholder="Report anything unusual — smells, sounds, sick birds, equipment issues...")

        if st.form_submit_button("💾 SUBMIT CHECKLIST", use_container_width=True):
            if not cl_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()
                    cur.execute("""
                        INSERT INTO public.daily_checklist
                        (BatchID, CheckDate, Shift, FeedRefilled,
                         FeedRefilledTimes, WaterChecked, LightsChecked,
                         TemperatureChecked, TemperatureReading,
                         VentilationChecked, RecordedBy, Notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        batch_options[cl_batch], cl_date, cl_shift,
                        cl_feed, cl_feed_times if cl_feed else 0,
                        cl_water, cl_lights, cl_temp,
                        cl_temp_val if cl_temp else None,
                        cl_vent, cl_by, cl_notes
                    ))
                    c.commit()
                    c.close()

                    tasks_done = sum([cl_feed, cl_water, cl_lights,
                                      cl_temp, cl_vent, cl_mortality])
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Checklist submitted!<br>
                        {tasks_done}/6 tasks completed | {cl_shift} shift | {cl_by}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================

    # ── Recent entries ──
    with st.expander("📋 Last 5 Checklists", expanded=False):
        _q = "SELECT cl.CheckDate, b.batchname, cl.Shift, cl.FeedRefilled, cl.WaterChecked, cl.LightsChecked, cl.TemperatureReading, cl.RecordedBy FROM public.daily_checklist cl JOIN public.batches_detailed b ON cl.BatchID = b.batchid ORDER BY cl.CheckDate DESC, cl.ChecklistID DESC LIMIT 5"
        _df = fetch_recent(_q)
        if _df is not None and not _df.empty:
            _df.columns = ['Date','Batch','Shift','Fed','Water','Lights','Temp °C','By']
            _df['Fed']    = _df['Fed'].apply(lambda x: "Yes" if x else "No")
            _df['Water']  = _df['Water'].apply(lambda x: "Yes" if x else "No")
            _df['Lights'] = _df['Lights'].apply(lambda x: "Yes" if x else "No")
            st.table(_df)
        else:
            st.caption("No checklists yet")

# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#94A3B8; font-size:12px;">
    🐔 KUKU Farm Worker Forms v3.0 | Report problems to farm owner
</p>
""", unsafe_allow_html=True)
