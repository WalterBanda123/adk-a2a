import os
import logging
import uuid
import base64
from typing import Dict, Any, Optional

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types as adk_types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "store_agents"

class TaskManager:
    
    def __init__(self, agent: Agent):
        logger.info(f"Initialising TaskManager for agent {agent.name}")
        self.agent = agent
        
        # Initialize the ADK services
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()
        
        # Create the runner
        self.runner = Runner(
            agent=self.agent,
            app_name=APP_NAME,
            session_service=self.session_service,
            artifact_service=self.artifact_service
        )
        
    async def process_task(self, message: str, context: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        
        user_id = context.get("user_id", "default_store_agents_user")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")
            
        session = await self.session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        
        if not session:
            session = await self.session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id, state={})
            logger.info(f"Created new session: {session_id}")
        
        # Check if there's an image in the context
        has_image = "image" in context and context["image"]
        
        # Build the message - if there's an image, keep it simple
        if has_image:
            enhanced_message = f"""User ID: {user_id}

{message}

I can see you've shared an image. Let me analyze this product for you."""
        else:
            enhanced_message = f"User ID: {user_id}\n\n{message}"
        
        # Create content parts - start with text
        content_parts = [adk_types.Part(text=enhanced_message)]
        
        # Add image to the conversation if present
        if has_image:
            try:
                # Decode base64 image
                image_data = base64.b64decode(context["image"])
                
                # Create image part for the content
                image_part = adk_types.Part(
                    inline_data=adk_types.Blob(
                        mime_type="image/jpeg",  # Assume JPEG for now
                        data=image_data
                    )
                )
                content_parts.append(image_part)
                
                logger.info(f"Added image data to request ({len(image_data)} bytes)")
                
            except Exception as e:
                logger.warning(f"Failed to process image data: {str(e)}")
        
        request_content = adk_types.Content(role="user", parts=content_parts)
        
        try:
            events = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=request_content
            )
            
            final_message = "(No response generated)"
            raw_events = []
            
            # Process responses
            async for event in events:
                raw_events.append(event.model_dump(exclude_none=True))
                
                # Only extract from the final response
                if event.is_final_response() and event.content and event.content.role == 'model':
                    if event.content and event.content.parts:
                        final_message = event.content.parts[0].text
                    logger.info(f"Final response: {final_message}")
                    
            return {
                "message": final_message,
                "status": "success",
                "data": {
                    "raw_events": raw_events[-1] if raw_events else None
                }  
            }
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return {
                "message": f"Error: {str(e)}",
                "status": "error",
                "data": {}  
            }
