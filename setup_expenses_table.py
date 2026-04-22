#!/usr/bin/env python3
"""
KUKU PROJECT - Create Comprehensive Expenses Table
Ready to receive migrated data from Access database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("="*70)
    print("CREATING EXPENSES TABLE FOR DATA MIGRATION")
    print("="*70)
    
    # Drop existing table if exists (optional - for testing)
    # cursor.execute("DROP TABLE IF EXISTS EXPENSES CASCADE")
    
    # Create EXPENSE_CATEGORIES table first
    print("\n1. Creating EXPENSE_CATEGORIES table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EXPENSE_CATEGORIES (
            CategoryID SERIAL PRIMARY KEY,
            CategoryName VARCHAR(100) NOT NULL UNIQUE,
            Description TEXT,
            DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ EXPENSE_CATEGORIES created")
    
    # Create main EXPENSES table with all possible fields
    print("\n2. Creating EXPENSES table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EXPENSES (
            ExpenseID SERIAL PRIMARY KEY,
            
            -- Date information
            ExpenseDate DATE NOT NULL,
            MonthYear VARCHAR(7),
            
            -- Category and description
            Category VARCHAR(100) NOT NULL,
            Subcategory VARCHAR(100),
            Description TEXT NOT NULL,
            ItemName VARCHAR(255),
            
            -- Amount information
            Amount DECIMAL(15, 2) NOT NULL,
            Quantity DECIMAL(10, 3),
            UnitPrice DECIMAL(15, 2),
            CurrencyCode VARCHAR(3) DEFAULT 'TZS',
            
            -- Payment details
            PaymentMethod VARCHAR(50),
            PaymentStatus VARCHAR(50) DEFAULT 'Paid',
            ReceivedFrom VARCHAR(150),
            InvoiceNumber VARCHAR(50),
            ReceiptNumber VARCHAR(50),
            
            -- Batch relationship
            BatchID INTEGER REFERENCES BATCHES_DETAILED(BatchID),
            
            -- Additional info
            Notes TEXT,
            ApprovedBy VARCHAR(100),
            IsRecurring BOOLEAN DEFAULT FALSE,
            RecurrencePattern VARCHAR(50),
            
            -- Metadata
            DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            DateModified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CreatedBy VARCHAR(100),
            IsArchived BOOLEAN DEFAULT FALSE,
            
            -- Migration tracking
            SourceSystem VARCHAR(50),
            SourceID VARCHAR(100),
            MigrationDate TIMESTAMP
        )
    """)
    print("   ✅ EXPENSES table created")
    
    # Create indexes for faster queries
    print("\n3. Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON EXPENSES(ExpenseDate)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON EXPENSES(Category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_batch ON EXPENSES(BatchID)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_source ON EXPENSES(SourceSystem, SourceID)")
    print("   ✅ Indexes created")
    
    # Insert default expense categories
    print("\n4. Adding expense categories...")
    categories = [
        ("Feed Purchase", "Purchase of chicken feed - Starter, Grower, Finisher"),
        ("Chick Purchase", "Initial purchase of baby chicks"),
        ("Electricity Bill", "Monthly electricity costs for farm"),
        ("Water Bill", "Water supply for farm"),
        ("Salaries", "Worker salaries and payments"),
        ("Labor Costs", "Daily labor hire or contract work"),
        ("Medicines", "Veterinary medicines, vaccines, antibiotics"),
        ("Vitamins", "Vitamin supplements for birds"),
        ("Equipment Purchase", "Farm equipment - feeders, drinkers, etc"),
        ("Equipment Repair", "Repair of existing equipment"),
        ("Maintenance", "General farm maintenance"),
        ("Construction", "Building, coop construction, fencing"),
        ("Heating Equipment", "Heat lamps, heating costs"),
        ("Gas/Fuel", "Fuel for generators or transport"),
        ("Transport", "Transportation costs"),
        ("Storage", "Storage facility rental"),
        ("Packaging", "Packaging materials for sale"),
        ("Marketing", "Marketing and advertising costs"),
        ("Insurance", "Farm or liability insurance"),
        ("Licenses", "Business licenses and permits"),
        ("Office Supplies", "Stationery, books, records"),
        ("Miscellaneous", "Other miscellaneous expenses"),
    ]
    
    for name, desc in categories:
        cursor.execute("""
            INSERT INTO EXPENSE_CATEGORIES (CategoryName, Description)
            VALUES (%s, %s)
            ON CONFLICT (CategoryName) DO NOTHING
        """, (name, desc))
    
    conn.commit()
    print(f"   ✅ {len(categories)} expense categories added")
    
    # Show category list
    print("\n" + "="*70)
    print("AVAILABLE EXPENSE CATEGORIES:")
    print("="*70)
    
    cursor.execute("""
        SELECT CategoryID, CategoryName, Description 
        FROM EXPENSE_CATEGORIES 
        ORDER BY CategoryID
    """)
    
    categories = cursor.fetchall()
    for cat in categories:
        print(f"\n{cat[0]:2d}. {cat[1]}")
        print(f"    → {cat[2]}")
    
    print("\n" + "="*70)
    print("✅ EXPENSES TABLE SYSTEM READY FOR MIGRATION!")
    print("="*70)
    
    print("""
    
TABLE STRUCTURE READY FOR:
├─ Date tracking (ExpenseDate, MonthYear)
├─ Category classification (Category, Subcategory)
├─ Amount tracking (Amount, Quantity, UnitPrice)
├─ Payment info (Method, Status, Invoice, Receipt)
├─ Batch linking (BatchID for linking to farm batches)
├─ Recurring expenses (IsRecurring, RecurrencePattern)
├─ Approval tracking (ApprovedBy)
├─ Migration tracking (SourceSystem, SourceID, MigrationDate)
└─ Full audit trail (CreatedBy, DateModified)

Ready to receive data from your Access database!
    """)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
