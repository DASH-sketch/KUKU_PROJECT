#!/usr/bin/env python3
"""
KUKU PROJECT - Complete Financial Dashboard
Shows real financial data with analysis
"""

import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(
    page_title="KUKU Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 KUKU Farm - Financial Dashboard")
st.markdown("Real-time farm management and financial analysis")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(os.getenv("DATABASE_URL"))
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")
        return None

def query_db(sql, conn):
    """Execute query safely"""
    try:
        return pd.read_sql(sql, conn)
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

conn = get_connection()

if conn is None:
    st.error("❌ Cannot connect to database")
    st.stop()

# ============================================================================
# SECTION 1: KEY METRICS
# ============================================================================

st.header("💰 Financial Summary")

col1, col2, col3, col4, col5 = st.columns(5)

try:
    # Total Revenue
    revenue_df = query_db("SELECT COALESCE(SUM(TotalRevenue), 0) as revenue FROM DAILY_SALES", conn)
    total_revenue = revenue_df['revenue'].values[0] if len(revenue_df) > 0 else 0
    
    # Total Expenses
    expense_df = query_db("SELECT COALESCE(SUM(Amount), 0) as expenses FROM EXPENSES", conn)
    total_expenses = expense_df['expenses'].values[0] if len(expense_df) > 0 else 0
    
    # Net Profit
    net_profit = total_revenue - total_expenses
    profit_percent = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Total Birds Sold
    birds_df = query_db("SELECT COALESCE(SUM(QuantitySold), 0) as birds FROM DAILY_SALES", conn)
    birds_sold = int(birds_df['birds'].values[0]) if len(birds_df) > 0 else 0
    
    # Number of Sales
    sales_count_df = query_db("SELECT COUNT(*) as count FROM DAILY_SALES", conn)
    sales_count = int(sales_count_df['count'].values[0]) if len(sales_count_df) > 0 else 0
    
    with col1:
        st.metric("💵 Total Revenue", f"TZS {total_revenue:,.0f}")
    
    with col2:
        st.metric("💸 Total Expenses", f"TZS {total_expenses:,.0f}")
    
    with col3:
        color = "🟢" if net_profit > 0 else "🔴"
        st.metric(f"{color} Net Profit", f"TZS {net_profit:,.0f}", f"{profit_percent:.1f}%")
    
    with col4:
        st.metric("🐔 Birds Sold", f"{birds_sold:,}")
    
    with col5:
        st.metric("📦 Sales", f"{sales_count}")

except Exception as e:
    st.error(f"Error loading metrics: {e}")

st.divider()

# ============================================================================
# SECTION 2: CHARTS
# ============================================================================

st.header("📈 Analysis")

col1, col2 = st.columns(2)

# Revenue Trend
with col1:
    st.subheader("Sales Trend")
    try:
        sales_trend = query_db("""
            SELECT DATE(DateSold) as date, COUNT(*) as count, SUM(TotalRevenue) as revenue
            FROM DAILY_SALES
            GROUP BY DATE(DateSold)
            ORDER BY date DESC
            LIMIT 30
        """, conn)
        
        if len(sales_trend) > 0:
            sales_trend = sales_trend.sort_values('date')
            fig = px.line(sales_trend, x='date', y='revenue', title='Daily Revenue Trend')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data")
    except Exception as e:
        st.error(f"Chart error: {e}")

# Expense Breakdown
with col2:
    st.subheader("Expenses by Category")
    try:
        expense_cat = query_db("""
            SELECT Category, SUM(Amount) as total
            FROM EXPENSES
            GROUP BY Category
            ORDER BY total DESC
        """, conn)
        
        if len(expense_cat) > 0:
            fig = px.pie(expense_cat, values='total', names='Category', title='Expense Breakdown')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data")
    except Exception as e:
        st.error(f"Chart error: {e}")

st.divider()

# ============================================================================
# SECTION 3: DETAILED TABLES
# ============================================================================

st.header("📋 Recent Transactions")

col1, col2 = st.columns(2)

# Recent Sales
with col1:
    st.subheader("Recent Sales (Last 10)")
    try:
        recent_sales = query_db("""
            SELECT 
                DateSold,
                QuantitySold,
                UnitPrice,
                TotalRevenue
            FROM DAILY_SALES
            ORDER BY DateSold DESC
            LIMIT 10
        """, conn)
        
        if len(recent_sales) > 0:
            recent_sales['TotalRevenue'] = recent_sales['TotalRevenue'].apply(lambda x: f"TZS {x:,.0f}")
            recent_sales['UnitPrice'] = recent_sales['UnitPrice'].apply(lambda x: f"TZS {x:,.0f}")
            st.dataframe(recent_sales, use_container_width=True, hide_index=True)
        else:
            st.info("No sales yet")
    except Exception as e:
        st.error(f"Error: {e}")

# Recent Expenses
with col2:
    st.subheader("Recent Expenses (Last 10)")
    try:
        recent_exp = query_db("""
            SELECT 
                ExpenseDate,
                Category,
                Description,
                Amount
            FROM EXPENSES
            ORDER BY ExpenseDate DESC
            LIMIT 10
        """, conn)
        
        if len(recent_exp) > 0:
            recent_exp['Amount'] = recent_exp['Amount'].apply(lambda x: f"TZS {x:,.0f}")
            st.dataframe(recent_exp, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses yet")
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()

# ============================================================================
# SECTION 4: DETAILED BREAKDOWN
# ============================================================================

st.header("💹 Expense Details by Category")

try:
    exp_summary = query_db("""
        SELECT 
            Category,
            COUNT(*) as Count,
            SUM(Amount) as Total,
            AVG(Amount) as Average
        FROM EXPENSES
        GROUP BY Category
        ORDER BY Total DESC
    """, conn)
    
    if len(exp_summary) > 0:
        exp_summary['Total'] = exp_summary['Total'].apply(lambda x: f"TZS {x:,.0f}")
        exp_summary['Average'] = exp_summary['Average'].apply(lambda x: f"TZS {x:,.0f}")
        st.dataframe(exp_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No expense data")
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# ============================================================================
# SECTION 5: BATCHES
# ============================================================================

st.header("🐣 Batch Information")

try:
    batches = query_db("""
        SELECT 
            BatchID,
            BatchName,
            DateStarted,
            DateEnded,
            QuantityChicksStarted,
            Status
        FROM BATCHES_DETAILED
        ORDER BY DateStarted DESC
    """, conn)
    
    if len(batches) > 0:
        st.dataframe(batches, use_container_width=True, hide_index=True)
    else:
        st.info("No batch data")
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# ============================================================================
# SECTION 6: SUMMARY STATS
# ============================================================================

st.header("📊 Summary Statistics")

col1, col2, col3 = st.columns(3)

try:
    # Average sale value
    avg_sale = query_db("SELECT AVG(TotalRevenue) as avg FROM DAILY_SALES", conn)
    avg_sale_val = avg_sale['avg'].values[0] if len(avg_sale) > 0 else 0
    
    # Average birds per sale
    avg_birds = query_db("SELECT AVG(QuantitySold) as avg FROM DAILY_SALES", conn)
    avg_birds_val = avg_birds['avg'].values[0] if len(avg_birds) > 0 else 0
    
    # Average expense
    avg_exp = query_db("SELECT AVG(Amount) as avg FROM EXPENSES", conn)
    avg_exp_val = avg_exp['avg'].values[0] if len(avg_exp) > 0 else 0
    
    with col1:
        st.metric("📈 Average Sale", f"TZS {avg_sale_val:,.0f}")
    
    with col2:
        st.metric("🐓 Avg Birds/Sale", f"{avg_birds_val:.0f}")
    
    with col3:
        st.metric("📉 Average Expense", f"TZS {avg_exp_val:,.0f}")
        
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# Footer
st.caption(f"KUKU Farm Management System | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
