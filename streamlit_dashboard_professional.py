#!/usr/bin/env python3
"""
KUKU PROJECT - Professional Dashboard with Financial Reports
Real-time farm management with profit analysis
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_database_connection():
    """Connect to Supabase"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            st.error("❌ DATABASE_URL not configured")
            st.stop()
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)[:100]}")
        st.stop()

conn = get_database_connection()

def run_query(query):
    """Execute query and return DataFrame"""
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Query error: {str(e)[:100]}")
        return pd.DataFrame()

# ============================================================================
# QUERIES
# ============================================================================

def get_all_batches():
    """Get all batches"""
    return run_query("""
        SELECT BatchID, BatchName, DateStarted, Status 
        FROM BATCHES_DETAILED 
        ORDER BY DateStarted DESC
    """)

def get_active_batches():
    """Get active batches"""
    return run_query("""
        SELECT COUNT(*) as count FROM BATCHES_DETAILED WHERE Status = 'Active'
    """)

def get_completed_batches():
    """Get completed batches"""
    return run_query("""
        SELECT COUNT(*) as count FROM BATCHES_DETAILED WHERE Status = 'Completed'
    """)

def get_financial_summary():
    """Get overall financial summary"""
    return run_query("""
        SELECT 
            COALESCE(SUM(s.TotalRevenue), 0) as TotalRevenue,
            COALESCE(SUM(f.FeedCost), 0) as TotalFeedCost
        FROM DAILY_SALES s
        FULL OUTER JOIN DAILY_FEED_LOG f ON 1=1
    """)

def get_batch_financial_details():
    """Get financial details for each batch"""
    return run_query("""
        SELECT 
            b.BatchID,
            b.BatchName,
            b.Status,
            b.DateStarted,
            COALESCE(SUM(s.TotalRevenue), 0) as Revenue,
            COALESCE(SUM(f.FeedCost), 0) as FeedCost,
            COALESCE(SUM(s.TotalRevenue), 0) - COALESCE(SUM(f.FeedCost), 0) as Profit,
            COALESCE(SUM(s.QuantitySold), 0) as BirdsSold,
            COALESCE(SUM(m.QuantityDied), 0) as BirdsDied
        FROM BATCHES_DETAILED b
        LEFT JOIN DAILY_SALES s ON b.BatchID = s.BatchID
        LEFT JOIN DAILY_FEED_LOG f ON b.BatchID = f.BatchID
        LEFT JOIN DAILY_MORTALITY m ON b.BatchID = m.BatchID
        GROUP BY b.BatchID, b.BatchName, b.Status, b.DateStarted
        ORDER BY b.DateStarted DESC
    """)

def get_sales_by_buyer():
    """Get sales breakdown by buyer"""
    return run_query("""
        SELECT 
            buyer.BuyerName,
            COUNT(*) as TransactionCount,
            COALESCE(SUM(s.QuantitySold), 0) as TotalBirds,
            COALESCE(SUM(s.TotalRevenue), 0) as TotalRevenue,
            ROUND(COALESCE(AVG(s.UnitPrice), 0), 2) as AvgPrice
        FROM DAILY_SALES s
        LEFT JOIN BUYERS buyer ON s.BuyerID = buyer.BuyerID
        GROUP BY buyer.BuyerName
        ORDER BY TotalRevenue DESC
    """)

def get_feed_analysis():
    """Get feed cost analysis"""
    return run_query("""
        SELECT 
            fd.FeedType,
            COUNT(*) as TimesUsed,
            ROUND(SUM(f.QuantityKG), 2) as TotalKG,
            ROUND(SUM(f.FeedCost), 2) as TotalCost,
            ROUND(AVG(f.FeedCost), 2) as AvgCostPerDay
        FROM DAILY_FEED_LOG f
        LEFT JOIN FEEDS fd ON f.FeedTypeID = fd.FeedID
        GROUP BY fd.FeedType
        ORDER BY TotalCost DESC
    """)

def get_mortality_analysis():
    """Get mortality rate analysis"""
    return run_query("""
        SELECT 
            b.BatchName,
            b.Status,
            COALESCE(SUM(m.QuantityDied), 0) as TotalDeaths,
            COALESCE(SUM(CASE WHEN m.Reason = 'Disease' THEN m.QuantityDied ELSE 0 END), 0) as DiseaseDeaths,
            COALESCE(SUM(CASE WHEN m.Reason = 'Accident' THEN m.QuantityDied ELSE 0 END), 0) as AccidentDeaths,
            COALESCE(SUM(CASE WHEN m.Reason = 'Starvation' THEN m.QuantityDied ELSE 0 END), 0) as StarvationDeaths
        FROM BATCHES_DETAILED b
        LEFT JOIN DAILY_MORTALITY m ON b.BatchID = m.BatchID
        GROUP BY b.BatchName, b.Status
        ORDER BY TotalDeaths DESC
    """)

def get_daily_stats():
    """Get stats for last 30 days"""
    return run_query("""
        SELECT 
            DATE(s.DateSold) as Date,
            COALESCE(SUM(s.TotalRevenue), 0) as DailyRevenue,
            COALESCE(SUM(s.QuantitySold), 0) as BirdsSold
        FROM DAILY_SALES s
        WHERE s.DateSold >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(s.DateSold)
        ORDER BY Date DESC
    """)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("🐔 KUKU Farm Dashboard")
st.markdown("Professional Farm Management System with Financial Analytics")

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")
    page = st.radio(
        "Select View",
        ["Overview", "Financial Reports", "Batch Analysis", "Buyer Analysis", "Feed Analysis", "Health Reports"]
    )
    
    st.divider()
    st.caption("Real-time data from Supabase")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M')}")

# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================

if page == "Overview":
    st.header("📈 Dashboard Overview")
    
    # Get data
    active = get_active_batches()
    completed = get_completed_batches()
    financial = get_financial_summary()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_count = active['count'].values[0] if len(active) > 0 else 0
        st.metric("🐣 Active Batches", int(active_count))
    
    with col2:
        completed_count = completed['count'].values[0] if len(completed) > 0 else 0
        st.metric("✅ Completed Batches", int(completed_count))
    
    with col3:
        revenue = financial['TotalRevenue'].values[0] if len(financial) > 0 else 0
        st.metric("💰 Total Revenue", f"TZS {int(revenue):,}")
    
    with col4:
        cost = financial['TotalFeedCost'].values[0] if len(financial) > 0 else 0
        st.metric("📦 Total Feed Cost", f"TZS {int(cost):,}")
    
    st.divider()
    
    # Financial summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if len(financial) > 0:
            profit = financial['TotalRevenue'].values[0] - financial['TotalFeedCost'].values[0]
            if profit > 0:
                st.success(f"**Profit: TZS {int(profit):,}**")
            else:
                st.warning(f"**Loss: TZS {int(abs(profit)):,}**")
        else:
            st.info("No data yet")
    
    with col2:
        if len(financial) > 0 and financial['TotalFeedCost'].values[0] > 0:
            profit_margin = ((financial['TotalRevenue'].values[0] - financial['TotalFeedCost'].values[0]) / financial['TotalRevenue'].values[0] * 100) if financial['TotalRevenue'].values[0] > 0 else 0
            st.info(f"**Profit Margin: {profit_margin:.1f}%**")
    
    with col3:
        st.info(f"**Date: {datetime.now().strftime('%Y-%m-%d')}**")
    
    st.divider()
    
    # Recent batches
    st.subheader("Recent Batches")
    batches = get_all_batches()
    if len(batches) > 0:
        st.dataframe(batches, use_container_width=True)
    else:
        st.info("No batches yet. Start by creating a batch in Worker Forms!")

# ============================================================================
# PAGE 2: FINANCIAL REPORTS
# ============================================================================

elif page == "Financial Reports":
    st.header("💵 Financial Reports")
    
    batch_data = get_batch_financial_details()
    
    if len(batch_data) > 0:
        st.subheader("Profit & Loss by Batch")
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = batch_data['Revenue'].sum()
            st.metric("Total Revenue", f"TZS {int(total_revenue):,}")
        
        with col2:
            total_cost = batch_data['FeedCost'].sum()
            st.metric("Total Feed Cost", f"TZS {int(total_cost):,}")
        
        with col3:
            total_profit = batch_data['Profit'].sum()
            if total_profit > 0:
                st.success(f"Total Profit: TZS {int(total_profit):,}")
            else:
                st.error(f"Total Loss: TZS {int(abs(total_profit)):,}")
        
        with col4:
            profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            st.metric("Profit Margin", f"{profit_margin:.1f}%")
        
        st.divider()
        
        # Detailed table
        st.subheader("Batch Financial Details")
        display_df = batch_data[['BatchName', 'Status', 'Revenue', 'FeedCost', 'Profit', 'BirdsSold', 'BirdsDied']].copy()
        display_df['Profit Margin %'] = (display_df['Profit'] / display_df['Revenue'] * 100).round(1)
        
        st.dataframe(display_df, use_container_width=True)
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenue vs Cost by Batch")
            chart_data = batch_data[['BatchName', 'Revenue', 'FeedCost']].set_index('BatchName')
            fig = go.Figure(data=[
                go.Bar(name='Revenue', x=chart_data.index, y=chart_data['Revenue'], marker_color='green'),
                go.Bar(name='Feed Cost', x=chart_data.index, y=chart_data['FeedCost'], marker_color='red')
            ])
            fig.update_layout(barmode='group', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Profit by Batch")
            colors = ['green' if x > 0 else 'red' for x in batch_data['Profit']]
            fig = px.bar(batch_data, x='BatchName', y='Profit', color=batch_data['Profit'],
                        color_continuous_scale='RdYlGn', title='Profit/Loss')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No financial data yet. Start entering sales data in Worker Forms!")

# ============================================================================
# PAGE 3: BATCH ANALYSIS
# ============================================================================

elif page == "Batch Analysis":
    st.header("🐔 Batch Analysis")
    
    batch_data = get_batch_financial_details()
    
    if len(batch_data) > 0:
        st.subheader("Batch Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Birds Sold vs Died")
            fig = px.scatter(batch_data, x='BirdsDied', y='BirdsSold', 
                            size='Profit', color='Status', hover_data=['BatchName'],
                            title='Birds Sold vs Mortality')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Feed Cost per Bird Sold")
            batch_data['CostPerBird'] = batch_data['FeedCost'] / (batch_data['BirdsSold'] + 1)
            fig = px.bar(batch_data, x='BatchName', y='CostPerBird', 
                        title='Feed Cost per Bird Sold')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Batch Details")
        st.dataframe(batch_data, use_container_width=True)
    
    else:
        st.info("No batch data yet")

# ============================================================================
# PAGE 4: BUYER ANALYSIS
# ============================================================================

elif page == "Buyer Analysis":
    st.header("🤝 Buyer Analysis")
    
    buyer_data = get_sales_by_buyer()
    
    if len(buyer_data) > 0:
        st.subheader("Sales by Buyer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenue by Buyer")
            fig = px.pie(buyer_data, values='TotalRevenue', names='BuyerName',
                        title='Revenue Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Birds Sold by Buyer")
            fig = px.bar(buyer_data, x='BuyerName', y='TotalBirds',
                        color='TotalRevenue', title='Birds Sold by Buyer')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Buyer Details")
        st.dataframe(buyer_data, use_container_width=True)
    
    else:
        st.info("No buyer data yet. Start recording sales in Worker Forms!")

# ============================================================================
# PAGE 5: FEED ANALYSIS
# ============================================================================

elif page == "Feed Analysis":
    st.header("📦 Feed Cost Analysis")
    
    feed_data = get_feed_analysis()
    
    if len(feed_data) > 0:
        st.subheader("Feed Usage and Cost")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Feed Cost Distribution")
            fig = px.pie(feed_data, values='TotalCost', names='FeedType',
                        title='Total Feed Cost by Type')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Feed Usage (kg)")
            fig = px.bar(feed_data, x='FeedType', y='TotalKG',
                        color='TotalCost', title='Total Feed Used by Type')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Feed Analysis Details")
        st.dataframe(feed_data, use_container_width=True)
    
    else:
        st.info("No feed data yet")

# ============================================================================
# PAGE 6: HEALTH REPORTS
# ============================================================================

elif page == "Health Reports":
    st.header("💔 Health & Mortality Reports")
    
    mortality_data = get_mortality_analysis()
    
    if len(mortality_data) > 0:
        st.subheader("Mortality Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Deaths by Cause")
            cause_data = mortality_data[['DiseaseDeaths', 'AccidentDeaths', 'StarvationDeaths']].sum()
            fig = px.pie(values=cause_data.values, names=['Disease', 'Accident', 'Starvation'],
                        title='Mortality by Cause')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Total Deaths by Batch")
            fig = px.bar(mortality_data, x='BatchName', y='TotalDeaths',
                        color='TotalDeaths', title='Mortality by Batch')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Mortality Details")
        st.dataframe(mortality_data, use_container_width=True)
    
    else:
        st.info("No mortality data yet")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("KUKU Project - Professional Farm Management System")
