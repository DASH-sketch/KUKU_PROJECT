#!/usr/bin/env python3
"""
KUKU WORKER FORMS v3.0 (CORRECTED)
Uses actual Supabase schema:
- Feed purchases stored in expenses table (category='Feed Purchase', quantity=bags, unit_price=price/bag)
- Daily feed costs calculated from batch's feed purchase
"""

import streamlit as st
import psycopg2
from datetime import datetime, date
import os

st.set_page_config(page_title="KUKU Worker Forms", page_icon="🐔", layout="wide")

# ============================================================================
# DATABASE
# ============================================================================

def fresh_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def fetch_data(query, params=None):
    try:
        conn = fresh_conn()
        cur = conn.cursor()
        cur.execute(query, params or [])
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        conn.close()
        return [(dict(zip(columns, row))) for row in data]
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_batches():
    """Get active batches"""
    data = fetch_data("""
        SELECT batchid, batchname, quantitychicksstarted, datestarted, dateended, status
        FROM public.batches_detailed
        WHERE status IN ('Active', 'Ongoing')
        ORDER BY datestarted DESC
    """)
    return {f"{b['batchname']} ({b['quantitychicksstarted']} birds)": b['batchid'] for b in data}

def get_feed_types():
    """Get available feed types"""
    data = fetch_data("SELECT feedid, feedtype FROM public.feeds ORDER BY feedtype")
    return {f['feedtype']: f['feedid'] for f in data}

def get_batch_feed_unit_cost(batchid):
    """
    Get the actual unit cost per kg that this batch paid for feed (most recent purchase)
    Queries actual schema: expenses.category, expenses.quantity (bags), expenses.unit_price (per bag)
    """
    data = fetch_data("""
        SELECT 
            ROUND((amount::numeric / (quantity * 50))::numeric, 0) as unit_cost_per_kg,
            expensedate,
            quantity as bags,
            ROUND(unit_price::numeric) as price_per_bag,
            ROUND(amount::numeric) as total_cost
        FROM public.expenses
        WHERE batchid = %s
        AND category = 'Feed Purchase'
        ORDER BY expensedate DESC
        LIMIT 1
    """, [batchid])
    
    if data:
        return {
            'unit_cost_per_kg': int(data[0]['unit_cost_per_kg']),
            'purchase_date': data[0]['expensedate'],
            'bags': int(data[0]['bags']),
            'price_per_bag': int(data[0]['price_per_bag']),
            'total_cost': int(data[0]['total_cost'])
        }
    return None

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
body { background-color: #0a0e27; color: #e6edf3; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px; }
.success-box {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 8px;
    padding: 12px;
    color: #10b981;
}
.warning-box {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 8px;
    padding: 12px;
    color: #f59e0b;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("# 🐔 KUKU Worker Forms")
st.markdown("*Daily farm data entry*")
st.divider()

# ============================================================================
# TABS
# ============================================================================

tabs = st.tabs([
    "📦 Feed Purchase",
    "🌾 Daily Feed Log",
    "📊 Daily Sales",
    "💸 Expenses",
    "💔 Mortality",
    "✓ Daily Checklist"
])

# ============================================================================
# TAB 1: FEED PURCHASE
# ============================================================================

with tabs[0]:
    st.markdown("## 📦 Record Feed Purchase")
    st.markdown("*Link feed purchases directly to batches for accurate cost tracking*")
    st.divider()
    
    batch_options = get_batches()
    
    if not batch_options:
        st.error("❌ No active batches found")
        st.stop()
    
    with st.form("feed_purchase_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fp_batch = st.selectbox("Batch", list(batch_options.keys()))
            fp_date = st.date_input("Purchase Date", value=date.today())
        
        with col2:
            fp_bags = st.number_input("Number of Bags (50kg each)", min_value=1, value=10, step=1)
            fp_unit_price = st.number_input("Price per Bag (TZS)", min_value=0, value=16600, step=100)
        
        fp_by = st.text_input("Recorded By", placeholder="Your name")
        
        # Auto-calculate totals
        fp_total = fp_bags * fp_unit_price
        fp_unit_cost_per_kg = fp_total / (fp_bags * 50)  # 50kg per bag
        
        st.info(f"""
        **📊 Purchase Summary:**
        - Total bags: {fp_bags} × 50kg = **{fp_bags * 50}kg**
        - Cost per bag: TZS {fp_unit_price:,}
        - **Total Cost: TZS {fp_total:,}**
        - **Unit Cost: TZS {fp_unit_cost_per_kg:,.0f}/kg**
        """)
        
        if st.form_submit_button("💾 SAVE FEED PURCHASE", use_container_width=True):
            if not fp_by:
                st.error("❌ Please enter your name")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()
                    
                    # Get Feed Purchase category_id
                    cur.execute(
                        "SELECT category_id FROM public.expense_categories WHERE category_name = %s",
                        ['Feed Purchase']
                    )
                    cat_result = cur.fetchone()
                    category_id = cat_result[0] if cat_result else None
                    
                    # Insert into expenses using actual schema
                    # category='Feed Purchase', quantity=bags, unit_price=price per bag, amount=total
                    cur.execute("""
                        INSERT INTO public.expenses
                        (expensedate, category, description, amount, quantity, unit_price, batchid, category_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        fp_date,
                        'Feed Purchase',
                        f"{fp_bags} bags feed purchase",
                        int(fp_total),
                        fp_bags,
                        int(fp_unit_price),
                        batch_options[fp_batch],
                        category_id
                    ))
                    
                    c.commit()
                    c.close()
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Feed purchase saved!<br>
                    <strong>{fp_bags} bags</strong> → <strong>TZS {fp_total:,}</strong> 
                    (TZS {fp_unit_cost_per_kg:,.0f}/kg)
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: DAILY FEED LOG
# ============================================================================

with tabs[1]:
    st.markdown("## 🌾 Daily Feed Log")
    st.markdown("*Costs auto-calculated from batch's feed purchase*")
    st.divider()
    
    batch_options = get_batches()
    feed_types = get_feed_types()
    
    if not batch_options or not feed_types:
        st.error("❌ No batches or feed types available")
        st.stop()
    
    with st.form("daily_feed_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dfl_batch = st.selectbox("Batch", list(batch_options.keys()))
            dfl_feed_type = st.selectbox("Feed Type", list(feed_types.keys()))
            dfl_date = st.date_input("Date", value=date.today())
        
        with col2:
            dfl_quantity = st.number_input("Quantity (kg)", min_value=0.1, value=25.0, step=0.5)
            dfl_by = st.text_input("Recorded By", placeholder="Your name")
        
        # Get batch's feed unit cost (from most recent purchase)
        batch_id = batch_options[dfl_batch]
        feed_cost_info = get_batch_feed_unit_cost(batch_id)
        
        if feed_cost_info:
            unit_cost = feed_cost_info['unit_cost_per_kg']
            total_cost = dfl_quantity * unit_cost
            
            st.markdown(f"""
            <div class="success-box">
            <strong>✅ Using actual cost from batch purchase</strong><br>
            📅 Purchased: {feed_cost_info['purchase_date']}<br>
            💰 Unit cost: <strong>TZS {unit_cost:,}/kg</strong> ({feed_cost_info['bags']} bags × TZS {feed_cost_info['price_per_bag']:,})<br>
            🌾 Today: {dfl_quantity}kg × TZS {unit_cost:,} = <strong>TZS {total_cost:,.0f}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            if st.form_submit_button("💾 SAVE FEED LOG", use_container_width=True):
                if not dfl_by:
                    st.error("❌ Please enter your name")
                else:
                    try:
                        c = fresh_conn()
                        cur = c.cursor()
                        
                        cur.execute("""
                            INSERT INTO public.daily_feed_log
                            (batchid, datefed, feedtypeid, quantitykg, feedcost, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            batch_id,
                            dfl_date,
                            feed_types[dfl_feed_type],
                            dfl_quantity,
                            int(total_cost),
                            f"Recorded by {dfl_by}"
                        ))
                        
                        c.commit()
                        c.close()
                        
                        st.markdown(f"""
                        <div class="success-box">
                        ✅ Feed log saved!<br>
                        {dfl_quantity}kg → TZS {total_cost:,.0f}
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.markdown(f"""
            <div class="warning-box">
            ⚠️ No feed purchase found for {dfl_batch}!<br>
            Please record the feed purchase first in the <strong>Feed Purchase</strong> tab before logging daily feed.
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# TAB 3: DAILY SALES
# ============================================================================

with tabs[2]:
    st.markdown("## 📊 Daily Sales")
    
    batch_options = get_batches()
    
    with st.form("sales_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            s_batch = st.selectbox("Batch", list(batch_options.keys()))
            s_date = st.date_input("Date Sold", value=date.today())
        
        with col2:
            s_quantity = st.number_input("Birds Sold", min_value=1, value=100)
            s_unit_price = st.number_input("Price per Bird (TZS)", min_value=0, value=5400)
        
        with col3:
            s_buyer = st.text_input("Buyer Name")
            s_by = st.text_input("Recorded By")
        
        s_total = s_quantity * s_unit_price
        st.info(f"Total Revenue: {s_quantity} birds × TZS {s_unit_price:,} = **TZS {s_total:,}**")
        
        if st.form_submit_button("💾 SAVE SALE", use_container_width=True):
            if not s_buyer or not s_by:
                st.error("❌ Fill all fields")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()
                    
                    # Get or create buyer
                    cur.execute("SELECT buyerid FROM public.buyers WHERE buyername = %s", [s_buyer])
                    buyer = cur.fetchone()
                    
                    if not buyer:
                        cur.execute("""
                            INSERT INTO public.buyers (buyername) VALUES (%s)
                            RETURNING buyerid
                        """, [s_buyer])
                        buyer_id = cur.fetchone()[0]
                    else:
                        buyer_id = buyer[0]
                    
                    # Save sale
                    cur.execute("""
                        INSERT INTO public.daily_sales
                        (batchid, datesold, quantitysold, unitprice, totalrevenue, buyerid)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        batch_options[s_batch],
                        s_date,
                        s_quantity,
                        s_unit_price,
                        s_total,
                        buyer_id
                    ))
                    
                    c.commit()
                    c.close()
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Sale recorded!<br>
                    {s_quantity} birds to {s_buyer} → TZS {s_total:,}
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 4: OTHER EXPENSES
# ============================================================================

with tabs[3]:
    st.markdown("## 💸 Other Expenses")
    st.markdown("*(Feed purchases are recorded in the Feed Purchase tab)*")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            e_date = st.date_input("Date", value=date.today())
            e_description = st.text_input("Description", placeholder="e.g., Medicine, Labor, Equipment")
        
        with col2:
            e_amount = st.number_input("Amount (TZS)", min_value=0, value=5000)
            e_by = st.text_input("Recorded By")
        
        if st.form_submit_button("💾 SAVE EXPENSE", use_container_width=True):
            if not e_description or not e_by:
                st.error("❌ Fill all fields")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()
                    
                    cur.execute("""
                        INSERT INTO public.expenses (expensedate, category, description, amount)
                        VALUES (%s, %s, %s, %s)
                    """, (e_date, 'Other', e_description, int(e_amount)))
                    
                    c.commit()
                    c.close()
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Expense recorded!<br>
                    {e_description} → TZS {e_amount:,}
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 5: MORTALITY
# ============================================================================

with tabs[4]:
    st.markdown("## 💔 Daily Mortality")
    
    batch_options = get_batches()
    
    with st.form("mortality_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            m_batch = st.selectbox("Batch", list(batch_options.keys()))
            m_date = st.date_input("Date", value=date.today())
        
        with col2:
            m_quantity = st.number_input("Birds Died", min_value=1, value=1)
            m_reason = st.selectbox("Reason", [
                "Disease",
                "Injury/Accident",
                "Predator",
                "Unknown",
                "Other"
            ])
        
        m_by = st.text_input("Recorded By")
        
        if st.form_submit_button("💾 SAVE MORTALITY", use_container_width=True):
            if not m_by:
                st.error("❌ Enter your name")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()
                    
                    cur.execute("""
                        INSERT INTO public.daily_mortality
                        (batchid, daterecorded, quantitydied, reason)
                        VALUES (%s, %s, %s, %s)
                    """, (batch_options[m_batch], m_date, m_quantity, m_reason))
                    
                    c.commit()
                    c.close()
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Mortality recorded!<br>
                    {m_quantity} birds - {m_reason}
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 6: DAILY CHECKLIST
# ============================================================================

with tabs[5]:
    st.markdown("## ✓ Daily Checklist")
    
    batch_options = get_batches()
    
    with st.form("checklist_form"):
        cl_batch = st.selectbox("Batch", list(batch_options.keys()))
        cl_date = st.date_input("Date", value=date.today())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cl_fed = st.checkbox("🌾 Fed birds?")
            cl_water = st.checkbox("💧 Water checked?")
        
        with col2:
            cl_lights = st.checkbox("💡 Lights OK?")
            cl_temp = st.checkbox("🌡️ Temperature OK?")
        
        with col3:
            cl_vent = st.checkbox("🌬️ Ventilation OK?")
            cl_clean = st.checkbox("🧹 Cleaned?")
        
        cl_notes = st.text_area("Notes", placeholder="Any issues or observations...")
        cl_by = st.text_input("Recorded By")
        
        tasks_done = sum([cl_fed, cl_water, cl_lights, cl_temp, cl_vent, cl_clean])
        
        st.info(f"✅ {tasks_done}/6 tasks completed")
        
        if st.form_submit_button("💾 SAVE CHECKLIST", use_container_width=True):
            if not cl_by:
                st.error("❌ Enter your name")
            else:
                try:
                    c = fresh_conn()
                    cur = c.cursor()
                    
                    cur.execute("""
                        INSERT INTO public.daily_checklist
                        (BatchID, CheckDate, FeedRefilled, WaterChecked, LightsChecked, 
                         TemperatureChecked, VentilationChecked, RecordedBy, Notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        batch_options[cl_batch],
                        cl_date,
                        cl_fed, cl_water, cl_lights, cl_temp, cl_vent, cl_clean,
                        cl_notes if cl_notes else f"Recorded by {cl_by}"
                    ))
                    
                    c.commit()
                    c.close()
                    
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ Checklist saved!<br>
                    {tasks_done}/6 tasks completed
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #8b949e; font-size: 11px; padding: 16px 0;">
KUKU Worker Forms v3.0 | Batch-linked feed cost tracking
</div>
""", unsafe_allow_html=True)
