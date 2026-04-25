#!/usr/bin/env python3
"""
KUKU PROJECT - Worker Forms v2.0
Forms for Juma and workers to enter daily farm data
Includes: Weight Grid, Sales, Feed, Mortality, Expenses, Events, Checklist
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
    
    .weight-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 5px;
        margin: 15px 0;
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

@st.cache_resource
def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def fresh_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

conn = get_conn()

def get_active_batches():
    try:
        cur = fresh_conn().cursor()
        cur.execute("""
            SELECT batchid, batchname, quantitychicksstarted, datestarted
            FROM batches_detailed
            ORDER BY datestarted DESC
        """)
        return cur.fetchall()
    except:
        return []

def get_expense_categories():
    try:
        cur = fresh_conn().cursor()
        cur.execute("SELECT categoryname FROM expense_categories ORDER BY categoryname")
        return [r[0] for r in cur.fetchall()]
    except:
        return ['Feed Purchase', 'Salaries', 'Transport', 'Medicines', 'Equipment',
                'Electricity Bill', 'Construction', 'Miscellaneous']

def get_feed_types():
    try:
        cur = fresh_conn().cursor()
        cur.execute("SELECT feedid, feedtype FROM feeds ORDER BY feedtype")
        return cur.fetchall()
    except:
        return [(1, 'Starter'), (2, 'Grower'), (3, 'Finisher')]

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
# TAB 1: WEIGHT CHECK (GRID INPUT)
# ============================================================================

with tabs[0]:
    st.markdown("""
    <div class="form-header">
        <h2>⚖️ Weight Check Form</h2>
        <p>Record individual bird weights - 10% sample of batch</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    if not batches:
        st.error("❌ No batches found. Please add a batch first.")
    else:
        # Batch selection
        col1, col2, col3 = st.columns(3)

        with col1:
            batch_options = {f"{b[1]} ({b[2]} birds)": b for b in batches}
            selected_batch_label = st.selectbox("Select Batch", list(batch_options.keys()))
            selected_batch = batch_options[selected_batch_label]
            batch_id = selected_batch[0]
            batch_size = selected_batch[2] or 500

        with col2:
            weigh_date = st.date_input("Weighing Date", value=date.today())

        with col3:
            day_of_cycle = st.selectbox("Day of Cycle", [7, 14, 21],
                                        help="Which weighing day is this?")

        # Calculate sample size (10% of batch)
        sample_size = max(10, round(batch_size * 0.10))
        recorded_by = st.text_input("Recorded By (Your name)", placeholder="e.g. Juma")

        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                    padding:15px; margin:15px 0; display:flex; gap:30px;">
            <div>
                <span style="color:#94A3B8; font-size:12px;">BATCH SIZE</span><br>
                <span style="color:#F1F5F9; font-size:20px; font-weight:700;">{batch_size} birds</span>
            </div>
            <div>
                <span style="color:#94A3B8; font-size:12px;">SAMPLE SIZE (10%)</span><br>
                <span style="color:#10B981; font-size:20px; font-weight:700;">{sample_size} birds</span>
            </div>
            <div>
                <span style="color:#94A3B8; font-size:12px;">DAY TARGET</span><br>
                <span style="color:#F59E0B; font-size:20px; font-weight:700;">
                    {"200g" if day_of_cycle == 7 else "550g" if day_of_cycle == 14 else "1,250g"}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### Enter Individual Bird Weights (grams) — {sample_size} birds")
        st.caption("Type each bird's weight in grams. Leave 0 if not weighed yet.")

        # Create weight input grid - 10 per row
        weights = []
        rows = (sample_size + 9) // 10  # round up

        for row in range(rows):
            cols = st.columns(10)
            for col_idx in range(10):
                bird_num = row * 10 + col_idx + 1
                if bird_num <= sample_size:
                    with cols[col_idx]:
                        w = st.number_input(
                            f"#{bird_num}",
                            min_value=0,
                            max_value=5000,
                            value=0,
                            step=1,
                            key=f"w_{bird_num}",
                            label_visibility="visible"
                        )
                        weights.append((bird_num, w))

        # Live stats (only count non-zero weights)
        entered = [(n, w) for n, w in weights if w > 0]
        entered_weights = [w for _, w in entered]

        st.markdown("---")
        st.markdown("### 📊 Live Statistics")

        if len(entered_weights) >= 2:
            avg_w = sum(entered_weights) / len(entered_weights)
            min_w = min(entered_weights)
            max_w = max(entered_weights)
            spread = max_w - min_w

            # Uniformity: birds within ±10% of average
            lower = avg_w * 0.90
            upper = avg_w * 1.10
            uniform_count = sum(1 for w in entered_weights if lower <= w <= upper)
            uniformity = (uniform_count / len(entered_weights)) * 100

            # Status vs target
            targets = {7: 200, 14: 550, 21: 1250}
            danger = {7: 180, 14: 520, 21: 1200}
            elite = {7: 220, 14: 650, 21: 1400}

            target = targets[day_of_cycle]
            dang = danger[day_of_cycle]
            elit = elite[day_of_cycle]

            deviation = ((avg_w - target) / target) * 100

            if avg_w >= elit:
                status = "🟢 ELITE"
                status_color = "status-green"
            elif avg_w >= target:
                status = "🟢 ON TARGET"
                status_color = "status-green"
            elif avg_w >= dang:
                status = "🟡 BELOW TARGET"
                status_color = "status-yellow"
            else:
                status = "🔴 DANGER"
                status_color = "status-red"

            if uniformity >= 85:
                uni_status = "🟢 GOOD"
                uni_color = "status-green"
            elif uniformity >= 80:
                uni_status = "🟡 FAIR"
                uni_color = "status-yellow"
            else:
                uni_status = "🔴 POOR"
                uni_color = "status-red"

            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Birds Entered</div>
                    <div class="stat-value status-green">{len(entered_weights)}/{sample_size}</div>
                </div>""", unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Average Weight</div>
                    <div class="stat-value {status_color}">{avg_w:.0f}g</div>
                </div>""", unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">vs Target ({target}g)</div>
                    <div class="stat-value {status_color}">{deviation:+.1f}%</div>
                </div>""", unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Min / Max</div>
                    <div class="stat-value" style="font-size:16px; color:#F1F5F9;">
                        {min_w:.0f}g / {max_w:.0f}g
                    </div>
                </div>""", unsafe_allow_html=True)

            with col5:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Uniformity</div>
                    <div class="stat-value {uni_color}">{uniformity:.0f}%</div>
                </div>""", unsafe_allow_html=True)

            with col6:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Status</div>
                    <div class="stat-value {status_color}" style="font-size:14px;">{status}</div>
                </div>""", unsafe_allow_html=True)

        else:
            st.info("👆 Enter at least 2 bird weights to see live statistics")

        notes = st.text_area("Notes (optional)", placeholder="Any observations about the birds today...")

        if st.button("💾 SAVE WEIGHT SESSION", use_container_width=True):
            valid_weights = [(n, w) for n, w in weights if w > 0]

            if len(valid_weights) < 5:
                st.error("❌ Please enter at least 5 bird weights!")
            elif not recorded_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    # Save session
                    cur.execute("""
                        INSERT INTO weight_sessions
                        (batchid, sessiondate, dayofcycle, batchsize, samplesize, recordedby, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING sessionid
                    """, (batch_id, weigh_date, day_of_cycle,
                          batch_size, sample_size, recorded_by, notes))

                    session_id = cur.fetchone()[0]

                    # Save individual weights
                    for bird_num, weight in valid_weights:
                        cur.execute("""
                            INSERT INTO weight_records (sessionid, birdnumber, weightgrams)
                            VALUES (%s, %s, %s)
                        """, (session_id, bird_num, weight))

                    c.commit()

                    avg = sum(w for _, w in valid_weights) / len(valid_weights)
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Weight session saved!<br>
                        Birds weighed: {len(valid_weights)}/{sample_size}<br>
                        Average: {avg:.0f}g | Day {day_of_cycle} target: {targets[day_of_cycle]}g
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: DAILY SALES
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

    with st.form("sales_form"):
        col1, col2 = st.columns(2)

        with col1:
            s_batch = st.selectbox("Batch", list(batch_options.keys()))
            s_date = st.date_input("Sale Date", value=date.today())
            s_buyer = st.text_input("Buyer Name", placeholder="e.g. Issa Center")

        with col2:
            s_qty = st.number_input("Birds Sold (Quantity)", min_value=1, value=50)
            s_price = st.number_input("Price per Bird (TZS)", min_value=0, value=4000)
            s_total = s_qty * s_price
            st.metric("Total Revenue", f"TZS {s_total:,}")

        s_status = st.selectbox("Payment Status",
            ["Paid", "Credit - Pending", "Partial Payment"])
        s_notes = st.text_area("Notes", placeholder="Any details about this sale...")
        s_by = st.text_input("Recorded By", placeholder="Your name")

        if st.form_submit_button("💾 SAVE SALE", use_container_width=True):
            if not s_buyer:
                st.error("❌ Please enter buyer name!")
            elif not s_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    # Get or create buyer
                    cur.execute("SELECT buyerid FROM buyers WHERE buyername = %s", (s_buyer,))
                    result = cur.fetchone()
                    if result:
                        buyer_id = result[0]
                    else:
                        cur.execute("INSERT INTO buyers (buyername) VALUES (%s) RETURNING buyerid", (s_buyer,))
                        buyer_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO daily_sales
                        (batchid, datesold, quantitysold, buyerid, unitprice, totalrevenue, salestatus, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (batch_options[s_batch], s_date, s_qty,
                          buyer_id, s_price, s_total, s_status, s_notes))

                    c.commit()
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Sale recorded!<br>
                        {s_qty} birds → {s_buyer} @ TZS {s_price:,} = TZS {s_total:,}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 3: FEED LOG
# ============================================================================

with tabs[2]:
    st.markdown("""
    <div class="form-header">
        <h2>🌾 Daily Feed Log</h2>
        <p>Record daily feed consumption</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}
    feed_types = get_feed_types()
    feed_options = {f[1]: f[0] for f in feed_types}

    with st.form("feed_form"):
        col1, col2 = st.columns(2)

        with col1:
            f_batch = st.selectbox("Batch", list(batch_options.keys()))
            f_date = st.date_input("Date", value=date.today())
            f_type = st.selectbox("Feed Type", list(feed_options.keys()))

        with col2:
            f_qty = st.number_input("Quantity (kg)", min_value=0.1,
                                     value=25.0, step=0.5)
            f_cost = st.number_input("Feed Cost (TZS)", min_value=0,
                                      value=int(f_qty * 1640))
            f_by = st.text_input("Recorded By", placeholder="Your name")

        f_notes = st.text_area("Notes", placeholder="Any issues with feed quality, delivery, etc...")

        if st.form_submit_button("💾 SAVE FEED LOG", use_container_width=True):
            if not f_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    cur.execute("""
                        INSERT INTO daily_feed_log
                        (batchid, datefed, feedtypeid, quantitykg, feedcost, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (batch_options[f_batch], f_date,
                          feed_options[f_type], f_qty, f_cost, f_notes))

                    c.commit()
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Feed log saved!<br>
                        {f_qty}kg {f_type} → TZS {f_cost:,}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 4: MORTALITY
# ============================================================================

with tabs[3]:
    st.markdown("""
    <div class="form-header">
        <h2>💔 Mortality Report</h2>
        <p>Record bird deaths</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    with st.form("mortality_form"):
        col1, col2 = st.columns(2)

        with col1:
            m_batch = st.selectbox("Batch", list(batch_options.keys()))
            m_date = st.date_input("Date", value=date.today())
            m_qty = st.number_input("Number of Deaths", min_value=1, value=1)

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
                    c = fresh_conn()
                    cur = c.cursor()

                    cur.execute("""
                        INSERT INTO daily_mortality
                        (batchid, daterecorded, quantitydied, reason, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (batch_options[m_batch], m_date,
                          m_qty, m_reason, m_notes))

                    c.commit()
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
# ============================================================================

with tabs[4]:
    st.markdown("""
    <div class="form-header">
        <h2>💸 Expense Entry</h2>
        <p>Record farm expenses and costs</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options_exp = {"No specific batch": None}
    batch_options_exp.update({f"{b[1]}": b[0] for b in batches})
    categories = get_expense_categories()

    with st.form("expense_form"):
        col1, col2 = st.columns(2)

        with col1:
            e_date = st.date_input("Expense Date", value=date.today())
            e_category = st.selectbox("Category", categories)
            e_amount = st.number_input("Amount (TZS)", min_value=0, value=0, step=500)

        with col2:
            e_batch = st.selectbox("Related Batch (Optional)",
                                    list(batch_options_exp.keys()))
            e_vendor = st.text_input("Vendor / Supplier",
                                      placeholder="Who received the money?")
            e_by = st.text_input("Recorded By", placeholder="Your name")

        e_desc = st.text_input("Description",
            placeholder="e.g. STARTER 8 BAGS @ 37,500 each")
        e_notes = st.text_area("Notes", placeholder="Any additional details...")

        if st.form_submit_button("💾 SAVE EXPENSE", use_container_width=True):
            if not e_desc:
                st.error("❌ Please enter a description!")
            elif e_amount <= 0:
                st.error("❌ Please enter a valid amount!")
            elif not e_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    batch_id = batch_options_exp[e_batch]

                    cur.execute("""
                        INSERT INTO expenses
                        (expensedate, category, description, amount,
                         receivedfrom, batchid, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (e_date, e_category, e_desc,
                          e_amount, e_vendor, batch_id, e_notes))

                    c.commit()
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Expense saved!<br>
                        {e_category}: {e_desc} → TZS {e_amount:,}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 6: CRITICAL EVENT
# ============================================================================

with tabs[5]:
    st.markdown("""
    <div class="form-header">
        <h2>⚠️ Critical Event Log</h2>
        <p>Record any problems or important events that happened today</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    with st.form("event_form"):
        col1, col2 = st.columns(2)

        with col1:
            ev_batch = st.selectbox("Batch", list(batch_options.keys()))
            ev_date = st.date_input("Event Date", value=date.today())
            ev_day = st.number_input("Day of Cycle", min_value=1,
                                      max_value=21, value=1)

        with col2:
            ev_type = st.selectbox("Event Type", [
                "Light Failure",
                "Feed Shortage",
                "Water Supply Issue",
                "Mortality Spike",
                "Disease Outbreak",
                "Equipment Failure",
                "Power Outage",
                "Temperature Problem",
                "Feed Quality Issue",
                "Other"
            ])
            ev_severity = st.selectbox("Severity", [
                "⚪ Low",
                "🟡 Medium",
                "🟠 High",
                "🔴 Critical"
            ])

        ev_desc = st.text_area("What Happened?",
            placeholder="Describe exactly what happened in detail...")
        ev_action = st.text_area("Action Taken",
            placeholder="What did you do about it?")
        ev_by = st.text_input("Recorded By", placeholder="Your name")

        if st.form_submit_button("💾 SAVE EVENT LOG", use_container_width=True):
            if not ev_desc:
                st.error("❌ Please describe what happened!")
            elif not ev_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    cur.execute("""
                        INSERT INTO critical_events
                        (batchid, eventdate, dayofcycle, eventtype,
                         severity, description, actiontaken, recordedby)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (batch_options[ev_batch], ev_date, ev_day,
                          ev_type, ev_severity, ev_desc,
                          ev_action, ev_by))

                    c.commit()
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ Event logged!<br>
                        {ev_type} | Severity: {ev_severity}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 7: DAILY CHECKLIST
# ============================================================================

with tabs[6]:
    st.markdown("""
    <div class="form-header">
        <h2>✅ Daily Checklist</h2>
        <p>End of shift checklist - confirm all tasks completed</p>
    </div>
    """, unsafe_allow_html=True)

    batches = get_active_batches()
    batch_options = {f"{b[1]}": b[0] for b in batches}

    with st.form("checklist_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            cl_batch = st.selectbox("Batch", list(batch_options.keys()))
            cl_date = st.date_input("Date", value=date.today())

        with col2:
            cl_shift = st.selectbox("Shift", ["Morning", "Afternoon", "Evening"])
            cl_by = st.text_input("Your Name", placeholder="Worker name")

        st.markdown("---")
        st.markdown("### ✅ Task Completion")

        col1, col2 = st.columns(2)

        with col1:
            cl_feed = st.checkbox("🌾 Feed Refilled")
            cl_feed_times = st.number_input("How many times refilled?",
                min_value=0, max_value=10, value=0,
                disabled=not cl_feed)
            cl_water = st.checkbox("💧 Water Supply Checked & Refilled")
            cl_lights = st.checkbox("💡 Lights Checked (all working)")

        with col2:
            cl_temp = st.checkbox("🌡️ Temperature Checked")
            cl_temp_val = st.number_input("Temperature Reading (°C)",
                min_value=0.0, max_value=50.0, value=28.0, step=0.5,
                disabled=not cl_temp)
            cl_vent = st.checkbox("💨 Ventilation Checked")
            cl_mortality = st.checkbox("💔 Checked for Dead Birds")

        st.markdown("---")
        cl_notes = st.text_area("Any Issues or Observations?",
            placeholder="Report anything unusual - smells, sounds, sick birds, equipment issues...")

        if st.form_submit_button("💾 SUBMIT CHECKLIST", use_container_width=True):
            if not cl_by:
                st.error("❌ Please enter your name!")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()

                    cur.execute("""
                        INSERT INTO daily_checklist
                        (batchid, checkdate, shift, feedrefilled,
                         feedrefilledtimes, waterchecked, lightschecked,
                         temperaturechecked, temperaturereading,
                         ventilationchecked, recordedby, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        batch_options[cl_batch], cl_date, cl_shift,
                        cl_feed, cl_feed_times if cl_feed else 0,
                        cl_water, cl_lights, cl_temp,
                        cl_temp_val if cl_temp else None,
                        cl_vent, cl_by, cl_notes
                    ))

                    c.commit()

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
    🐔 KUKU Farm Worker Forms v2.0 | Report problems to farm owner
</p>
""", unsafe_allow_html=True)
