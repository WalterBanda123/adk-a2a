import os
import logging
import tempfile
import uuid
from typing import Dict, Any, Optional

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types as adk_types

# Import the vision processor for direct image analysis
from .tools.add_product_vision_tool import ProductVisionProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME="store_agents"



class TaskManager:
    
    def __init__(self, agent:Agent):
        logger.info(f"Initialising TaskManager for agent {agent.name}")
        self.agent = agent
        
        #Initialise the ADK services
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()
        
        # Initialize vision processor for direct image analysis
        self.vision_processor = ProductVisionProcessor()
        
        #Create the runner
        self.runner = Runner(
            agent=self.agent,
            app_name=APP_NAME,
            session_service=self.session_service,
            artifact_service=self.artifact_service
        )
        
    async def process_task(self, message:str, context:Dict[str, Any], session_id:Optional[str] = None) -> Dict[str, Any]:
        
        user_id = context.get("user_id", "default_store_agents_user")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generate new session_id: {session_id}")
            
        session = await self.session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        
        if not session:
            session = await self.session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id, state={})
            logger.info(f"Created new session: {session_id}")
    
        # NEW APPROACH: Check for image data and process directly
        if "image_data" in context:
            logger.info("🖼️ Image data detected - processing directly with vision API")
            
            try:
                # Extract image parameters
                image_data = context.get("image_data", "")
                is_url = context.get("is_url", False)
                
                if not image_data:
                    return {
                        "message": "Image data is required but not provided",
                        "status": "error",
                        "data": {}
                    }
                
                # Process image directly using vision processor
                vision_result = await self.vision_processor.process_image(image_data, is_url)
                
                if vision_result.get("success"):
                    product_info = vision_result.get("product", {})
                    
                    # Create a concise summary message
                    title = product_info.get("title", "Unknown Product")
                    brand = product_info.get("brand", "")
                    size = product_info.get("size", "")
                    unit = product_info.get("unit", "")
                    category = product_info.get("category", "")
                    processing_time = product_info.get("processing_time", 0)
                    
                    # Build summary message
                    summary_parts = [f"✅ Product identified: {title}"]
                    if brand:
                        summary_parts.append(f"Brand: {brand}")
                    if size and unit:
                        summary_parts.append(f"Size: {size}{unit}")
                    if category:
                        summary_parts.append(f"Category: {category}")
                    summary_parts.append(f"Processing time: {processing_time:.2f}s")
                    
                    summary_message = " | ".join(summary_parts)
                    
                    # Structure the product data for response
                    product_data = {
                        "title": title,
                        "brand": brand,
                        "size": size,
                        "unit": unit,
                        "category": category,
                        "subcategory": product_info.get("subcategory", ""),
                        "description": product_info.get("description", ""),
                        "confidence": product_info.get("confidence", 0.0),
                        "processing_time": processing_time
                    }
                    
                    logger.info(f"✅ Successfully processed image: {title}")
                    
                    return {
                        "message": summary_message,
                        "status": "success",
                        "data": {
                            "product": product_data,
                            "processing_method": "direct_vision_api"
                        }
                    }
                else:
                    error_msg = vision_result.get("error", "Unknown vision processing error")
                    logger.error(f"❌ Vision processing failed: {error_msg}")
                    
                    return {
                        "message": f"Failed to analyze image: {error_msg}",
                        "status": "error", 
                        "data": {"error": error_msg}
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error in direct image processing: {str(e)}")
                return {
                    "message": f"Image processing error: {str(e)}",
                    "status": "error",
                    "data": {"error": str(e)}
                }
        
        # FALLBACK: For non-image requests, use the original agent approach
        logger.info("📝 Processing text-only request with agent")
        
        enhanced_message = f"User ID: {user_id}\n\n{message}"
        request_content = adk_types.Content(role="user", parts=[adk_types.Part(text=enhanced_message)])
        
        try:
            events = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=request_content
            )
            
            final_message = "(No response generated)"
            raw_events = []
            
            # Process responses from agent
            async for event in events:
                event_data = event.model_dump(exclude_none=True)
                raw_events.append(event_data)
                
                # Only extract from the final response
                if event.is_final_response() and event.content and event.content.role == 'model':
                    if event.content and event.content.parts:
                        final_message = event.content.parts[0].text
                    logger.info(f"Final response: {final_message}")
                    
            return {
                "message": final_message,
                "status": "success",
                "data": {
                    "raw_events": raw_events[-1] if raw_events else None,
                    "processing_method": "agent_llm"
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing task with agent: {str(e)}")
            return {
                "message": f"Error: {str(e)}",
                "status": "error",
                "data": {}
            }



