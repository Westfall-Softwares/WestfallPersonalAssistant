#!/usr/bin/env python3
"""
Setup Demo Tailor Pack
Copies the marketing essentials pack to the proper location for testing
"""

import os
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.platform_compatibility import PlatformManager
from util.tailor_pack_manager import get_tailor_pack_manager

def setup_demo_pack():
    """Set up the demo marketing pack in the proper location"""
    
    # Get platform manager and create directories
    platform_manager = PlatformManager()
    app_dirs = platform_manager.setup_application_directories("westfall-assistant")
    target_packs_dir = app_dirs['data'] / "tailor_packs" / "installed"
    
    # Ensure target directory exists
    target_packs_dir.mkdir(parents=True, exist_ok=True)
    
    # Source directory (current project)
    source_pack_dir = Path(__file__).parent / "tailor_packs" / "installed" / "marketing_essentials"
    target_pack_dir = target_packs_dir / "marketing_essentials"
    
    print(f"Source: {source_pack_dir}")
    print(f"Target: {target_pack_dir}")
    
    if source_pack_dir.exists():
        if target_pack_dir.exists():
            shutil.rmtree(target_pack_dir)
        
        shutil.copytree(source_pack_dir, target_pack_dir)
        print(f"✅ Demo pack copied to: {target_pack_dir}")
        
        # Test the pack manager
        manager = get_tailor_pack_manager()
        packs = manager.get_installed_packs()
        print(f"📦 Found {len(packs)} installed pack(s)")
        for pack in packs:
            print(f"  - {pack.name} v{pack.version}")
        
        return True
    else:
        print(f"❌ Source pack not found: {source_pack_dir}")
        return False

if __name__ == "__main__":
    setup_demo_pack()