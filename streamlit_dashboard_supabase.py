#!/usr/bin/env python3
"""
KUKU PROJECT - Dashboard (Supabase Version)
Shows farm data in real-time
"""

import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_database_connection():
    """Connect to Supabase via Session Pooler"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            st.error("❌ DATABASE_URL secret not configured!")
            st.stop()
        
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)[:100]}")
        st.info("Check DATABASE_URL secret and try again")
        st.stop()

conn = get_database_connection()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run_query(query):
    """Execute a query and return results as DataFrame"""
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Query error: {str(e)[:100]}")
        return pd.DataFrame()

def get_active_batches():
    """Get all active batches"""
    query = """
    SELECT BatchID, BatchName, DateStarted, Status, QuantityChicksStarted
    FROM BATCHES_DETAILED
    WHERE Status = 'Active'
    ORDER BY DateStarted DESC
    """
    return run_query(query)

def get_completed_batches():
    """Get completed batches"""
    query = """
    SELECT BatchID, BatchName, DateStarted, DateEnded, Status
    FROM BATCHES_DETAILED
    WHERE Status = 'Completed'
    ORDER BY DateEnded DESC
    LIMIT 8
    """
    return run_query(query)

def get_batch_summary(batch_id):
    """Get summary for a specific batch"""
    query = f"""
    SELECT 
        b.BatchID,
        b.BatchName,
        b.DateStarted,
        b.QuantityChicksStarted,
        COUNT(DISTINCT m.MortalityID) as TotalDeaths,
        COALESCE(SUM(s.QuantitySold), 0) as TotalSold,
        COALESCE(SUM(s.TotalRevenue), 0) as TotalRevenue,
        COALESCE(SUM(f.FeedCost), 0) as TotalFeedCost
    FROM BATCHES_DETAILED b
    LEFT JOIN DAILY_MORTALITY m ON b.BatchID = m.BatchID
    LEFT JOIN DAILY_SALES s ON b.BatchID = s.BatchID
    LEFT JOIN DAILY_FEED_LOG f ON b.BatchID = f.BatchID
    WHERE b.BatchID = {batch_id}
    GROUP BY b.BatchID, b.BatchName, b.DateStarted, b.QuantityChicksStarted
    """
    return run_query(query)

def get_daily_feed(batch_id):
    """Get feed log for batch"""
    query = f"""
    SELECT 
        f.DateFed,
        fd.FeedType,
        f.QuantityKG,
        f.FeedCost
    FROM DAILY_FEED_LOG f
    LEFT JOIN FEEDS fd ON f.FeedTypeID = fd.FeedID
    WHERE f.BatchID = {batch_id}
    ORDER BY f.DateFed DESC
    LIMIT 30
    """
    return run_query(query)

def get_daily_mortality(batch_id):
    """Get mortality for batch"""
    query = f"""
    SELECT 
        DateRecorded,
        QuantityDied,
        Reason
    FROM DAILY_MORTALITY
    WHERE BatchID = {batch_id}
    ORDER BY DateRecorded DESC
    LIMIT 30
    """
    return run_query(query)

def get_daily_sales(batch_id):
    """Get sales for batch"""
    query = f"""
    SELECT 
        s.DateSold,
        b.BuyerName,
        s.QuantitySold,
        s.UnitPrice,
        s.TotalRevenue,
        s.SaleStatus
    FROM DAILY_SALES s
    LEFT JOIN BUYERS b ON s.BuyerID = b.BuyerID
    WHERE s.BatchID = {batch_id}
    ORDER BY s.DateSold DESC
    LIMIT 30
    """
    return run_query(query)

def get_weight_tracking(batch_id):
    """Get weight data for batch"""
    query = f"""
    SELECT 
        DateMeasured,
        Week,
        AverageWeightPerBird
    FROM WEIGHT_TRACKING
    WHERE BatchID = {batch_id}
    ORDER BY Week ASC
    """
    return run_query(query)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("🐔 KUKU Farm Dashboard")
st.markdown("Real-time farm management data")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Active Batches", "Batch Details", "Financial Analysis", "Reports"]
)

# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================

if page == "Overview":
    st.header("📊 Overview")
    
    active = get_active_batches()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🐔 Active Batches", len(active))
    
    with col2:
        if len(active) > 0:
            total_birds = active['QuantityChicksStarted'].sum()
            st.metric("Total Birds", int(total_birds))
        else:
            st.metric("Total Birds", 0)
    
    with col3:
        today = datetime.now().date()
        st.metric("Today's Date", today.strftime("%Y-%m-%d"))
    
    with col4:
        st.metric("Status", "✅ Online")
    
    st.divider()
    
    if len(active) > 0:
        st.subheader("Active Batches")
        st.dataframe(active, use_container_width=True)
    else:
        st.info("No active batches. Create a batch in worker forms!")

# ============================================================================
# PAGE 2: ACTIVE BATCHES
# ============================================================================

elif page == "Active Batches":
    st.header("🐣 Active Batches")
    
    active = get_active_batches()
    
    if len(active) == 0:
        st.info("No active batches")
    else:
        st.dataframe(active, use_container_width=True)
        
        st.subheader("Batch Details")
        selected_batch = st.selectbox(
            "Select a batch",
            active['BatchID'].tolist(),
            format_func=lambda x: f"Batch {x} - {active[active['BatchID']==x]['BatchName'].values[0]}"
        )
        
        summary = get_batch_summary(selected_batch)
        if len(summary) > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Started", summary['DateStarted'].values[0])
            with col2:
                st.metric("Started With", int(summary['QuantityChicksStarted'].values[0]))
            with col3:
                st.metric("Deaths", int(summary['TotalDeaths'].values[0]))
            with col4:
                st.metric("Sold", int(summary['TotalSold'].values[0]))

# ============================================================================
# PAGE 3: BATCH DETAILS
# ============================================================================

elif page == "Batch Details":
    st.header("📋 Batch Details")
    
    all_batches = run_query("SELECT BatchID, BatchName FROM BATCHES_DETAILED ORDER BY BatchID DESC")
    
    if len(all_batches) == 0:
        st.info("No batches found")
    else:
        selected_batch = st.selectbox(
            "Select a batch",
            all_batches['BatchID'].tolist(),
            format_func=lambda x: f"Batch {x} - {all_batches[all_batches['BatchID']==x]['BatchName'].values[0]}"
        )
        
        # Summary
        summary = get_batch_summary(selected_batch)
        if len(summary) > 0:
            st.subheader("Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Started", str(summary['DateStarted'].values[0])[:10])
            with col2:
                st.metric("Initial Birds", int(summary['QuantityChicksStarted'].values[0]))
            with col3:
                st.metric("Total Deaths", int(summary['TotalDeaths'].values[0]))
            with col4:
                st.metric("Total Sold", int(summary['TotalSold'].values[0]))
        
        # Feed Log
        st.subheader("📦 Feed Consumption")
        feed_df = get_daily_feed(selected_batch)
        if len(feed_df) > 0:
            st.dataframe(feed_df, use_container_width=True)
        else:
            st.info("No feed data")
        
        # Mortality
        st.subheader("💔 Mortality Report")
        mort_df = get_daily_mortality(selected_batch)
        if len(mort_df) > 0:
            st.dataframe(mort_df, use_container_width=True)
        else:
            st.info("No mortality recorded")
        
        # Sales
        st.subheader("💰 Sales")
        sales_df = get_daily_sales(selected_batch)
        if len(sales_df) > 0:
            st.dataframe(sales_df, use_container_width=True)
        else:
            st.info("No sales recorded")
        
        # Weight Tracking
        st.subheader("⚖️ Weight Tracking")
        weight_df = get_weight_tracking(selected_batch)
        if len(weight_df) > 0:
            st.dataframe(weight_df, use_container_width=True)
            if len(weight_df) > 1:
                st.line_chart(weight_df.set_index('Week')['AverageWeightPerBird'])
        else:
            st.info("No weight data")

# ============================================================================
# PAGE 4: FINANCIAL ANALYSIS
# ============================================================================

elif page == "Financial Analysis":
    st.header("💵 Financial Analysis")
    
    completed = get_completed_batches()
    
    if len(completed) == 0:
        st.info("No completed batches for analysis")
    else:
        # Get detailed financial info
        financial_query = """
        SELECT 
            b.BatchID,
            b.BatchName,
            COALESCE(SUM(s.TotalRevenue), 0) as Revenue,
            COALESCE(SUM(f.FeedCost), 0) as FeedCost,
            COALESCE(SUM(s.TotalRevenue), 0) - COALESCE(SUM(f.FeedCost), 0) as Profit
        FROM BATCHES_DETAILED b
        LEFT JOIN DAILY_SALES s ON b.BatchID = s.BatchID
        LEFT JOIN DAILY_FEED_LOG f ON b.BatchID = f.BatchID
        WHERE b.Status = 'Completed'
        GROUP BY b.BatchID, b.BatchName
        ORDER BY b.BatchID DESC
        LIMIT 8
        """
        
        financial_df = run_query(financial_query)
        
        if len(financial_df) > 0:
            st.dataframe(financial_df, use_container_width=True)
            
            st.subheader("Revenue vs Costs")
            chart_df = financial_df[['BatchName', 'Revenue', 'FeedCost']].set_index('BatchName')
            st.bar_chart(chart_df)
            
            st.subheader("Total Profit")
            total_profit = financial_df['Profit'].sum()
            st.metric("Total Profit (Last 8 Batches)", f"TZS {int(total_profit):,}")

# ============================================================================
# PAGE 5: REPORTS
# ============================================================================

elif page == "Reports":
    st.header("📄 Reports")
    
    st.subheader("Quick Stats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        active_count = len(get_active_batches())
        st.info(f"**Active Batches:** {active_count}")
    
    with col2:
        completed = get_completed_batches()
        st.info(f"**Completed Batches:** {len(completed)}")
    
    st.divider()
    
    st.subheader("Market Feedback")
    feedback_query = """
    SELECT 
        b.BuyerName,
        f.DemandLevel,
        f.PriceResistance,
        f.Comments,
        f.DateFeedback
    FROM MARKET_FEEDBACK f
    LEFT JOIN BUYERS b ON f.BuyerID = b.BuyerID
    ORDER BY f.DateFeedback DESC
    LIMIT 10
    """
    
    feedback_df = run_query(feedback_query)
    if len(feedback_df) > 0:
        st.dataframe(feedback_df, use_container_width=True)
    else:
        st.info("No market feedback recorded")
    
    st.divider()
    
    st.subheader("Buyers")
    buyers_query = "SELECT BuyerID, BuyerName, Location, Status FROM BUYERS ORDER BY BuyerName"
    buyers_df = run_query(buyers_query)
    if len(buyers_df) > 0:
        st.dataframe(buyers_df, use_container_width=True)
    else:
        st.info("No buyers configured")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("KUKU Project - Farm Management System")
