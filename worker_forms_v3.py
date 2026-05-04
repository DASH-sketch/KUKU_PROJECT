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

def get_batch_feed_unit_cost(batchid):
    """
    Fetch most recent feed purchase for this batch from expenses table.
    Uses: category='Feed Purchase', quantity=bags, unit_price=per bag, amount=total
    Returns dict with unit_cost_per_kg and purchase info, or None.
    """
    try:
        c = fresh_conn()
        cur = c.cursor()
        cur.execute("""
            SELECT
                ROUND((amount::numeric / (quantity * 50))::numeric, 0) as unit_cost_per_kg,
                expensedate,
                quantity as bags,
                ROUND(unit_price::numeric) as price_per_bag,
                ROUND(amount::numeric) as total_cost
            FROM public.expenses
            WHERE batchid = %s
            AND category = 'Feed Purchase'
            AND quantity IS NOT NULL
            AND quantity > 0
            ORDER BY expensedate DESC
            LIMIT 1
        """, [batchid])
        row = cur.fetchone()
        c.close()
        if row:
            return {
                'unit_cost_per_kg': int(row[0]),
                'purchase_date': row[1],
                'bags': int(row[2]),
                'price_per_bag': int(row[3]),
                'total_cost': int(row[4])
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

    with st.form("sales_form"):
        col1, col2 = st.columns(2)

        with col1:
            s_batch = st.selectbox("Batch", list(batch_options.keys()))
            s_date  = st.date_input("Sale Date", value=date.today())

        with col2:
            s_qty   = st.number_input("Birds Sold (Quantity)", min_value=1, value=50)
            s_price = st.number_input("Price per Bird (TZS)", min_value=0, value=4000)
            s_total = s_qty * s_price
            st.metric("Total Revenue", f"TZS {s_total:,}")

        s_status = st.selectbox("Payment Status",
            ["Paid", "Credit - Pending", "Partial Payment"])
        s_notes = st.text_area("Notes", placeholder="Any details about this sale...")
        s_by    = st.text_input("Recorded By", placeholder="Your name")

        if st.form_submit_button("💾 SAVE SALE", use_container_width=True):
            # Resolve final buyer name
            resolved_buyer = s_new_buyer_name.strip() if s_buyer_choice == NEW_BUYER else s_buyer_choice

            if not resolved_buyer:
                st.error("❌ Please select or enter a buyer name!")
            elif not s_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()

                    # Use known buyer_id if existing buyer selected (via label)
                    if s_buyer_choice != NEW_BUYER and s_buyer_choice in buyer_map:
                        buyer_id = buyer_map[s_buyer_choice]
                    else:
                        # New buyer — check if name already exists, else create
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

                    cur.execute("""
                        INSERT INTO public.daily_sales
                        (batchid, datesold, quantitysold, buyerid, unitprice, totalrevenue, salestatus, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (batch_options[s_batch], s_date, s_qty,
                          buyer_id, s_price, s_total, s_status, s_notes))
                    c.commit()
                    c.close()

                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Sale recorded!<br>
                        {s_qty} birds → {resolved_buyer} @ TZS {s_price:,} = TZS {s_total:,}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
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
    feed_cost_info = get_batch_feed_unit_cost(fl_batch_id)

    if not feed_cost_info:
        st.markdown(f"""
        <div class="warn-box">
        ⚠️ <strong>No feed purchase found for {fl_batch_label}</strong><br><br>
        To record daily feed, you must first record a feed purchase for this batch.<br>
        Go to the <strong>💸 Expenses</strong> tab → select category <strong>Feed Purchase</strong>
        → enter bags and unit price for this batch.
        </div>
        """, unsafe_allow_html=True)
    else:
        unit_cost = feed_cost_info['unit_cost_per_kg']
        st.info(f"📦 Using {fl_batch_label}'s feed purchase: **TZS {unit_cost:,}/kg** "
                f"({feed_cost_info['bags']} bags @ TZS {feed_cost_info['price_per_bag']:,}/bag "
                f"— purchased {feed_cost_info['purchase_date']})")

        with st.form("feed_form"):
            col1, col2 = st.columns(2)

            with col1:
                f_date = st.date_input("Date", value=date.today())
                f_type = st.selectbox("Feed Type", list(feed_options.keys()))

            with col2:
                f_qty  = st.number_input("Quantity (kg)", min_value=0.1, value=25.0, step=0.5)
                f_by   = st.text_input("Recorded By", placeholder="Your name")

            f_notes = st.text_area("Notes", placeholder="Any issues with feed quality, delivery, etc...")

            # Show calculated cost preview inside form
            f_calculated_cost = f_qty * unit_cost
            st.markdown(f"""
            <div style="background:#0d2e1f; border:1px solid #10B981; border-radius:8px; padding:12px; margin-top:8px;">
                <span style="color:#94A3B8; font-size:12px;">AUTO-CALCULATED COST</span><br>
                <span style="color:#10B981; font-size:20px; font-weight:700;">
                    {f_qty:.1f}kg × TZS {unit_cost:,} = TZS {f_calculated_cost:,.0f}
                </span>
            </div>
            """, unsafe_allow_html=True)

            if st.form_submit_button("💾 SAVE FEED LOG", use_container_width=True):
                if not f_by:
                    st.error("❌ Please enter your name!")
                else:
                    try:
                        c   = fresh_conn()
                        cur = c.cursor()
                        cur.execute("""
                            INSERT INTO public.daily_feed_log
                            (batchid, datefed, feedtypeid, quantitykg, feedcost, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (fl_batch_id, f_date,
                              feed_options[f_type],
                              f_qty,
                              int(f_calculated_cost),
                              f_notes))
                        c.commit()
                        c.close()

                        st.markdown(f"""
                        <div class="success-box">
                            ✅ Feed log saved!<br>
                            {f_qty}kg {f_type} → TZS {f_calculated_cost:,.0f}
                        </div>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============================================================================
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

    with st.form("mortality_form"):
        col1, col2 = st.columns(2)

        with col1:
            m_batch = st.selectbox("Batch", list(batch_options.keys()))
            m_date  = st.date_input("Date", value=date.today())
            m_qty   = st.number_input("Number of Deaths", min_value=1, value=1)

        with col2:
            m_reason = st.selectbox("Reason", [
                "Disease", "Accident", "Starvation",
                "Dehydration", "Unknown", "Other"
            ])
            m_by = st.text_input("Recorded By", placeholder="Your name")

        m_notes = st.text_area("Notes",
            placeholder="Describe symptoms, location of deaths, any pattern...")

        if st.form_submit_button("💾 SAVE MORTALITY REPORT", use_container_width=True):
            if not m_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()
                    cur.execute("""
                        INSERT INTO public.daily_mortality
                        (batchid, daterecorded, quantitydied, reason, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (batch_options[m_batch], m_date, m_qty, m_reason, m_notes))
                    c.commit()
                    c.close()

                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Mortality recorded!<br>
                        {m_qty} birds | Reason: {m_reason}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
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
        <p>Record farm expenses — enter quantity & unit price when available for auto-calculation</p>
    </div>
    """, unsafe_allow_html=True)

    batches          = get_active_batches()
    batch_options_ex = {"No specific batch": None}
    batch_options_ex.update({f"{b[1]}": b[0] for b in batches})
    categories = get_expense_categories()

    with st.form("expense_form"):
        col1, col2 = st.columns(2)

        with col1:
            e_date     = st.date_input("Expense Date", value=date.today())
            e_category = st.selectbox("Category", categories)
            e_batch    = st.selectbox("Related Batch (Optional)", list(batch_options_ex.keys()))

        with col2:
            e_vendor = st.text_input("Vendor / Supplier",
                                     placeholder="Who received the money?")
            e_by     = st.text_input("Recorded By", placeholder="Your name")

        e_desc = st.text_input("Description",
            placeholder="e.g. Starter feed 10 bags, Vaccines 3 packages, Labor 5 days")

        st.markdown("---")
        st.markdown("**Quantity & Pricing** *(optional — fill for auto-calculation)*")

        col1, col2, col3 = st.columns(3)

        with col1:
            e_qty = st.number_input(
                "Quantity",
                min_value=0.0, value=None, step=1.0,
                placeholder="e.g. 10",
                help="Number of bags, packages, pieces, days, etc."
            )

        with col2:
            # Show unit hint for Feed Purchase
            unit_hint = "bags" if e_category == "Feed Purchase" else "e.g. bags, pcs, pkgs, days"
            e_unit = st.text_input(
                "Unit",
                placeholder=unit_hint,
                help="What is the unit? bags, pieces, packages, days, etc."
            )

        with col3:
            e_unit_price = st.number_input(
                "Unit Price (TZS)",
                min_value=0.0, value=None, step=100.0,
                placeholder="e.g. 16600",
                help="Price per single unit"
            )

        # Auto-calculate or manual amount
        if e_qty and e_qty > 0 and e_unit_price and e_unit_price > 0:
            auto_amount = int(e_qty * e_unit_price)
            st.markdown(f"""
            <div style="background:#0d2e1f; border:1px solid #10B981; border-radius:8px;
                        padding:12px; margin:8px 0;">
                <span style="color:#94A3B8; font-size:12px;">AUTO-CALCULATED AMOUNT</span><br>
                <span style="color:#10B981; font-size:20px; font-weight:700;">
                    {e_qty:.0f} {e_unit} × TZS {e_unit_price:,.0f} = TZS {auto_amount:,}
                </span>
                {"<br><span style='color:#94A3B8; font-size:11px;'>Feed Purchase: " + str(int(e_qty)) + " bags × 50kg = " + str(int(e_qty * 50)) + "kg total</span>" if e_category == "Feed Purchase" else ""}
            </div>
            """, unsafe_allow_html=True)
            e_amount_final = auto_amount
            # Hidden placeholder — amount is auto-calculated
            st.number_input("Amount (TZS)", value=auto_amount, disabled=True,
                           help="Auto-calculated from Quantity × Unit Price")
        else:
            e_amount_final = None
            e_amount_manual = st.number_input(
                "Amount (TZS)",
                min_value=0, value=0, step=500,
                help="Enter total amount (or fill Quantity + Unit Price above for auto-calculation)"
            )
            if e_amount_manual > 0:
                e_amount_final = e_amount_manual

        e_notes = st.text_area("Notes", placeholder="Any additional details...")

        if st.form_submit_button("💾 SAVE EXPENSE", use_container_width=True):
            if not e_desc:
                st.error("❌ Please enter a description!")
            elif not e_amount_final or e_amount_final <= 0:
                st.error("❌ Please enter a valid amount (or fill Quantity × Unit Price)!")
            elif not e_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c   = fresh_conn()
                    cur = c.cursor()

                    batch_id_ex = batch_options_ex[e_batch]

                    cur.execute("""
                        INSERT INTO public.expenses
                        (expensedate, category, description, amount,
                         quantity, unit_price,
                         receivedfrom, batchid, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        e_date, e_category, e_desc,
                        e_amount_final,
                        float(e_qty) if e_qty else None,
                        float(e_unit_price) if e_unit_price else None,
                        e_vendor, batch_id_ex, e_notes
                    ))
                    c.commit()
                    c.close()

                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Expense saved!<br>
                        {e_category}: {e_desc} → TZS {e_amount_final:,}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
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
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<p style="text-align:center; color:#94A3B8; font-size:12px;">
    🐔 KUKU Farm Worker Forms v3.0 | Report problems to farm owner
</p>
""", unsafe_allow_html=True)
