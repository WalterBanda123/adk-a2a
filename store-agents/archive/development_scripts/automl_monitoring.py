#!/usr/bin/env python3
"""
AutoML System Monitoring Dashboard
Monitor AutoML performance and system status
"""
import json
import time
from datetime import datetime

def show_system_status():
    """Display current system status"""
    
    print("📊 AutoML System Status Dashboard")
    print("=" * 50)
    print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Dataset Status
    try:
        with open('automl_dataset_info.json', 'r') as f:
            dataset_info = json.load(f)
        print("✅ Dataset Status: Active")
        print(f"   📊 Dataset: {dataset_info['dataset_name']}")
        print(f"   📍 Project: {dataset_info['project_id']}")
    except:
        print("❌ Dataset Status: Not Found")
    
    # Model Status
    try:
        with open('automl_model_info.json', 'r') as f:
            model_info = json.load(f)
        print("✅ Model Status: Deployed")
        print(f"   🤖 Model: {model_info['model_name']}")
        print(f"   📅 Deployed: {model_info.get('deployed_at', 'Unknown')}")
        print(f"   🎯 Ready: {model_info.get('ready_for_production', False)}")
    except:
        print("⏳ Model Status: Training or Not Available")
    
    # Integration Status
    try:
        from automl_production_processor import AutoMLProductionProcessor
        processor = AutoMLProductionProcessor()
        status = processor.get_model_status()
        
        print("✅ Integration Status: Active")
        print(f"   🤖 AutoML Available: {status['automl_available']}")
        print(f"   🛡️ Fallback Available: {status['fallback_available']}")
        print(f"   🚀 Production Ready: {status['ready_for_production']}")
    except:
        print("⚠️ Integration Status: Issues Detected")
    
    print()
    print("📋 Quick Actions:")
    print("   • Check training: python check_training_status.py")
    print("   • Test system: python automl_production_processor.py")
    print("   • View logs: tail -f server.log")
    print("   • Start server: ./start_automl_production.sh")

if __name__ == "__main__":
    show_system_status()
