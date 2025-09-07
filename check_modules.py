import os

print("Checking for business modules in your project...\n")

modules_to_check = [
    "business_intelligence/dashboard/business_dashboard.py",
    "crm_system/crm_manager.py",
    "screen_intelligence/capture/multi_monitor_capture.py",
    "ai_assistant/core/chat_manager.py",
    "security/encryption_manager.py"
]

for module in modules_to_check:
    if os.path.exists(module):
        print(f"✅ FOUND: {module}")
        # Check file size to ensure it's not empty
        size = os.path.getsize(module)
        if size < 100:
            print(f"   ⚠️  Warning: File is very small ({size} bytes)")
    else:
        print(f"❌ MISSING: {module}")

print("\nChecking for __init__.py files...")

init_files = [
    "business_intelligence/__init__.py",
    "business_intelligence/dashboard/__init__.py",
    "crm_system/__init__.py",
    "screen_intelligence/__init__.py",
    "screen_intelligence/capture/__init__.py"
]

for init_file in init_files:
    if os.path.exists(init_file):
        print(f"✅ FOUND: {init_file}")
    else:
        print(f"❌ MISSING: {init_file}")
        # Create it
        os.makedirs(os.path.dirname(init_file), exist_ok=True)
        with open(init_file, 'w') as f:
            f.write('"""Module"""\n')
        print(f"   ✅ Created: {init_file}")