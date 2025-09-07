#!/usr/bin/env python3
import sys
import os

# Add path fix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports with path fix...\n")

try:
    from business_intelligence.dashboard.business_dashboard import BusinessDashboard
    print("✅ BusinessDashboard imported successfully")
except ImportError as e:
    print(f"❌ BusinessDashboard import failed: {e}")

try:
    from crm_system.crm_manager import CRMManager
    print("✅ CRMManager imported successfully")
except ImportError as e:
    print(f"❌ CRMManager import failed: {e}")

try:
    from screen_intelligence.capture.multi_monitor_capture import MultiMonitorCapture
    print("✅ MultiMonitorCapture imported successfully")
except ImportError as e:
    print(f"❌ MultiMonitorCapture import failed: {e}")

print("\nChecking for __init__.py files...")
init_files = [
    "business_intelligence/__init__.py",
    "business_intelligence/dashboard/__init__.py",
    "crm_system/__init__.py",
    "screen_intelligence/__init__.py",
    "screen_intelligence/capture/__init__.py"
]

for f in init_files:
    if os.path.exists(f):
        print(f"✅ {f} exists")
    else:
        print(f"❌ {f} MISSING - Creating it now...")
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, 'w') as file:
            file.write('"""Package"""\n')
        print(f"   ✅ Created {f}")