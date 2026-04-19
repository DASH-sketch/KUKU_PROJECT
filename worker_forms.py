#!/usr/bin/env python3
"""
KUKU PROJECT - Simplified Worker Forms
Creates database tables automatically on first run
No pre-existing data required
"""

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os

st.set_page_config(
    page_title="KUKU Worker Forms",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .success-message {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database_connection():
    """Connect to Supabase PostgreSQL"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            st.error("❌ DATABASE_URL secret not configured!")
            st.stop()
        
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)[:100]}")
        st.info("Make sure DATABASE_URL is configured in Streamlit Secrets!")
        st.stop()

conn = get_database_connection()

def create_tables():
    """Create all necessary tables on first run"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BATCHES_DETAILED (
                BatchID SERIAL PRIMARY KEY,
                BatchName VARCHAR(50) NOT NULL UNIQUE,
                DateStarted DATE NOT NULL,
                DateEnded DATE,
                QuantityChicksStarted INTEGER NOT NULL,
                CurrentQuantity INTEGER,
                Status VARCHAR(20) NOT NULL,
                AssignedWorker VARCHAR(100),
                Notes TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS FEEDS (
                FeedID SERIAL PRIMARY KEY,
                FeedType VARCHAR(50) NOT NULL UNIQUE,
                UnitPrice DECIMAL(10,2) NOT NULL,
                LastUpdated DATE DEFAULT CURRENT_DATE,
                Notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BUYERS (
                BuyerID SERIAL PRIMARY KEY,
                BuyerName VARCHAR(100) NOT NULL UNIQUE,
                Location VARCHAR(100),
                PhoneNumber VARCHAR(20),
                Status VARCHAR(20) DEFAULT 'Active',
                DateAdded DATE DEFAULT CURRENT_DATE,
                Notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DAILY_FEED_LOG (
                FeedLogID SERIAL PRIMARY KEY,
                BatchID INTEGER NOT NULL REFERENCES BATCHES_DETAILED(BatchID),
                DateFed DATE NOT NULL,
                FeedTypeID INTEGER NOT NULL REFERENCES FEEDS(FeedID),
                QuantityKG DECIMAL(10,2) NOT NULL,
                FeedCost DECIMAL(12,2),
                Notes TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DAILY_MORTALITY (
                MortalityID SERIAL PRIMARY KEY,
                BatchID INTEGER NOT NULL REFERENCES BATCHES_DETAILED(BatchID),
                DateRecorded DATE NOT NULL,
                QuantityDied INTEGER NOT NULL,
                Reason VARCHAR(100),
                AgeAtDeath INTEGER,
                Notes TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WEIGHT_TRACKING (
                WeightID SERIAL PRIMARY KEY,
                BatchID INTEGER NOT NULL REFERENCES BATCHES_DETAILED(BatchID),
                DateMeasured DATE NOT NULL,
                Week INTEGER NOT NULL,
                AverageWeightPerBird DECIMAL(6,3) NOT NULL,
                SampleSize INTEGER NOT NULL,
                DaysOld INTEGER,
                Notes TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(BatchID, Week)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DAILY_SALES (
                SaleID SERIAL PRIMARY KEY,
                BatchID INTEGER NOT NULL REFERENCES BATCHES_DETAILED(BatchID),
                DateSold DATE NOT NULL,
                QuantitySold INTEGER NOT NULL,
                BuyerID INTEGER NOT NULL REFERENCES BUYERS(BuyerID),
                UnitPrice DECIMAL(10,2) NOT NULL,
                TotalRevenue DECIMAL(12,2),
                SaleStatus VARCHAR(20),
                Notes TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MARKET_FEEDBACK (
                FeedbackID SERIAL PRIMARY KEY,
                DateFeedback DATE NOT NULL,
                BuyerID INTEGER NOT NULL REFERENCES BUYERS(BuyerID),
                DemandLevel VARCHAR(20),
                PriceResistance VARCHAR(10),
                CompetitorActivity VARCHAR(100),
                Sentiment VARCHAR(20),
                Comments TEXT,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()

create_tables()

def get_active_batches():
    """Get all batches"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT BatchID, BatchName FROM BATCHES_DETAILED ORDER BY BatchID DESC LIMIT 10")
        batches = cursor.fetchall()
        
        if not batches:
            cursor.execute("""
                INSERT INTO BATCHES_DETAILED (BatchName, DateStarted, QuantityChicksStarted, Status)
                VALUES ('Batch 1', CURRENT_DATE, 500, 'Active')
                RETURNING BatchID, BatchName
            """)
            conn.commit()
            batches = cursor.fetchall()
        
        return [b[1] for b in batches]
    except:
        return ["Batch 1"]

def get_feed_types():
    """Get feed types"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT FeedType FROM FEEDS ORDER BY FeedType")
        types = cursor.fetchall()
        
        if not types:
            for name, price in [("Starter", 750), ("Grower", 600), ("Finisher", 650)]:
                cursor.execute("INSERT INTO FEEDS (FeedType, UnitPrice) VALUES (%s, %s)", (name, price))
            conn.commit()
            types = [("Starter",), ("Grower",), ("Finisher",)]
        
        return [t[0] for t in types]
    except:
        return ["Starter", "Grower", "Finisher"]

def get_buyers():
    """Get buyers"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT BuyerName FROM BUYERS ORDER BY BuyerName LIMIT 10")
        buyers = cursor.fetchall()
        
        if not buyers:
            for name in ["Sadiki", "Issa Center", "Mama Zai"]:
                cursor.execute("INSERT INTO BUYERS (BuyerName) VALUES (%s)", (name,))
            conn.commit()
            buyers = [(n,) for n in ["Sadiki", "Issa Center", "Mama Zai"]]
        
        return [b[0] for b in buyers]
    except:
        return ["Sadiki", "Issa Center", "Mama Zai"]

def get_batch_id(batch_name):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT BatchID FROM BATCHES_DETAILED WHERE BatchName = %s", (batch_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None

def get_feed_id(feed_type):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT FeedID, UnitPrice FROM FEEDS WHERE FeedType = %s", (feed_type,))
        result = cursor.fetchone()
        return result if result else None
    except:
        return None

def get_buyer_id(buyer_name):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT BuyerID FROM BUYERS WHERE BuyerName = %s", (buyer_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("INSERT INTO BUYERS (BuyerName) VALUES (%s) RETURNING BuyerID", (buyer_name,))
        conn.commit()
        return cursor.fetchone()[0]
    except:
        return None

st.title("🐔 KUKU Worker Forms")
st.markdown("Enter data from the farm")

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

st.divider()

if 'form' not in st.session_state:
    st.session_state.form = None

if st.session_state.form == "feed":
    st.header("📦 Daily Feed Log")
    with st.form("feed_form"):
        batch = st.selectbox("Which batch?", get_active_batches())
        date = st.date_input("Date", datetime.now())
        feed_type = st.selectbox("Feed type", get_feed_types())
        qty = st.number_input("Quantity (kg)", min_value=0.0, step=0.5)
        notes = st.text_area("Notes")
        if st.form_submit_button("Submit", use_container_width=True):
            try:
                cursor = conn.cursor()
                batch_id = get_batch_id(batch)
                feed_result = get_feed_id(feed_type)
                if batch_id and feed_result:
                    feed_id, price = feed_result
                    cursor.execute("INSERT INTO DAILY_FEED_LOG (BatchID, DateFed, FeedTypeID, QuantityKG, FeedCost, Notes) VALUES (%s,%s,%s,%s,%s,%s)", 
                                 (batch_id, date, feed_id, qty, qty*price, notes))
                    conn.commit()
                    st.success("✅ Feed log recorded!")
                    st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")

elif st.session_state.form == "mortality":
    st.header("💔 Daily Mortality Report")
    with st.form("mort_form"):
        batch = st.selectbox("Which batch?", get_active_batches())
        date = st.date_input("Date", datetime.now())
        qty = st.number_input("How many died?", min_value=0)
        reason = st.selectbox("Reason", ["Disease", "Accident", "Starvation", "Unknown"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Submit", use_container_width=True):
            try:
                cursor = conn.cursor()
                batch_id = get_batch_id(batch)
                if batch_id:
                    cursor.execute("INSERT INTO DAILY_MORTALITY (BatchID, DateRecorded, QuantityDied, Reason, Notes) VALUES (%s,%s,%s,%s,%s)", 
                                 (batch_id, date, qty, reason, notes))
                    conn.commit()
                    st.success("✅ Mortality report recorded!")
                    st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")

elif st.session_state.form == "sales":
    st.header("💰 Daily Sales Log")
    with st.form("sales_form"):
        batch = st.selectbox("Which batch?", get_active_batches())
        date = st.date_input("Sale date", datetime.now())
        qty = st.number_input("How many sold?", min_value=0)
        buyer = st.selectbox("Buyer", get_buyers())
        price = st.number_input("Price per bird (TZS)", min_value=0.0, step=100.0)
        status = st.selectbox("Status", ["Sold & Paid", "Sold on Credit"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Submit", use_container_width=True):
            try:
                cursor = conn.cursor()
                batch_id = get_batch_id(batch)
                buyer_id = get_buyer_id(buyer)
                if batch_id and buyer_id:
                    cursor.execute("INSERT INTO DAILY_SALES (BatchID, DateSold, QuantitySold, BuyerID, UnitPrice, TotalRevenue, SaleStatus, Notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", 
                                 (batch_id, date, qty, buyer_id, price, qty*price, status, notes))
                    conn.commit()
                    st.success("✅ Sale recorded!")
                    st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")

elif st.session_state.form == "weight":
    st.header("⚖️ Weekly Weight Check")
    with st.form("weight_form"):
        batch = st.selectbox("Which batch?", get_active_batches())
        date = st.date_input("Date", datetime.now())
        week = st.selectbox("Week", ["Week 1", "Week 2", "Week 3", "Week 4+"])
        total_weight = st.number_input("Total weight of 10 birds (kg)", min_value=0.0, step=0.1)
        notes = st.text_area("Notes")
        if st.form_submit_button("Submit", use_container_width=True):
            try:
                cursor = conn.cursor()
                batch_id = get_batch_id(batch)
                week_num = int(week.split()[1])
                if batch_id:
                    cursor.execute("INSERT INTO WEIGHT_TRACKING (BatchID, DateMeasured, Week, AverageWeightPerBird, SampleSize, Notes) VALUES (%s,%s,%s,%s,%s,%s)", 
                                 (batch_id, date, week_num, total_weight/10, 10, notes))
                    conn.commit()
                    st.success("✅ Weight check recorded!")
                    st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")

else:
    st.info("Click a button to start!")

st.divider()
st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
