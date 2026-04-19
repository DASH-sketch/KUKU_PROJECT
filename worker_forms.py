#!/usr/bin/env python3
"""
KUKU PROJECT - Worker Mobile Forms
Dynamic forms connected to database
Automatically shows active batches from database
No manual form updates needed!
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="KUKU Worker Forms",
    page_icon="phone",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .form-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-message {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_database_connection():
    """Connect to SQLite database"""
    db_path = Path("kuku_project.db")
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_database_connection()

# ============================================================================
# HELPER FUNCTIONS - AUTO-FETCH FROM DATABASE
# ============================================================================

def get_active_batches():
    """Get ALL active batches from database"""
    query = """
    SELECT BatchID, BatchName
    FROM BATCHES_DETAILED
    WHERE Status IN ('Active', 'Selling')
    ORDER BY BatchID DESC
    """
    df = pd.read_sql_query(query, conn)
    return df

def get_feed_types():
    """Get all feed types from database"""
    query = "SELECT FeedType FROM FEEDS ORDER BY FeedType"
    df = pd.read_sql_query(query, conn)
    return df['FeedType'].tolist()

def get_buyers():
    """Get all buyers from database"""
    query = "SELECT BuyerName FROM BUYERS WHERE Status = 'Active' ORDER BY BuyerName"
    df = pd.read_sql_query(query, conn)
    return df['BuyerName'].tolist()

def get_batch_by_name(batch_name):
    """Get batch ID by name"""
    query = "SELECT BatchID FROM BATCHES_DETAILED WHERE BatchName = ?"
    result = pd.read_sql_query(query, conn, params=(batch_name,))
    return result.iloc[0]['BatchID'] if len(result) > 0 else None

def get_feed_price(feed_type):
    """Get feed price from database"""
    query = "SELECT UnitPrice FROM FEEDS WHERE FeedType = ?"
    result = pd.read_sql_query(query, conn, params=(feed_type,))
    return result.iloc[0]['UnitPrice'] if len(result) > 0 else 0

# ============================================================================
# FORM 1: DAILY FEED LOG
# ============================================================================

def form_feed_log():
    """Daily Feed Log Form"""
    st.header("Daily Feed Log")
    st.markdown("Enter today's feed usage")
    
    # Get active batches (auto-updated from database!)
    active_batches = get_active_batches()
    batch_names = active_batches['BatchName'].tolist()
    
    if len(batch_names) == 0:
        st.warning("No active batches found. Contact manager.")
        return
    
    with st.form("feed_log_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.selectbox(
                "Which batch?",
                options=batch_names,
                key="feed_batch"
            )
            date = st.date_input("Date", datetime.now())
        
        with col2:
            feed_type = st.selectbox(
                "Feed type",
                options=get_feed_types(),
                key="feed_type"
            )
            quantity = st.number_input(
                "Quantity (kg)",
                min_value=0.0,
                step=0.5,
                key="feed_qty"
            )
        
        notes = st.text_area(
            "Any issues?",
            placeholder="Feed quality, bird behavior, etc.",
            key="feed_notes"
        )
        
        submitted = st.form_submit_button("Submit Feed Log", use_container_width=True)
        
        if submitted:
            try:
                batch_id = get_batch_by_name(batch_name)
                feed_price = get_feed_price(feed_type)
                feed_cost = quantity * feed_price
                
                # Get feed type ID
                feed_result = pd.read_sql_query(
                    "SELECT FeedID FROM FEEDS WHERE FeedType = ?",
                    conn,
                    params=(feed_type,)
                )
                feed_id = feed_result.iloc[0]['FeedID']
                
                # Insert into database
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO DAILY_FEED_LOG
                (BatchID, DateFed, FeedTypeID, QuantityKG, FeedCost, Notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (batch_id, date, feed_id, quantity, feed_cost, notes))
                conn.commit()
                
                st.markdown("""
                <div class="success-message">
                <strong>Success!</strong> Feed log recorded.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# FORM 2: DAILY MORTALITY
# ============================================================================

def form_mortality():
    """Daily Mortality Report Form"""
    st.header("Daily Mortality Report")
    st.markdown("Report bird deaths")
    
    active_batches = get_active_batches()
    batch_names = active_batches['BatchName'].tolist()
    
    if len(batch_names) == 0:
        st.warning("No active batches found.")
        return
    
    with st.form("mortality_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.selectbox(
                "Which batch?",
                options=batch_names,
                key="mort_batch"
            )
            date = st.date_input("Date", datetime.now(), key="mort_date")
        
        with col2:
            qty_died = st.number_input(
                "How many died?",
                min_value=0,
                key="mort_qty"
            )
            reason = st.selectbox(
                "Likely cause",
                options=["Disease", "Accident", "Starvation", "Unknown", "Other"],
                key="mort_reason"
            )
        
        notes = st.text_area(
            "Notes",
            placeholder="Symptoms, observations, etc.",
            key="mort_notes"
        )
        
        submitted = st.form_submit_button("Submit Mortality Report", use_container_width=True)
        
        if submitted:
            try:
                batch_id = get_batch_by_name(batch_name)
                
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO DAILY_MORTALITY
                (BatchID, DateRecorded, QuantityDied, Reason, Notes)
                VALUES (?, ?, ?, ?, ?)
                """, (batch_id, date, qty_died, reason, notes))
                conn.commit()
                
                st.markdown("""
                <div class="success-message">
                <strong>Success!</strong> Mortality report recorded.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# FORM 3: DAILY SALES
# ============================================================================

def form_sales():
    """Daily Sales Log Form"""
    st.header("Daily Sales Log")
    st.markdown("Record bird sales")
    
    active_batches = get_active_batches()
    batch_names = active_batches['BatchName'].tolist()
    buyers = get_buyers()
    
    if len(batch_names) == 0:
        st.warning("No active batches found.")
        return
    
    with st.form("sales_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.selectbox(
                "Which batch?",
                options=batch_names,
                key="sales_batch"
            )
            date = st.date_input("Sale date", datetime.now(), key="sales_date")
        
        with col2:
            qty_sold = st.number_input(
                "How many sold?",
                min_value=0,
                key="sales_qty"
            )
            price = st.number_input(
                "Price per bird (TZS)",
                min_value=0.0,
                step=100.0,
                key="sales_price"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            buyer = st.selectbox(
                "Buyer",
                options=buyers,
                key="sales_buyer"
            )
        
        with col2:
            status = st.selectbox(
                "Status",
                options=["Sold & Paid", "Sold on Credit", "Reserved", "Rejected"],
                key="sales_status"
            )
        
        notes = st.text_area(
            "Notes",
            placeholder="Buyer feedback, quality comments, etc.",
            key="sales_notes"
        )
        
        submitted = st.form_submit_button("Submit Sale", use_container_width=True)
        
        if submitted:
            try:
                batch_id = get_batch_by_name(batch_name)
                
                # Get buyer ID
                buyer_result = pd.read_sql_query(
                    "SELECT BuyerID FROM BUYERS WHERE BuyerName = ?",
                    conn,
                    params=(buyer,)
                )
                buyer_id = buyer_result.iloc[0]['BuyerID']
                
                total_revenue = qty_sold * price
                
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO DAILY_SALES
                (BatchID, DateSold, QuantitySold, BuyerID, UnitPrice, TotalRevenue, SaleStatus, Notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (batch_id, date, qty_sold, buyer_id, price, total_revenue, status, notes))
                conn.commit()
                
                st.markdown("""
                <div class="success-message">
                <strong>Success!</strong> Sale recorded.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# FORM 4: WEIGHT CHECK
# ============================================================================

def form_weight():
    """Weekly Weight Check Form"""
    st.header("Weekly Weight Check")
    st.markdown("Measure bird weight progression")
    
    active_batches = get_active_batches()
    batch_names = active_batches['BatchName'].tolist()
    
    if len(batch_names) == 0:
        st.warning("No active batches found.")
        return
    
    with st.form("weight_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.selectbox(
                "Which batch?",
                options=batch_names,
                key="weight_batch"
            )
            date = st.date_input("Measurement date", datetime.now(), key="weight_date")
        
        with col2:
            week = st.selectbox(
                "Which week?",
                options=["Week 1 (Days 1-7)", "Week 2 (Days 8-14)", "Week 3 (Days 15-21)", "Week 4+"],
                key="weight_week"
            )
            total_weight = st.number_input(
                "Total weight of 10 birds (kg)",
                min_value=0.0,
                step=0.1,
                key="weight_total"
            )
        
        notes = st.text_area(
            "Health observations",
            placeholder="Appetite, growth rate, health status, etc.",
            key="weight_notes"
        )
        
        submitted = st.form_submit_button("Submit Weight Check", use_container_width=True)
        
        if submitted:
            try:
                batch_id = get_batch_by_name(batch_name)
                
                # Extract week number from selection
                week_num = int(week.split()[1])
                avg_weight = total_weight / 10
                
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO WEIGHT_TRACKING
                (BatchID, DateMeasured, Week, AverageWeightPerBird, SampleSize, Notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (batch_id, date, week_num, avg_weight, 10, notes))
                conn.commit()
                
                st.markdown("""
                <div class="success-message">
                <strong>Success!</strong> Weight check recorded.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# FORM 5: MARKET FEEDBACK
# ============================================================================

def form_feedback():
    """Market Feedback Form"""
    st.header("Market Feedback")
    st.markdown("Report demand and market conditions")
    
    buyers = get_buyers()
    
    if len(buyers) == 0:
        st.warning("No buyers found.")
        return
    
    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            buyer = st.selectbox(
                "Who did you speak with?",
                options=buyers,
                key="fb_buyer"
            )
            date = st.date_input("Conversation date", datetime.now(), key="fb_date")
        
        with col2:
            demand = st.selectbox(
                "Demand level",
                options=["Very Good", "Good", "Soft", "Weak", "Dead"],
                key="fb_demand"
            )
            price_resist = st.selectbox(
                "Price resistance?",
                options=["No", "Minor", "Strong", "Not asked"],
                key="fb_price"
            )
        
        competitors = st.selectbox(
            "Competition?",
            options=["None", "One competitor", "Multiple competitors", "Unknown"],
            key="fb_comp"
        )
        
        comments = st.text_area(
            "Comments",
            placeholder="Trends, buyer needs, seasonal patterns, etc.",
            key="fb_comments"
        )
        
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submitted:
            try:
                # Get buyer ID
                buyer_result = pd.read_sql_query(
                    "SELECT BuyerID FROM BUYERS WHERE BuyerName = ?",
                    conn,
                    params=(buyer,)
                )
                buyer_id = buyer_result.iloc[0]['BuyerID']
                
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO MARKET_FEEDBACK
                (DateFeedback, BuyerID, DemandLevel, PriceResistance, CompetitorActivity, Comments)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (date, buyer_id, demand, price_resist, competitors, comments))
                conn.commit()
                
                st.markdown("""
                <div class="success-message">
                <strong>Success!</strong> Feedback recorded.
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.title("KUKU Worker Forms")
st.markdown("Mobile-friendly data entry forms")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Feed Log", use_container_width=True, key="btn_feed"):
        st.session_state.form = "feed"

with col2:
    if st.button("Mortality", use_container_width=True, key="btn_mort"):
        st.session_state.form = "mortality"

with col3:
    if st.button("Sales", use_container_width=True, key="btn_sales"):
        st.session_state.form = "sales"

col1, col2 = st.columns(2)

with col1:
    if st.button("Weight", use_container_width=True, key="btn_weight"):
        st.session_state.form = "weight"

with col2:
    if st.button("Feedback", use_container_width=True, key="btn_feedback"):
        st.session_state.form = "feedback"

st.divider()

# Initialize session state
if 'form' not in st.session_state:
    st.session_state.form = None

# Display selected form
if st.session_state.form == "feed":
    form_feed_log()
elif st.session_state.form == "mortality":
    form_mortality()
elif st.session_state.form == "sales":
    form_sales()
elif st.session_state.form == "weight":
    form_weight()
elif st.session_state.form == "feedback":
    form_feedback()
else:
    st.info("Click a button above to start entering data!")
    st.markdown("""
    **Available Forms:**
    - Feed Log - Daily feed consumption
    - Mortality - Bird deaths
    - Sales - Bird sales
    - Weight - Weekly weight measurements
    - Feedback - Market demand feedback
    
    All batches and buyers automatically sync from database!
    """)

st.divider()
st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
