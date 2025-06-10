# Zimbabwe Product Recognition System - Production Structure

## 📁 Core Production Files

### 🔧 Main Processors
- `enhanced_add_product_vision_tool_clean.py` - Main vision processor with AutoML integration
- `automl_production_processor.py` - AutoML-specific processor
- `direct_vision_server.py` - FastAPI server for vision processing

### 🤖 Training & Data Management
- `automl_training_pipeline.py` - Complete AutoML training pipeline
- `enhanced_training_collector.py` - Zimbabwe-specific pattern recognition for labeling
- `training_data_manager.py` - Data verification and quality management
- `pattern_based_uploader.py` - AutoML-ready training data upload
- `zimbabwe_training_scaler.py` - Strategic collection planning

### 📊 Monitoring & Status
- `check_training_status.py` - Training progress monitoring
- `environment_status.py` - Comprehensive system status reporting

### 🛠️ Utilities
- `upload_images.py` - Easy image upload utility
- `start_server.py` - Server startup script
- `start_automl_production.sh` - Production startup script

### 📋 Configuration & Templates
- `automl_dataset_info.json` - AutoML dataset configuration
- `training_data_template.csv` - Labeling template for training data
- `requirements.txt` - Core dependencies
- `requirements_automl.txt` - AutoML-specific dependencies

### 🔐 Service Accounts
- `firebase-service-account-key.json` - Firebase authentication
- `vision-api-service.json` - Google Cloud Vision API authentication

## 📁 Directory Structure

### `agents/` - Agent system components
- `assistant/tools/` - Assistant tools including get_user_tool.py

### `training_data/` - Training data organization
- `images/` - Categorized training images
- `labels/` - Training labels and annotations
- `collections/` - Collection plans and guides

### `archive/` - Archived development files
- `test_files/` - Development test files
- `docs/` - Development documentation
- `development_scripts/` - Cleanup and deployment scripts

### `common/` - Shared utilities
### `data/` - Data storage
### `docs/` - Production documentation
### `reports/` - System reports

## 🎯 System Capabilities

### Current Features:
✅ AutoML Vision integration with fallback to enhanced Vision API
✅ Zimbabwe-specific product pattern recognition
✅ Smart confidence-based routing (AutoML first if ≥0.6 confidence)
✅ Comprehensive training data collection system
✅ Training progress monitoring and status reporting
✅ Production-ready FastAPI server

### Target Accuracy:
- **Current**: ~50% (basic Vision API)
- **Target**: 90-95% (custom AutoML model)
- **Products**: Zimbabwe retail brands (Hullets, Mazoe, Baker Inn, etc.)

## 🚀 Next Steps

1. **Training Data Collection** (165 more images needed)
   - Use `enhanced_training_collector.py` for pattern-based labeling
   - Focus on priority brands: Huletts, Baker Inn, Coca Cola
   - Follow naming convention: `brand_variant_size_angle.jpg`

2. **AutoML Training** (After 50+ images collected)
   - Run `automl_training_pipeline.py`
   - Monitor with `check_training_status.py`
   - Deploy trained model

3. **Production Deployment**
   - Start with `./start_automl_production.sh`
   - Monitor system status with `environment_status.py`

Generated: 2025-06-10T23:19:03.329434
