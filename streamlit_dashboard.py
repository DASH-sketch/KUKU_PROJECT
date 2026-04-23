import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="KUKU PROJECT Dashboard",
    page_icon="chicken",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-high {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #d32f2f;
    }
    .alert-medium {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f57c00;
    }
    .alert-low {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #388e3c;
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
# HELPER FUNCTIONS
# ============================================================================

def fetch_active_batches():
    """Get last 5 active batches"""
    query = """
    SELECT BatchID, BatchName, DateStarted, QuantityChicksStarted, Status
    FROM BATCHES_DETAILED
    WHERE Status IN ('Active', 'Selling')
    ORDER BY DateStarted DESC
    LIMIT 5
    """
    df = pd.read_sql_query(query, conn)
    if len(df) > 0:
        df['DateStarted'] = pd.to_datetime(df['DateStarted']).dt.date
    return df

def fetch_batch_metrics(batch_id):
    """Get metrics for a specific batch"""
    query = """
    SELECT * FROM BATCH_METRICS WHERE BatchID = ?
    """
    df = pd.read_sql_query(query, conn, params=(batch_id,))
    return df.iloc[0] if len(df) > 0 else None

def fetch_weight_data(batch_id):
    """Get weight progression for a batch"""
    query = """
    SELECT Week, AverageWeightPerBird, DateMeasured
    FROM WEIGHT_TRACKING
    WHERE BatchID = ?
    ORDER BY Week ASC
    """
    df = pd.read_sql_query(query, conn, params=(batch_id,))
    return df

def fetch_last_8_completed_batches():
    """Get last 8 completed batches for comparison chart"""
    query = """
    SELECT bm.BatchID, bd.BatchName, bm.TotalRevenue, bm.TotalCosts, bm.ProfitLoss
    FROM BATCH_METRICS bm
    JOIN BATCHES_DETAILED bd ON bm.BatchID = bd.BatchID
    WHERE bd.Status = 'Completed'
    ORDER BY bm.DateCalculated DESC
    LIMIT 8
    """
    df = pd.read_sql_query(query, conn)
    return df.sort_values('BatchID') if len(df) > 0 else df

def calculate_demand_health(batch_id):
    """Calculate demand health score and stalling detection"""
    query = """
    SELECT DATE(DateSold) as Date, SUM(QuantitySold) as DailySold
    FROM DAILY_SALES
    WHERE BatchID = ?
    GROUP BY DATE(DateSold)
    ORDER BY Date DESC
    LIMIT 14
    """
    df = pd.read_sql_query(query, conn, params=(batch_id,))
    
    if len(df) < 7:
        return 7, False, 0
    
    this_week = df.iloc[:7]['DailySold'].sum()
    last_week = df.iloc[7:14]['DailySold'].sum() if len(df) >= 14 else this_week
    
    if last_week == 0:
        change = 0
    else:
        change = ((this_week - last_week) / last_week) * 100
    
    is_stalling = (this_week < last_week * 0.7) if last_week > 0 else False
    
    score = 5
    if change > 20:
        score += 3
    elif change > 0:
        score += 1
    elif change < -30:
        score -= 4
    elif change < 0:
        score -= 1
    
    score = max(1, min(10, score))
    
    return score, is_stalling, change

def get_ai_insights(batch_id):
    """Generate AI insights for batch"""
    metrics = fetch_batch_metrics(batch_id)
    
    insights = []
    
    if metrics:
        if metrics['FCR'] < 1.9:
            insights.append({
                'type': 'positive',
                'text': f"Excellent FCR: {metrics['FCR']:.2f} - Feed efficiency is outstanding!"
            })
        elif metrics['FCR'] > 2.1:
            insights.append({
                'type': 'warning',
                'text': f"Poor FCR: {metrics['FCR']:.2f} - Check feed quality or bird health"
            })
        
        if metrics['MortalityRate'] > 8:
            insights.append({
                'type': 'alert',
                'text': f"High mortality: {metrics['MortalityRate']:.1f}% - Investigate health issues"
            })
        
        if metrics['ProfitMargin'] > 40:
            insights.append({
                'type': 'positive',
                'text': f"Strong profit margin: {metrics['ProfitMargin']:.0f}% - Great performance!"
            })
        
        if metrics['CostPerBird'] < 3500:
            insights.append({
                'type': 'positive',
                'text': f"Low cost per bird: {metrics['CostPerBird']:,.0f} TZS - Efficient operations"
            })
    
    return insights

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("KUKU PROJECT DASHBOARD")
st.markdown("Real-time farm management and analytics")

# Sidebar
with st.sidebar:
    st.header("Dashboard Controls")
    view_mode = st.radio("Select View:", ["Overview", "Batch Details", "Financial Analysis", "Reports"])
    
    st.divider()
    st.markdown("**Last Updated:** " + datetime.now().strftime("%Y-%m-%d %H:%M"))

# ============================================================================
# VIEW 1: OVERVIEW
# ============================================================================

if view_mode == "Overview":
    
    active_batches = fetch_active_batches()
    
    if len(active_batches) == 0:
        st.warning("No active batches found. Start a new batch to begin!")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Active Batches",
                value=len(active_batches),
                delta="Total units running"
            )
        
        with col2:
            total_chicks = active_batches['QuantityChicksStarted'].sum()
            st.metric(
                label="Total Chicks",
                value=f"{total_chicks:,}",
                delta="Units in system"
            )
        
        with col3:
            query = "SELECT SUM(TotalRevenue) as Revenue FROM DAILY_SALES WHERE DateSold >= DATE('now', '-7 days')"
            result = pd.read_sql_query(query, conn)
            revenue_7d = result.iloc[0]['Revenue'] if len(result) > 0 and result.iloc[0]['Revenue'] is not None else 0
            st.metric(
                label="Weekly Revenue",
                value=f"{revenue_7d:,.0f} TZS",
                delta="Last 7 days"
            )
        
        with col4:
            query = "SELECT SUM(ProfitLoss) as Profit FROM BATCH_METRICS WHERE BatchID IN (SELECT BatchID FROM BATCHES_DETAILED WHERE Status IN ('Active', 'Selling'))"
            result = pd.read_sql_query(query, conn)
            profit = result.iloc[0]['Profit'] if len(result) > 0 and result.iloc[0]['Profit'] is not None else 0
            st.metric(
                label="Running Profit",
                value=f"{profit:,.0f} TZS",
                delta="All active batches"
            )
        
        st.divider()
        
        st.subheader("ALERTS AND WARNINGS")
        
        has_alerts = False
        for idx, batch in active_batches.iterrows():
            metrics = fetch_batch_metrics(batch['BatchID'])
            score, is_stalling, change = calculate_demand_health(batch['BatchID'])
            
            if is_stalling:
                st.markdown(f"""
                <div class="alert-high">
                    <strong>DEMAND STALLING DETECTED</strong><br>
                    {batch['BatchName']}: Sales down {abs(change):.0f}% from last week<br>
                    Action: Review pricing, check competitors, contact buyers
                </div>
                """, unsafe_allow_html=True)
                has_alerts = True
            
            if metrics and metrics['MortalityRate'] > 8:
                st.markdown(f"""
                <div class="alert-high">
                    <strong>HIGH MORTALITY</strong><br>
                    {batch['BatchName']}: {metrics['MortalityRate']:.1f}%<br>
                    Action: Check water quality, temperature, ventilation
                </div>
                """, unsafe_allow_html=True)
                has_alerts = True
            
            if metrics and metrics['FCR'] > 2.1:
                st.markdown(f"""
                <div class="alert-medium">
                    <strong>FCR TRENDING UP</strong><br>
                    {batch['BatchName']}: {metrics['FCR']:.2f}<br>
                    Action: Monitor feed quality and bird health
                </div>
                """, unsafe_allow_html=True)
                has_alerts = True
        
        if not has_alerts:
            st.markdown("""
            <div class="alert-low">
                All Batches Healthy - No issues detected
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        st.subheader("ACTIVE BATCHES STATUS")
        
        for idx, batch in active_batches.iterrows():
            col1, col2, col3, col4, col5 = st.columns(5)
            metrics = fetch_batch_metrics(batch['BatchID'])
            score, is_stalling, change = calculate_demand_health(batch['BatchID'])
            
            with col1:
                st.metric(
                    label=f"{batch['BatchName']}",
                    value=batch['Status'],
                    delta=f"{(datetime.now().date() - batch['DateStarted']).days} days old"
                )
            
            with col2:
                if metrics:
                    st.metric(
                        label="FCR",
                        value=f"{metrics['FCR']:.2f}",
                        delta="Target: 1.95"
                    )
            
            with col3:
                if metrics:
                    st.metric(
                        label="Mortality",
                        value=f"{metrics['MortalityRate']:.1f}%",
                        delta="Target: <5%"
                    )
            
            with col4:
                if metrics:
                    st.metric(
                        label="Avg Weight",
                        value=f"{metrics.get('AvgWeight', 0):.2f} kg",
                        delta="Growth tracking"
                    )
            
            with col5:
                st.metric(
                    label="Demand",
                    value=f"{score}/10",
                    delta=f"{change:+.0f}% vs last week"
                )

# ============================================================================
# VIEW 2: BATCH DETAILS
# ============================================================================

elif view_mode == "Batch Details":
    
    active_batches = fetch_active_batches()
    
    if len(active_batches) == 0:
        st.warning("No active batches found")
    else:
        selected_batch = st.selectbox(
            "Select Batch:",
            options=active_batches['BatchName'].tolist(),
            index=0
        )
        
        batch_data = active_batches[active_batches['BatchName'] == selected_batch].iloc[0]
        batch_id = batch_data['BatchID']
        metrics = fetch_batch_metrics(batch_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Batch Name", batch_data['BatchName'])
            st.metric("Started", str(batch_data['DateStarted']))
            st.metric("Status", batch_data['Status'])
        
        with col2:
            if metrics:
                st.metric("Profit", f"{metrics['ProfitLoss']:,.0f} TZS")
                st.metric("Profit Margin", f"{metrics['ProfitMargin']:.0f}%")
                st.metric("Cost/Bird", f"{metrics['CostPerBird']:,.0f} TZS")
        
        with col3:
            if metrics:
                st.metric("Revenue", f"{metrics['TotalRevenue']:,.0f} TZS")
                st.metric("Total Costs", f"{metrics['TotalCosts']:,.0f} TZS")
                st.metric("Profit/Bird", f"{metrics['ProfitPerBird']:,.0f} TZS")
        
        st.divider()
        
        st.subheader("Weight Progression by Week")
        
        weight_data = fetch_weight_data(batch_id)
        
        if len(weight_data) > 0:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=weight_data['Week'],
                y=weight_data['AverageWeightPerBird'],
                mode='lines+markers',
                name='Average Weight',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=12)
            ))
            
            weeks = [1, 2, 3, 4]
            targets = [0.35, 0.78, 1.32, 1.70]
            
            fig.add_trace(go.Scatter(
                x=weeks,
                y=targets,
                mode='lines',
                name='Target Weight',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title=f"Weight Progression - {selected_batch}",
                xaxis_title="Week of Cycle",
                yaxis_title="Average Weight per Bird (kg)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            if len(weight_data) > 0:
                latest = weight_data.iloc[-1]
                st.markdown(f"""
                **Latest Measurement (Week {int(latest['Week'])}):**
                - Average Weight: {latest['AverageWeightPerBird']:.2f} kg per bird
                - Measured on: {latest['DateMeasured']}
                """)
        else:
            st.info("No weight measurements yet. Add weekly weight checks!")
        
        st.divider()
        
        st.subheader("AI Analysis and Insights")
        
        insights = get_ai_insights(batch_id)
        
        if insights:
            for insight in insights:
                if insight['type'] == 'positive':
                    st.success(f"[POSITIVE] {insight['text']}")
                elif insight['type'] == 'warning':
                    st.warning(f"[WARNING] {insight['text']}")
                else:
                    st.error(f"[ALERT] {insight['text']}")
        else:
            st.info("More data needed for detailed insights")

# ============================================================================
# VIEW 3: FINANCIAL ANALYSIS
# ============================================================================

elif view_mode == "Financial Analysis":
    
    st.subheader("Batch Financial Comparison (Last 8 Completed Batches)")
    
    batch_comparison = fetch_last_8_completed_batches()
    
    if len(batch_comparison) > 0:
        fig = go.Figure(data=[
            go.Bar(
                x=batch_comparison['BatchName'],
                y=batch_comparison['TotalRevenue'],
                name='Revenue',
                marker_color='#2ecc71'
            ),
            go.Bar(
                x=batch_comparison['BatchName'],
                y=batch_comparison['TotalCosts'],
                name='Costs',
                marker_color='#e74c3c'
            ),
            go.Bar(
                x=batch_comparison['BatchName'],
                y=batch_comparison['ProfitLoss'],
                name='Profit',
                marker_color='#f39c12'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            title='Batch Financial Comparison (Revenue | Costs | Profit)',
            xaxis_title='Batch',
            yaxis_title='Amount (TZS)',
            hovermode='x unified',
            height=500,
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader("Detailed Financial Summary")
        
        summary_df = batch_comparison.copy()
        summary_df['Profit Margin %'] = (summary_df['ProfitLoss'] / summary_df['TotalRevenue'] * 100).round(1)
        
        display_df = summary_df[['BatchName', 'TotalRevenue', 'TotalCosts', 'ProfitLoss', 'Profit Margin %']].copy()
        display_df.columns = ['Batch', 'Revenue (TZS)', 'Costs (TZS)', 'Profit (TZS)', 'Margin (%)']
        
        st.dataframe(
            display_df.style.format({
                'Revenue (TZS)': '{:,.0f}',
                'Costs (TZS)': '{:,.0f}',
                'Profit (TZS)': '{:,.0f}',
                'Margin (%)': '{:.1f}'
            }),
            use_container_width=True
        )
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            best_profit_idx = batch_comparison['ProfitLoss'].idxmax()
            best_profit_batch = batch_comparison.loc[best_profit_idx, 'BatchName']
            best_profit_amt = batch_comparison.loc[best_profit_idx, 'ProfitLoss']
            st.metric("Best Profit Batch", best_profit_batch, f"{best_profit_amt:,.0f} TZS")
        
        with col2:
            best_margin_idx = (batch_comparison['ProfitLoss'] / batch_comparison['TotalRevenue']).idxmax()
            best_margin_batch = batch_comparison.loc[best_margin_idx, 'BatchName']
            best_margin_pct = (batch_comparison.loc[best_margin_idx, 'ProfitLoss'] / batch_comparison.loc[best_margin_idx, 'TotalRevenue'] * 100)
            st.metric("Best Margin Batch", best_margin_batch, f"{best_margin_pct:.0f}%")
        
        with col3:
            avg_profit = batch_comparison['ProfitLoss'].mean()
            avg_margin = (batch_comparison['ProfitLoss'] / batch_comparison['TotalRevenue'] * 100).mean()
            st.metric("Average Margin", f"{avg_margin:.0f}%", f"Avg profit: {avg_profit:,.0f}")
    else:
        st.info("No completed batches yet to display comparison")

# ============================================================================
# VIEW 4: REPORTS AND EXPORT
# ============================================================================

else:
    
    st.subheader("Generate Reports")
    
    report_type = st.selectbox(
        "Select Report Type:",
        ["Loan Application Statement", "Batch Performance Report", "Monthly Summary", "Buyer Analysis"]
    )
    
    if report_type == "Loan Application Statement":
        st.markdown("""
        ### Loan Application Financial Statement
        
        This report shows:
        - Last 3 months of batch profitability
        - Profit margins and ROI
        - Cash flow analysis
        - Repayment capacity
        
        Perfect for: Bank loan applications, investor presentations
        
        """)
        
        if st.button("Generate Loan Report"):
            query = """
            SELECT BatchName, TotalRevenue, TotalCosts, ProfitLoss,
                   ProfitLoss / TotalRevenue * 100 as Margin,
                   DateCalculated
            FROM BATCH_METRICS
            ORDER BY DateCalculated DESC
            LIMIT 3
            """
            
            df = pd.read_sql_query(query, conn)
            
            if len(df) == 0:
                st.warning("No batch data available yet. Complete at least one batch to generate reports.")
            else:
                st.write("### KUKU PROJECT - Financial Statement for Loan Application")
                st.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}")
                st.dataframe(df)
                
                total_revenue = df['TotalRevenue'].sum()
                total_costs = df['TotalCosts'].sum()
                total_profit = df['ProfitLoss'].sum()
                avg_margin = df['Margin'].mean()
                
                st.markdown(f"""
                #### Financial Summary (Last 3 Batches)
                - **Total Revenue:** {total_revenue:,.0f} TZS
                - **Total Costs:** {total_costs:,.0f} TZS
                - **Total Profit:** {total_profit:,.0f} TZS
                - **Average Margin:** {avg_margin:.1f}%
                - **Repayment Capacity:** {total_profit/3:,.0f} TZS per month
                """)
                
                st.info("Ready to submit to bank. Demonstrates strong profitability and repayment ability.")
    
    elif report_type == "Batch Performance Report":
        st.markdown("Compare how your batches performed. Identify best practices!")
        st.info("Select batch and view detailed performance analysis")
    
    elif report_type == "Monthly Summary":
        st.markdown("See your monthly revenue, costs, and profit trends")
        st.info("Coming soon - Monthly aggregated data")
    
    else:
        st.markdown("Analyze your top buyers and their purchase patterns")
        st.info("Coming soon - Buyer frequency and volume analysis")
        
        query = """
        SELECT BuyerName, COUNT(*) as Transactions, SUM(QuantitySold) as TotalBought,
               AVG(UnitPrice) as AvgPrice
        FROM DAILY_SALES
        JOIN BUYERS ON DAILY_SALES.BuyerID = BUYERS.BuyerID
        GROUP BY BuyerName
        ORDER BY TotalBought DESC
        LIMIT 10
        """
        
        try:
            df = pd.read_sql_query(query, conn)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No sales data yet")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
---
KUKU PROJECT Dashboard | Version 1.0 | Last updated: 2026-03-20

Support: Contact farm manager
Data syncs every 5 minutes from Google Forms
Secure access with role-based permissions
""")
