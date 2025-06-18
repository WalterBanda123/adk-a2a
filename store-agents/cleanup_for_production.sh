#!/bin/bash

# Production Cleanup Script
# Removes unnecessary files and keeps only production-ready components

echo "🧹 Starting production cleanup..."

# Files to remove - unnecessary for launch
echo "Removing unnecessary files..."

# Old startup scripts (replaced by unified agent)
rm -f start_product_transaction_agent.sh
rm -f start_automl_production.sh  
rm -f start_photo_cart.sh
rm -f start_server.py

# Redundant documentation
rm -f CURL_EXAMPLES.md
rm -f PHOTO_CART_INTEGRATION_REPORT.md
rm -f PHOTO_CART_README.md
rm -f PRODUCTION_READY.md
rm -f PRODUCTION_STRUCTURE.md
rm -f SYSTEM_RECOVERY_REPORT.md
rm -f UNIFIED_LAUNCH_SUMMARY.md

# Standalone services (replaced by unified agent)
rm -f direct_vision_server.py
rm -f photo_cart_app.py
rm -f photo_cart_gcp_setup.py
rm -f photo_cart_service.py
rm -f product_management_api.py

# Development/testing files
rm -f test_photo_cart.py
rm -f test_product_transaction_agent.py
rm -f enhanced_text_detection.py
rm -f final_verification.py
rm -f image_processing_utils.py

# AutoML training files (keep basic ones for future training)
rm -f automl_production_processor.py
rm -f enhanced_add_product_vision_tool_clean.py
rm -f enhanced_training_collector.py
rm -f pattern_based_uploader.py
rm -f zimbabwe_training_scaler.py

# Upload utilities (replaced by unified chat)
rm -f upload_images.py

# Agent startup log
rm -f agent_startup.log

# Temporary data files
rm -f automl_dataset_info.json
rm -f automl_model_info.json
rm -f training_data_template.csv

# Remove unnecessary requirement files
rm -f requirements_automl.txt
rm -f requirements_photo_cart.txt
rm -f requirements_product_transaction.txt

# Clean up cache
rm -rf __pycache__
rm -rf .pytest_cache

echo "✅ Cleanup complete!"

echo ""
echo "🎯 Production-ready files remaining:"
echo "   📁 Core system:"
echo "      • unified_chat_agent.py       - Main chat interface"
echo "      • start_unified_agent.sh      - Startup script"
echo "      • test_unified_api.py         - API testing"
echo ""
echo "   📁 Essential services:"
echo "      • common/user_service.py      - User management"
echo "      • common/real_product_service.py - Product management"
echo "      • agents/                     - Sub-agent systems"
echo ""
echo "   📁 Training (optional):"
echo "      • automl_training_pipeline.py - Model training"
echo "      • check_training_status.py   - Training monitoring"
echo "      • training_data_manager.py   - Data management"
echo ""
echo "   📁 Configuration:"
echo "      • requirements.txt           - Dependencies"
echo "      • setup_products.py         - Product setup"
echo "      • .env                      - Environment config"
echo ""
echo "   📁 Documentation:"
echo "      • README.md                 - Main documentation"
echo "      • UNIFIED_CHAT_API.md       - API guide"
echo "      • REAL_PRODUCTS_GUIDE.md    - Product setup guide"
echo ""
echo "🚀 Ready for production launch!"
