# Store Assistant Agent - Image Analysis Service

A comprehensive image analysis service for store assistant agents that can analyze product images to extract structured product information.

## 🎯 Features

- **Product Image Analysis**: Extract product name, brand, size, category, subcategory, and description from images
- **AI-Powered Recognition**: Uses Google Vision API for enhanced text and object detection
- **Image Enhancement**: Automatic image processing for better analysis results
- **Firebase Storage Integration**: Upload and store processed images with public URLs
- **Zimbabwe-Specific Categories**: Tailored product categorization for local market needs
- **Multilingual Support**: English, Shona, and Ndebele language support

## 📋 What It Returns

The system returns clean JSON structure with:
```json
{
  "name": "ORIGINAL TASTE",
  "category": "Beverages", 
  "subcategory": "Soft Drinks",
  "size": "500",
  "brand": "Coca-Cola",
  "description": "500ml of coca-cola original taste",
  "image_url": "https://storage.googleapis.com/...",
  "success": true
}
```

## 🏗️ Architecture

```
store-agents/
├── agents/assistant/           # Main agent logic
│   ├── __main__.py            # Server entry point
│   ├── agent.py               # Agent configuration
│   ├── task_manager.py        # Request processing
│   └── tools/                 # Agent tools
│       ├── analyze_image_tool.py    # Image analysis tool
│       ├── get_products_tool.py     # Product management
│       └── get_user_tool.py         # User management
├── common/                    # Shared services
│   ├── image_analysis_service.py    # Core image analysis
│   ├── product_service.py           # Product operations
│   ├── user_service.py              # User operations
│   └── server.py                    # FastAPI server
└── firebase-service-account-key.json # Firebase credentials
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Project with Vision API enabled
- Firebase project with Storage configured

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install google-adk firebase-admin google-cloud-vision pillow
   ```
3. Configure environment variables in `.env`:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_SERVICE_ACCOUNT_KEY=path/to/service-account-key.json
   ```

### Running the Server
```bash
python -m agents.assistant
```

The server will start on `http://localhost:8003`

## 📡 API Usage

### Analyze Product Image

**POST** `/run`

```json
{
  "message": "Please analyze this product image",
  "context": {
    "user_id": "store_owner_123",
    "image": "base64_encoded_image_data"
  }
}
```

### Response
```json
{
  "message": "Product analysis results...",
  "status": "success",
  "data": {
    "raw_events": {...}
  }
}
```

## 🛠️ Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Gemini API key for AI processing
- `FIREBASE_PROJECT_ID`: Firebase project identifier
- `FIREBASE_SERVICE_ACCOUNT_KEY`: Path to Firebase service account JSON
- `STORE_AGENTS_HOST`: Server host (default: 127.0.0.1)
- `STORE_AGENTS_PORT`: Server port (default: 8003)

### Firebase Setup
1. Create a Firebase project
2. Enable Cloud Storage
3. Generate service account key
4. Set storage rules for public access

### Google Cloud Vision API
1. Enable Vision API in Google Cloud Console
2. Use the same service account for authentication

## 🧩 Components

### Image Analysis Service
- **Image Enhancement**: Automatic brightness, contrast, and sharpness adjustment
- **Vision API Integration**: Text detection and object recognition
- **Product Information Extraction**: Smart parsing of detected text
- **Storage Management**: Firebase Storage upload with public URLs

### Agent Tools
- **analyze_product_image**: Main image analysis functionality
- **get_user_info**: User account management
- **get_products_info**: Product inventory operations

### Task Manager
- **Request Processing**: Handle API requests with image data
- **Session Management**: Maintain conversation context
- **Response Formatting**: Structure agent responses

## 🔧 Customization

### Adding New Product Categories
Edit the categorization logic in `image_analysis_service.py`:

```python
def _categorize_product(self, text_content: str) -> tuple:
    # Add your custom category logic
    if "your_product_type" in text_content.lower():
        return "Your Category", "Your Subcategory"
```

### Extending Analysis Features
Add new analysis methods to `ImageAnalysisService`:

```python
async def _analyze_nutritional_info(self, text_content: str):
    # Custom analysis logic
    pass
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues and questions, please open a GitHub issue.
