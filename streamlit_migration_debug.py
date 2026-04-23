#!/usr/bin/env python3
"""
KUKU PROJECT - Streamlit Migration Interface (WITH ERROR LOGGING)
Upload Access data files and migrate to Supabase
Shows ALL errors so we can debug!
"""

import streamlit as st
import psycopg2
from datetime import datetime
import re
import os

st.set_page_config(
    page_title="KUKU Data Migration",
    page_icon="📤",
    layout="wide"
)

st.title("📤 KUKU Data Migration (DEBUG)")
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
        st.error(f"❌ Database connection failed: {str(e)}")
        return None

# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_text_table(text_content):
    """Parse Access export text table format"""
    rows = []
    lines = text_content.split('\n')
    
    # Find header line
    header_idx = -1
    for idx, line in enumerate(lines):
        if '|' in line and '---' not in line:
            header_idx = idx
            break
    
    if header_idx == -1:
        return [], []
    
    # Get headers
    header_line = lines[header_idx]
    headers = [h.strip() for h in header_line.split('|')[1:-1]]
    
    if not headers:
        return [], []
    
    # Parse data rows
    for line_idx in range(header_idx + 1, len(lines)):
        line = lines[line_idx]
        
        if '---' in line or not line.strip():
            continue
        
        if not line.strip().startswith('|'):
            continue
        
        parts = line.split('|')
        values = [v.strip() for v in parts[1:-1]]
        
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

def extract_buyer_from_description(desc):
    """Extract buyer name from sales description"""
    if not desc:
        return 'Unknown Buyer'
    
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
# MIGRATION LOGIC (WITH ERROR REPORTING)
# ============================================================================

def migrate_data(batch_rows, trans_rows, conn, error_list):
    """Execute migration with detailed error logging"""
    
    cursor = conn.cursor()
    batch_count = 0
    sales_count = 0
    expense_count = 0
    
    st.write("**1️⃣ Migrating Batches...**")
    
    for row in batch_rows:
        try:
            batch_id = int(row['BatchId'])
            batch_name = row['BatchName'].strip()
            date_started = parse_date(row['DateStarted'])
            date_ended = parse_date(row['DateEnded'])
            remark = row['Remark'].strip() if row['Remark'] else None
            
            status = 'Completed' if date_ended else 'Active'
            
            qty = 500
            if remark:
                match = re.search(r'(\d+)\s*(?:chicks|CHICKS)', remark)
                if match:
                    qty = int(match.group(1))
            
            cursor.execute("""
                INSERT INTO BATCHES_DETAILED 
                (BatchID, BatchName, DateStarted, DateEnded, QuantityChicksStarted, Status, Notes, SourceSystem, MigrationDate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (BatchID) DO NOTHING
            """, (batch_id, batch_name, date_started, date_ended, qty, status, remark, 'Access', datetime.now()))
            
            batch_count += 1
            st.write(f"   ✓ Batch {batch_id}: {batch_name}")
            
        except Exception as e:
            error_msg = f"Batch {row['BatchId']}: {str(e)}"
            error_list.append(error_msg)
            st.error(f"   ❌ {error_msg}")
    
    try:
        conn.commit()
        st.write(f"   ✅ Committed {batch_count} batches")
    except Exception as e:
        error_msg = f"Batch commit error: {str(e)}"
        error_list.append(error_msg)
        st.error(f"   ❌ {error_msg}")
        conn.rollback()
    
    # SALES
    st.write("\n**2️⃣ Migrating Sales...**")
    
    for row in trans_rows:
        try:
            if row['BOOK ID'].strip() != 'KUKU PROJECT':
                continue
            
            sn = row['S/N'].strip()
            date = parse_date(row['Date'])
            trans_type = row['TRASACTION TYPE'].strip().lower()
            description = row['DESCRIPTION'].strip()
            category = row['CARTEGORY ID'].strip()
            amount_str = row['AMOUNT'].strip().replace(',', '')
            
            # Parse amount
            try:
                amount = float(amount_str)
            except:
                continue
            
            remark = row['REMARK'].strip() if row['REMARK'] else None
            batch_id_str = row['BatchId'].strip() if row['BatchId'] else ''
            
            try:
                batch_id = int(batch_id_str) if batch_id_str else None
            except:
                batch_id = None
            
            # SALES only
            if trans_type == 'cash in' and category in ['SALES', 'CREDIT SALES']:
                
                buyer_name = extract_buyer_from_description(description)
                qty = extract_quantity_from_description(description)
                unit_price = extract_unit_price_from_description(description)
                
                if qty is None:
                    qty = int(amount / 4000) if amount > 0 else 0
                if unit_price is None:
                    unit_price = int(amount / qty) if qty > 0 else amount
                
                # Get or create buyer
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
                """, (batch_id, date, qty, buyer_id, unit_price, amount, 'Paid', description, 'Access', sn, datetime.now()))
                
                sales_count += 1
        
        except Exception as e:
            error_msg = f"Sale S/N {row['S/N']}: {str(e)}"
            error_list.append(error_msg)
    
    try:
        conn.commit()
        st.write(f"   ✅ Committed {sales_count} sales")
    except Exception as e:
        error_msg = f"Sales commit error: {str(e)}"
        error_list.append(error_msg)
        st.error(f"   ❌ {error_msg}")
        conn.rollback()
    
    # EXPENSES
    st.write("\n**3️⃣ Migrating Expenses...**")
    
    for row in trans_rows:
        try:
            if row['BOOK ID'].strip() != 'KUKU PROJECT':
                continue
            
            sn = row['S/N'].strip()
            date = parse_date(row['Date'])
            trans_type = row['TRASACTION TYPE'].strip().lower()
            description = row['DESCRIPTION'].strip()
            category = row['CARTEGORY ID'].strip()
            amount_str = row['AMOUNT'].strip().replace(',', '')
            
            try:
                amount = float(amount_str)
            except:
                continue
            
            remark = row['REMARK'].strip() if row['REMARK'] else None
            batch_id_str = row['BatchId'].strip() if row['BatchId'] else ''
            
            try:
                batch_id = int(batch_id_str) if batch_id_str else None
            except:
                batch_id = None
            
            # EXPENSES only
            if trans_type == 'cash out':
                
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
                """, (date, category_name, description, amount, remark, batch_id, description, 'Access', sn, datetime.now()))
                
                expense_count += 1
        
        except Exception as e:
            error_msg = f"Expense S/N {row['S/N']}: {str(e)}"
            error_list.append(error_msg)
    
    try:
        conn.commit()
        st.write(f"   ✅ Committed {expense_count} expenses")
    except Exception as e:
        error_msg = f"Expenses commit error: {str(e)}"
        error_list.append(error_msg)
        st.error(f"   ❌ {error_msg}")
        conn.rollback()
    
    return batch_count, sales_count, expense_count

# ============================================================================
# MAIN UI
# ============================================================================

conn = get_connection()

if conn is None:
    st.error("❌ Cannot connect to database")
    st.stop()

st.info("""
### 📋 How to use:

1. **Upload the text files** from your Access database export
2. **Click "Start Migration"**
3. **See detailed progress** with all errors shown
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Upload Files")
    batch_file = st.file_uploader("Upload tblBatch.txt", type="txt", key="batch")
    trans_file = st.file_uploader("Upload tbltransaction.txt", type="txt", key="trans")

with col2:
    st.subheader("📊 Preview")
    if batch_file:
        batch_content = batch_file.read().decode('utf-8-sig', errors='ignore')
        _, batch_rows = parse_text_table(batch_content)
        st.metric("Batches", len(batch_rows))
    
    if trans_file:
        trans_content = trans_file.read().decode('utf-8-sig', errors='ignore')
        _, trans_rows = parse_text_table(trans_content)
        
        kuku_count = sum(1 for r in trans_rows if r['BOOK ID'].strip() == 'KUKU PROJECT')
        st.metric("KUKU transactions", kuku_count)

st.divider()

if st.button("🚀 START MIGRATION", use_container_width=True, type="primary"):
    
    if not batch_file or not trans_file:
        st.error("❌ Please upload both files")
        st.stop()
    
    # Read files
    batch_content = batch_file.read().decode('utf-8-sig', errors='ignore')
    trans_content = trans_file.read().decode('utf-8-sig', errors='ignore')
    
    # Parse
    _, batch_rows = parse_text_table(batch_content)
    _, trans_rows = parse_text_table(trans_content)
    
    if not batch_rows or not trans_rows:
        st.error("❌ Could not parse files")
        st.stop()
    
    # Error log
    error_list = []
    
    st.write("### Migration Progress:")
    
    # Run migration
    batch_count, sales_count, expense_count = migrate_data(
        batch_rows, trans_rows, conn, error_list
    )
    
    # Results
    st.divider()
    st.write("### 📊 Migration Results:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Batches", batch_count)
    with col2:
        st.metric("Sales", sales_count)
    with col3:
        st.metric("Expenses", expense_count)
    with col4:
        st.metric("Total", batch_count + sales_count + expense_count)
    
    # Show errors if any
    if error_list:
        st.write("### ⚠️ Errors Found:")
        for error in error_list[:20]:  # Show first 20 errors
            st.error(error)
        
        if len(error_list) > 20:
            st.warning(f"... and {len(error_list) - 20} more errors")
    else:
        st.success("✅ No errors! Migration complete!")

st.divider()
st.caption("KUKU Project - Complete Farm Management System")
