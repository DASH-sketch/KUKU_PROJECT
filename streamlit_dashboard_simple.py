#!/usr/bin/env python3
"""
KUKU PROJECT - Simple Dashboard
System status and basic info
"""

import streamlit as st
import psycopg2
from datetime import datetime
import os

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("🐔 KUKU Farm Dashboard")
st.markdown("Farm management system - Online")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_database_connection():
    """Connect to Supabase"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return None
        conn = psycopg2.connect(db_url)
        return conn
    except:
        return None

conn = get_database_connection()

# ============================================================================
# MAIN DISPLAY
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    if conn:
        st.metric("Database", "✅ Connected")
    else:
        st.metric("Database", "❌ Not Connected")

with col2:
    st.metric("System", "✅ Online")

with col3:
    st.metric("Version", "1.0")

with col4:
    st.metric("Last Check", datetime.now().strftime("%H:%M"))

st.divider()

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Data Summary", "Quick Stats", "Help"])

# ============================================================================
# TAB 1: OVERVIEW
# ============================================================================

with tab1:
    st.header("📊 System Overview")
    
    st.info("""
    **KUKU Project is LIVE!** ✅
    
    Your farm management system is working. Here's what you have:
    
    **Worker Forms App:**
    - Feed Log - Daily feed consumption
    - Mortality Report - Bird deaths
    - Daily Sales - Bird sales
    - Weight Tracking - Weekly measurements
    - Market Feedback - Buyer feedback
    
    **Dashboard:**
    - Real-time data display
    - Financial analysis
    - Batch tracking
    """)

# ============================================================================
# TAB 2: DATA SUMMARY
# ============================================================================

with tab2:
    st.header("📋 Data Summary")
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Count tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            st.success(f"✅ Database has {len(tables)} tables")
            
            st.subheader("Tables Found:")
            if tables:
                table_names = [t[0] for t in tables]
                for i, name in enumerate(table_names, 1):
                    st.caption(f"{i}. {name}")
            
        except Exception as e:
            st.warning(f"Could not read tables: {str(e)[:50]}")
    else:
        st.error("Database not connected")

# ============================================================================
# TAB 3: QUICK STATS
# ============================================================================

with tab3:
    st.header("⚡ Quick Stats")
    
    if conn:
        try:
            cursor = conn.cursor()
            
            col1, col2 = st.columns(2)
            
            # Count batches
            with col1:
                try:
                    cursor.execute("SELECT COUNT(*) FROM BATCHES_DETAILED")
                    batch_count = cursor.fetchone()[0]
                    st.metric("Total Batches", batch_count)
                except:
                    st.metric("Total Batches", "?")
            
            # Count active batches
            with col2:
                try:
                    cursor.execute("SELECT COUNT(*) FROM BATCHES_DETAILED WHERE Status = 'Active'")
                    active_count = cursor.fetchone()[0]
                    st.metric("Active Batches", active_count)
                except:
                    st.metric("Active Batches", "?")
            
            col1, col2 = st.columns(2)
            
            # Total sales
            with col1:
                try:
                    cursor.execute("SELECT COUNT(*) FROM DAILY_SALES")
                    sales_count = cursor.fetchone()[0]
                    st.metric("Total Sales Records", sales_count)
                except:
                    st.metric("Total Sales Records", "?")
            
            # Total feed logs
            with col2:
                try:
                    cursor.execute("SELECT COUNT(*) FROM DAILY_FEED_LOG")
                    feed_count = cursor.fetchone()[0]
                    st.metric("Feed Log Entries", feed_count)
                except:
                    st.metric("Feed Log Entries", "?")
            
        except:
            st.error("Could not fetch stats")
    else:
        st.error("Database not connected")

# ============================================================================
# TAB 4: HELP
# ============================================================================

with tab4:
    st.header("❓ Help & Instructions")
    
    st.subheader("How to Use")
    
    st.markdown("""
    **Step 1: Share Worker Forms Link with Worker**
    - URL: Share the worker forms app link with Juma Mohamed
    - He can fill forms on his phone
    - Data saves automatically
    
    **Step 2: Review Data Here**
    - Check this dashboard to see reported data
    - Use tabs above to view summaries
    - Financial analysis coming soon
    
    **Step 3: Make Decisions**
    - Adjust feed quantities based on data
    - Plan sales based on market feedback
    - Track batch health
    
    ---
    
    **Worker Forms Available:**
    - 📦 Feed Log - How much feed given daily
    - 💔 Mortality - Deaths and reasons
    - 💰 Sales - Birds sold, price, buyer
    - ⚖️ Weight - Weekly bird weight checks
    - 📊 Feedback - Market demand and prices
    
    ---
    
    **Tips:**
    - Update batch status regularly
    - Review sales weekly
    - Check weight tracking progress
    - Monitor mortality rates
    """)
    
    st.divider()
    
    st.subheader("System Info")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("KUKU Project v1.0 - Free Farm Management System")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

if conn:
    st.success("✅ System is operational - All systems online")
else:
    st.warning("⚠️ Database connection issue - Check secrets configuration")

st.caption("KUKU Project - Farm Management System by LIEMBA")
