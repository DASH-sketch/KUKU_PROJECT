#!/usr/bin/env python3
"""
KUKU PROJECT - Streamlit Migration Interface
Upload Access data files and migrate to Supabase with one click
"""

import streamlit as st
import psycopg2
from datetime import datetime
from io import StringIO
import re
import os

st.set_page_config(
    page_title="KUKU Data Migration",
    page_icon="📤",
    layout="wide"
)

st.title("📤 KUKU Data Migration")
st.markdown("Migrate your historical data from Access to Supabase")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)[:100]}")
        return None

# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_text_table(text_content):
    """Parse Access export text table format"""
    rows = []
    lines = text_content.split('\n')
    
    # Skip header lines
    data_lines = []
    for line in lines:
        if line.strip().startswith('|') and '---' not in line:
            data_lines.append(line)
    
    if not data_lines:
        return [], []
    
    # First line has headers
    header_line = data_lines[0]
    headers = [h.strip() for h in header_line.split('|')[1:-1]]
    
    # Parse data rows
    for line in data_lines[1:]:
        if '---' in line:
            continue
        
        values = [v.strip() for v in line.split('|')[1:-1]]
        if len(values) == len(headers):
            row = dict(zip(headers, values))
            rows.append(row)
    
    return headers, rows

def parse_date(date_str):
    """Parse date from dd-MMM-yy format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d-%b-%y').date()
    except:
        return None

def extract_quantity_from_remarks(remark):
    """Extract batch starting quantity from remarks"""
    if not remark:
        return None
    match = re.search(r'(\d+)\s*(?:chicks|CHICKS)', remark, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def extract_buyer_from_description(desc):
    """Extract buyer name from sales description"""
    if not desc:
        return None
    
    desc_upper = desc.upper()
    buyers = ['ISSA CENTER', 'SADIKI', 'MAMA ZAI', 'MTEJA', 'JUMA', 'HASSAN', 'RASHID']
    
    for buyer in buyers:
        if buyer in desc_upper:
            return buyer.title()
    
    return 'Unknown Buyer'

def extract_quantity_from_description(desc):
    """Extract quantity sold from sales description"""
    if not desc:
        return None
    
    patterns = [r'PIC\s+(\d+)', r'QTY\s+(\d+)', r'(\d+)\s*BIRDS']
    
    for pattern in patterns:
        match = re.search(pattern, desc.upper())
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    return None

def extract_unit_price_from_description(desc):
    """Extract unit price from sales description"""
    if not desc:
        return None
    
    match = re.search(r'@(\d+)', desc)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    return None

# ============================================================================
# MIGRATION LOGIC
# ============================================================================

def migrate_data(batch_rows, trans_rows, conn, progress_callback):
    """Execute migration"""
    
    cursor = conn.cursor()
    batch_count = 0
    sales_count = 0
    expense_count = 0
    
    # MIGRATE BATCHES
    progress_callback("Migrating batches...")
    
    for idx, row in enumerate(batch_rows):
        try:
            batch_id = int(row['BatchId'])
            batch_name = row['BatchName'].strip()
            date_started = parse_date(row['DateStarted'])
            date_ended = parse_date(row['DateEnded'])
            remark = row['Remark'].strip() if row['Remark'] else None
            
            status = 'Completed' if date_ended else 'Active'
            qty = extract_quantity_from_remarks(remark)
            if qty is None:
                qty = 500
            
            cursor.execute("""
                INSERT INTO BATCHES_DETAILED 
                (BatchID, BatchName, DateStarted, DateEnded, QuantityChicksStarted, Status, Notes, SourceSystem, MigrationDate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (BatchID) DO NOTHING
            """, (batch_id, batch_name, date_started, date_ended, qty, status, remark, 'Access', datetime.now()))
            
            batch_count += 1
            
        except Exception as e:
            st.warning(f"Error on batch {row['BatchId']}: {str(e)[:50]}")
    
    conn.commit()
    progress_callback(f"✅ Migrated {batch_count} batches")
    
    # MIGRATE TRANSACTIONS
    progress_callback("Migrating transactions...")
    
    for idx, row in enumerate(trans_rows):
        try:
            if row['BOOK ID'].strip() != 'KUKU PROJECT':
                continue
            
            sn = row['S/N'].strip()
            date = parse_date(row['Date'])
            trans_type = row['TRASACTION TYPE'].strip().lower()
            description = row['DESCRIPTION'].strip()
            category = row['CARTEGORY ID'].strip()
            amount = float(row['AMOUNT'].strip().replace(',', ''))
            remark = row['REMARK'].strip() if row['REMARK'] else None
            batch_id_str = row['BatchId'].strip() if row['BatchId'] else ''
            
            try:
                batch_id = int(batch_id_str) if batch_id_str else None
            except:
                batch_id = None
            
            # SALES
            if trans_type == 'cash in' and category in ['SALES', 'CREDIT SALES']:
                
                buyer_name = extract_buyer_from_description(description)
                qty = extract_quantity_from_description(description)
                unit_price = extract_unit_price_from_description(description)
                
                if qty is None:
                    qty = int(amount / 4000) if amount > 0 else 0
                if unit_price is None:
                    unit_price = int(amount / qty) if qty > 0 else amount
                
                cursor.execute("SELECT BuyerID FROM BUYERS WHERE BuyerName = %s", (buyer_name,))
                buyer_result = cursor.fetchone()
                
                if buyer_result:
                    buyer_id = buyer_result[0]
                else:
                    cursor.execute("INSERT INTO BUYERS (BuyerName) VALUES (%s) RETURNING BuyerID", (buyer_name,))
                    buyer_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO DAILY_SALES
                    (BatchID, DateSold, QuantitySold, BuyerID, UnitPrice, TotalRevenue, SaleStatus, Notes, SourceSystem, SourceID, MigrationDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (batch_id, date, qty, buyer_id, unit_price, amount, 'Paid', description, 'Access', sn, datetime.now()))
                
                sales_count += 1
            
            # EXPENSES
            elif trans_type == 'cash out':
                
                category_map = {
                    'VIFARANGA': 'Heating Equipment',
                    'BILLS': 'Electricity Bill',
                    'FEED': 'Feed Purchase',
                    'HEALTH': 'Medicines',
                    'TRANSPORT': 'Transport',
                    'CONSTRUCTION': 'Construction',
                    'SALARY': 'Salaries',
                    'WORK APPLIANCES': 'Equipment',
                }
                
                category_name = category_map.get(category, category)
                
                cursor.execute("""
                    INSERT INTO EXPENSES
                    (ExpenseDate, Category, Description, Amount, ReceivedFrom, BatchID, Notes, SourceSystem, SourceID, MigrationDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (date, category_name, description, amount, remark, batch_id, description, 'Access', sn, datetime.now()))
                
                expense_count += 1
        
        except Exception as e:
            st.warning(f"Error on transaction S/N {row['S/N']}: {str(e)[:50]}")
    
    conn.commit()
    
    return batch_count, sales_count, expense_count

# ============================================================================
# MAIN UI
# ============================================================================

conn = get_connection()

if conn is None:
    st.error("Cannot connect to database")
    st.stop()

st.info("""
### 📋 How to use:

1. **Upload the text files** from your Access database export
2. **Click "Start Migration"**
3. **Wait for completion** ✅

Your historical data will be instantly available in the dashboard!
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Upload Files")
    
    batch_file = st.file_uploader("Upload tblBatch.txt", type="txt", key="batch")
    trans_file = st.file_uploader("Upload tbltransaction.txt", type="txt", key="trans")

with col2:
    st.subheader("📊 File Preview")
    
    if batch_file:
        batch_content = batch_file.read().decode('utf-8')
        _, batch_rows = parse_text_table(batch_content)
        st.metric("Batches to migrate", len(batch_rows))
    
    if trans_file:
        trans_content = trans_file.read().decode('utf-8')
        _, trans_rows = parse_text_table(trans_content)
        
        # Count KUKU transactions
        kuku_count = sum(1 for r in trans_rows if r['BOOK ID'].strip() == 'KUKU PROJECT')
        st.metric("KUKU transactions", kuku_count)

st.divider()

if st.button("🚀 START MIGRATION", use_container_width=True, type="primary"):
    
    if not batch_file or not trans_file:
        st.error("❌ Please upload both files")
        st.stop()
    
    # Read files
    batch_content = batch_file.read().decode('utf-8')
    trans_content = trans_file.read().decode('utf-8')
    
    # Parse
    _, batch_rows = parse_text_table(batch_content)
    _, trans_rows = parse_text_table(trans_content)
    
    if not batch_rows or not trans_rows:
        st.error("❌ Could not parse files")
        st.stop()
    
    # Progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(msg):
        status_text.write(f"⏳ {msg}")
    
    try:
        # Run migration
        batch_count, sales_count, expense_count = migrate_data(
            batch_rows, trans_rows, conn, update_progress
        )
        
        # Success
        status_text.empty()
        progress_bar.progress(100)
        
        st.success("✅ Migration Complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Batches", batch_count)
        with col2:
            st.metric("Sales", sales_count)
        with col3:
            st.metric("Expenses", expense_count)
        with col4:
            st.metric("Total", batch_count + sales_count + expense_count)
        
        st.info("""
        🎉 Your historical data is now in Supabase!
        
        📈 **Dashboard will show:**
        - Complete batch history
        - All past sales with buyers
        - Full expense breakdown
        - Profit/loss analysis
        - Trends and forecasts
        """)
        
    except Exception as e:
        st.error(f"❌ Migration failed: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        conn.rollback()

st.divider()
st.caption("KUKU Project - Complete Farm Management System")
