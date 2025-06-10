"""
Test Complete Scrapping Workflow
Demonstrates extracting product information from the encoded image and storing as text files
"""

import asyncio
import logging
import json
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from agents.complete_scrapping_agent import CompleteScrappingAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scrapping_workflow():
    """Test the complete scrapping workflow with the provided encoded image"""
    
    # Read the encoded image from the file
    encoded_image_path = Path(__file__).parent / "encoded_image.txt"
    
    if not encoded_image_path.exists():
        logger.error("encoded_image.txt not found")
        return
    
    with open(encoded_image_path, 'r') as f:
        encoded_image = f.read().strip()
    
    logger.info(f"Loaded encoded image, size: {len(encoded_image)} characters")
    
    # Initialize scrapping agent
    user_id = "test_user_123"
    agent = CompleteScrappingAgent(
        user_id=user_id,
        auto_upload=False,  # Disable bucket upload for local testing
        bucket_provider="gcs"
    )
    
    logger.info("✅ Scrapping agent initialized")
    
    try:
        # Test 1: Scrap product from the encoded image
        logger.info("\n" + "="*50)
        logger.info("TEST 1: Scrapping product from encoded image")
        logger.info("="*50)
        
        result = await agent.scrap_and_store_product(
            data=encoded_image,
            data_type="image_base64",
            source_context="test_encoded_image",
            tags=["test", "product", "image_analysis"],
            upload_to_bucket=False
        )
        
        print("\n🔍 SCRAPPING RESULT:")
        print(json.dumps(result, indent=2))
        
        if result["success"]:
            scrap_id = result["scrap_id"]
            logger.info(f"✅ Successfully created scrap: {scrap_id}")
            
            # Test 2: Get scrapping stats
            logger.info("\n" + "="*50)
            logger.info("TEST 2: Getting scrapping statistics")
            logger.info("="*50)
            
            stats = await agent.get_scrapping_stats()
            print("\n📊 SCRAPPING STATS:")
            print(json.dumps(stats, indent=2))
            
            # Test 3: Search for the created scrap
            logger.info("\n" + "="*50)
            logger.info("TEST 3: Searching for created scraps")
            logger.info("="*50)
            
            search_result = await agent.search_scraps(
                query="product",
                tags=["test"],
                limit=5
            )
            print("\n🔍 SEARCH RESULTS:")
            print(json.dumps(search_result, indent=2))
            
            # Test 4: Get the full content of the scrap
            logger.info("\n" + "="*50)
            logger.info("TEST 4: Getting full scrap content")
            logger.info("="*50)
            
            # Access storage service directly to get content
            scrap_content = await agent.storage_service.get_scrap(scrap_id)
            if scrap_content:
                print("\n📄 SCRAP CONTENT PREVIEW:")
                print(scrap_content["content"][:500] + "..." if len(scrap_content["content"]) > 500 else scrap_content["content"])
                
                print(f"\n📁 Full content saved to: {scrap_content['filepath']}")
            
            # Test 5: Create export file
            logger.info("\n" + "="*50)
            logger.info("TEST 5: Creating export file")
            logger.info("="*50)
            
            export_result = await agent.export_user_scraps(
                export_format="txt",
                upload_to_bucket=False
            )
            print("\n📦 EXPORT RESULT:")
            print(json.dumps(export_result, indent=2))
            
            if export_result["success"]:
                print(f"\n📁 Export file created at: {export_result['export_path']}")
        
        else:
            logger.error(f"❌ Scrapping failed: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_text_scrapping():
    """Test scrapping from text input"""
    
    logger.info("\n" + "="*50)
    logger.info("BONUS TEST: Scrapping from text description")
    logger.info("="*50)
    
    user_id = "test_user_text_123"
    agent = CompleteScrappingAgent(
        user_id=user_id,
        auto_upload=False
    )
    
    # Sample product text
    product_text = """
    Mazoe Orange Crush
    Brand: Mazoe
    Size: 2L
    Category: Beverages
    Description: Premium orange-flavored drink concentrate from Zimbabwe
    Ingredients: Orange juice concentrate, sugar, citric acid, natural flavors
    Instructions: Mix 1 part concentrate with 7 parts water
    """
    
    result = await agent.scrap_and_store_product(
        data=product_text,
        data_type="text",
        source_context="manual_product_entry",
        tags=["mazoe", "beverage", "zimbabwe", "concentrate"],
        upload_to_bucket=False
    )
    
    print("\n📝 TEXT SCRAPPING RESULT:")
    print(json.dumps(result, indent=2))
    
    if result["success"]:
        # Get the content
        scrap_content = await agent.storage_service.get_scrap(result["scrap_id"])
        if scrap_content:
            print("\n📄 TEXT SCRAP CONTENT:")
            print(scrap_content["content"])

async def demonstrate_file_organization():
    """Show how files are organized with user ID prefixes"""
    
    logger.info("\n" + "="*50)
    logger.info("FILE ORGANIZATION DEMONSTRATION")
    logger.info("="*50)
    
    # Create scraps for multiple users to show organization
    users = ["user_001", "user_002", "user_003"]
    
    for user_id in users:
        agent = CompleteScrappingAgent(user_id=user_id, auto_upload=False)
        
        # Create a sample scrap for each user
        await agent.scrap_and_store_product(
            data=f"Sample product for {user_id}",
            data_type="text",
            source_context="demo",
            tags=[f"user_{user_id}"],
            upload_to_bucket=False
        )
        
        logger.info(f"✅ Created sample scrap for {user_id}")
    
    # Show directory structure
    data_path = Path(__file__).parent / "data" / "scraps"
    
    print(f"\n📁 STORAGE DIRECTORY STRUCTURE:")
    print(f"Root: {data_path}")
    
    if data_path.exists():
        for user_dir in data_path.iterdir():
            if user_dir.is_dir():
                print(f"\n👤 {user_dir.name}/")
                for file in user_dir.iterdir():
                    if file.is_file():
                        size = file.stat().st_size
                        print(f"   📄 {file.name} ({size} bytes)")

if __name__ == "__main__":
    print("🚀 Starting Complete Scrapping Workflow Tests")
    print("=" * 60)
    
    # Run all tests
    asyncio.run(test_scrapping_workflow())
    asyncio.run(test_text_scrapping())
    asyncio.run(demonstrate_file_organization())
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\nFiles are organized as:")
    print("  data/scraps/user_{user_id}/")
    print("    ├── {user_id}_{scrap_id}_{timestamp}.txt")
    print("    ├── {user_id}_{scrap_id}_{timestamp}.txt")
    print("    └── scraps_index.json")
    print("\nThis structure makes it easy to:")
    print("  - Upload to buckets with user ID prefixes")
    print("  - Organize and backup user data separately")
    print("  - Scale storage across multiple users")
    print("  - Implement user-specific retention policies")
