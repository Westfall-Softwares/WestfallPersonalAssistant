#!/usr/bin/env python3
"""
Initialize the finance database tables without creating the GUI
"""

import sqlite3
import os

def init_finance_database():
    """Initialize finance database with comprehensive tables"""
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/finance.db')
    cursor = conn.cursor()
    
    print("Creating finance database tables...")
    
    # Invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            client_email TEXT,
            amount DECIMAL(10,2) NOT NULL,
            tax_amount DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL,
            currency TEXT DEFAULT 'USD',
            date_created DATE NOT NULL,
            date_due DATE NOT NULL,
            date_paid DATE,
            status TEXT DEFAULT 'draft',
            description TEXT,
            notes TEXT,
            payment_terms TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            vendor TEXT,
            date DATE NOT NULL,
            receipt_path TEXT,
            tax_deductible BOOLEAN DEFAULT 1,
            project_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Projects table for time tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client_name TEXT,
            hourly_rate DECIMAL(10,2),
            total_budget DECIMAL(10,2),
            status TEXT DEFAULT 'active',
            start_date DATE,
            end_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Time tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            description TEXT,
            hours DECIMAL(5,2) NOT NULL,
            hourly_rate DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            date DATE NOT NULL,
            billable BOOLEAN DEFAULT 1,
            invoiced BOOLEAN DEFAULT 0,
            invoice_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (invoice_id) REFERENCES invoices (id)
        )
    ''')
    
    # Financial goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name TEXT NOT NULL,
            target_amount DECIMAL(10,2) NOT NULL,
            current_amount DECIMAL(10,2) DEFAULT 0,
            target_date DATE,
            category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Finance database tables created successfully!")

if __name__ == "__main__":
    init_finance_database()