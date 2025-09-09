#!/usr/bin/env python3
"""
Initialize sample data for the financial management system
This creates sample projects, clients, and initial data for demo purposes
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

def initialize_sample_data():
    """Initialize the finance database with sample data for solo developers"""
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Connect to finance database
    conn = sqlite3.connect('data/finance.db')
    cursor = conn.cursor()
    
    print("🗄️ Initializing Financial Management Sample Data...")
    
    # Sample projects for solo developers
    sample_projects = [
        ("Website Redesign", "TechCorp Inc", 150.00, 15000.00, "active", 
         date.today() - timedelta(days=30), None, "Complete website redesign and modernization"),
        ("Mobile App Development", "StartupXYZ", 120.00, 25000.00, "active",
         date.today() - timedelta(days=20), None, "React Native mobile application"),
        ("API Integration", "E-commerce Plus", 100.00, 8000.00, "completed",
         date.today() - timedelta(days=45), date.today() - timedelta(days=5), "Payment gateway integration"),
        ("Database Optimization", "DataFlow LLC", 130.00, 12000.00, "active",
         date.today() - timedelta(days=10), None, "PostgreSQL performance optimization"),
        ("Personal Portfolio", "Self", 0.00, 5000.00, "active",
         date.today() - timedelta(days=60), None, "Personal portfolio website and blog")
    ]
    
    # Insert sample projects
    for project in sample_projects:
        cursor.execute("""
            INSERT OR IGNORE INTO projects 
            (name, client_name, hourly_rate, total_budget, status, start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, project)
    
    print("   ✅ Sample projects created")
    
    # Sample time entries
    project_ids = []
    cursor.execute("SELECT id FROM projects")
    project_ids = [row[0] for row in cursor.fetchall()]
    
    if project_ids:
        sample_time_entries = [
            (project_ids[0], "Frontend component development", 8.0, 150.00, 1200.00, 
             date.today() - timedelta(days=5), True, False),
            (project_ids[0], "Client meeting and requirements", 2.0, 150.00, 300.00,
             date.today() - timedelta(days=4), True, False),
            (project_ids[1], "App architecture design", 6.0, 120.00, 720.00,
             date.today() - timedelta(days=3), True, False),
            (project_ids[1], "Authentication module", 10.0, 120.00, 1200.00,
             date.today() - timedelta(days=2), True, False),
            (project_ids[3], "Database analysis", 4.0, 130.00, 520.00,
             date.today() - timedelta(days=1), True, False),
        ]
        
        for entry in sample_time_entries:
            cursor.execute("""
                INSERT OR IGNORE INTO time_entries 
                (project_id, description, hours, hourly_rate, total_amount, date, billable, invoiced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, entry)
    
    print("   ✅ Sample time entries created")
    
    # Sample invoices
    sample_invoices = [
        ("INV-20240901-001", "TechCorp Inc", "contact@techcorp.com", 5000.00, 250.00, 5250.00,
         "USD", date.today() - timedelta(days=20), date.today() - timedelta(days=5), 
         date.today() - timedelta(days=2), "paid", "Website homepage redesign phase 1", "", "Net 15"),
        ("INV-20240902-002", "StartupXYZ", "billing@startupxyz.com", 3600.00, 0.00, 3600.00,
         "USD", date.today() - timedelta(days=15), date.today() + timedelta(days=15),
         None, "sent", "Mobile app development - Sprint 1", "", "Net 30"),
        ("INV-20240903-003", "E-commerce Plus", "finance@ecomplus.com", 8000.00, 400.00, 8400.00,
         "USD", date.today() - timedelta(days=10), date.today() - timedelta(days=10),
         date.today() - timedelta(days=8), "paid", "API Integration project completion", "", "Net 15"),
        ("INV-20240904-004", "DataFlow LLC", "accounts@dataflow.com", 2600.00, 130.00, 2730.00,
         "USD", date.today() - timedelta(days=5), date.today() + timedelta(days=25),
         None, "sent", "Database optimization - Phase 1", "", "Net 30"),
    ]
    
    for invoice in sample_invoices:
        cursor.execute("""
            INSERT OR IGNORE INTO invoices 
            (invoice_number, client_name, client_email, amount, tax_amount, total_amount,
             currency, date_created, date_due, date_paid, status, description, notes, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, invoice)
    
    print("   ✅ Sample invoices created")
    
    # Sample expenses
    sample_expenses = [
        ("GitHub Pro subscription", 4.00, "Software", "GitHub", "GitHub", 
         date.today() - timedelta(days=30), True, None, "Monthly subscription"),
        ("Adobe Creative Suite", 52.99, "Software", "Adobe", "Adobe Systems",
         date.today() - timedelta(days=25), True, None, "Monthly subscription"),
        ("AWS hosting costs", 89.50, "Software", "Cloud Services", "Amazon Web Services",
         date.today() - timedelta(days=20), True, None, "Monthly cloud hosting"),
        ("Business lunch with client", 45.75, "Meals", "Business Meals", "Restaurant ABC",
         date.today() - timedelta(days=15), True, None, "Client meeting"),
        ("New monitor", 299.99, "Hardware", "Office Equipment", "Tech Store",
         date.today() - timedelta(days=10), True, None, "4K development monitor"),
        ("Conference ticket", 299.00, "Education", "Professional Development", "DevCon 2024",
         date.today() - timedelta(days=5), True, None, "Annual developer conference"),
        ("Internet service", 79.99, "Office Supplies", "Utilities", "ISP Provider",
         date.today() - timedelta(days=2), True, None, "Monthly internet"),
    ]
    
    for expense in sample_expenses:
        cursor.execute("""
            INSERT OR IGNORE INTO expenses 
            (description, amount, category, subcategory, vendor, date, tax_deductible, receipt_path, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, expense)
    
    print("   ✅ Sample expenses created")
    
    # Sample financial goals
    sample_goals = [
        ("Emergency Fund", 50000.00, 25000.00, date(2024, 12, 31), "Savings", 
         "6-month emergency fund for business continuity"),
        ("New Development Setup", 8000.00, 3500.00, date(2024, 11, 30), "Equipment",
         "Upgrade to M2 MacBook Pro and accessories"),
        ("Annual Revenue Goal", 120000.00, 67890.00, date(2024, 12, 31), "Revenue",
         "Target annual revenue for solo development business"),
        ("Professional Development", 3000.00, 850.00, date(2024, 12, 31), "Education",
         "Courses, conferences, and certifications"),
        ("Business Tax Reserve", 15000.00, 8500.00, date(2025, 4, 15), "Taxes",
         "Set aside funds for quarterly and annual taxes"),
    ]
    
    for goal in sample_goals:
        cursor.execute("""
            INSERT OR IGNORE INTO financial_goals 
            (goal_name, target_amount, current_amount, target_date, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, goal)
    
    print("   ✅ Sample financial goals created")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print("🎉 Financial Management sample data initialized successfully!")
    print("\n📊 Summary:")
    print("   • 5 sample projects with different clients and rates")
    print("   • Multiple time entries showing billable work")
    print("   • 4 sample invoices (2 paid, 2 outstanding)")
    print("   • 7 business expenses across different categories")
    print("   • 5 financial goals tracking business objectives")
    print("\n💡 You can now:")
    print("   • Track time against projects")
    print("   • Generate invoices from time entries")
    print("   • Monitor expenses and profit/loss")
    print("   • View financial reports and analytics")
    print("   • Set and track financial goals")

if __name__ == "__main__":
    initialize_sample_data()