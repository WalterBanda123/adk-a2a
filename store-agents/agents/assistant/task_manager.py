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
            
    
        # Check if there's image data in the context
        if "image_data" in context:
            # Include image data information in the message for the agent
            # Simplified image_info to be more concise
            image_info = f"\n\n--- IMAGE DATA AVAILABLE ---\n"
            image_info += f"Task: {message}\n"
            image_info += f"To process this image, use the 'add_product_vision_tool' with these exact parameters:\n"
            image_info += f"- image_data: [provided_image_data_base64_string_or_url]\n" # Placeholder, actual data is large
            image_info += f"- is_url: {context.get('is_url', False)}\n"
            image_info += f"- user_id: {user_id}\n"
            # The full image_data is still passed in the tool call by the agent based on its instructions
            # The agent will see the cue "IMAGE DATA AVAILABLE" and its instructions tell it to find the params.
            # The task_manager passes the actual full image data in the context that the agent framework uses.
            
            # Construct the message for the LLM. The critical part is the cue and the parameters structure.
            # The actual base64 string will be retrieved by the agent from the context provided by the user message.
            # We are just showing the agent *how* the parameters are named.
            
            # The agent's instructions in add_new_product_subagent.py tell it:
            # "2. The user message will contain the necessary parameters for the tool: 'image_data', 'is_url', and 'user_id'. Extract these exact values from the user's message."
            # So, the enhanced_message needs to *simulate* this user message structure for the agent.
            
            # This is the message the *agent* sees, simulating what a user might send if they were manually providing all details.
            simulated_user_message_with_image_details = (
                f"{message}\n\n"
                f"IMAGE DATA AVAILABLE:\n"
                f"- image_data: {context.get('image_data', '')}\n" # Actual data for the agent to parse
                f"- is_url: {context.get('is_url', False)}\n"
                f"- user_id: {user_id}"
            )
            enhanced_message = f"User ID: {user_id}\n\n{simulated_user_message_with_image_details}"

        else:
            enhanced_message = f"User ID: {user_id}\n\n{message}"
        
        request_content = adk_types.Content(role="user", parts=[adk_types.Part(text=enhanced_message)])
        
        try:
            events = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=request_content
            )
            
            final_message="(No response generated)"
            raw_events=[]
            product_data = None
            
            #Process responses
            async for event in events:
                event_data = event.model_dump(exclude_none=True)
                raw_events.append(event_data)
                
                # Debug logging - print the full event structure when we see tool usage
                if "add_product_vision_tool" in str(event_data):
                    logger.info(f"🔍 FOUND VISION TOOL EVENT:")
                    logger.info(f"Full event data: {event_data}")
                
                # Check for tool calls
                # According to ADK structure, tool_calls are often found in event_data['actions']['tool_action']['tool_calls']
                # or sometimes event_data['tool_calls'] directly in some event types.
                current_tool_calls = None
                if event_data.get('actions') and isinstance(event_data['actions'], dict):
                    tool_action = event_data['actions'].get('tool_action')
                    if tool_action and isinstance(tool_action, dict):
                        current_tool_calls = tool_action.get('tool_calls')
                
                if current_tool_calls:
                    logger.info(f"Found tool calls: {current_tool_calls}")
                    # Iteration here might not be necessary if the response is always in a separate event.

                # Check for tool responses
                # Tool responses are in event_data['content']['parts'] when event_data['content']['role'] == 'tool'
                current_content = event_data.get('content')
                if current_content and isinstance(current_content, dict) and current_content.get('role') == 'tool':
                    parts = current_content.get('parts')
                    if parts and isinstance(parts, list):
                        for part in parts:
                            if isinstance(part, dict) and part.get('function_response'):
                                fn_response_data = part['function_response']
                                if isinstance(fn_response_data, dict):
                                    logger.info(f"Found function response: {fn_response_data.get('name')} (ID: {fn_response_data.get('id')})")
                                    if fn_response_data.get('name') == 'add_product_vision_tool':
                                        try:
                                            tool_result = fn_response_data.get('response')
                                            logger.info(f"Tool result for add_product_vision_tool: {tool_result}")
                                            if isinstance(tool_result, dict) and tool_result.get('success'):
                                                product_data = {
                                                    "title": tool_result.get('title', ''),
                                                    "brand": tool_result.get('brand', ''),
                                                    "size": tool_result.get('size', ''),
                                                    "unit": tool_result.get('unit', ''),
                                                    "category": tool_result.get('category', ''),
                                                    "subcategory": tool_result.get('subcategory', ''),
                                                    "description": tool_result.get('description', ''),
                                                    "confidence": tool_result.get('confidence', 0.0),
                                                    "processing_time": tool_result.get('processing_time', 0.0)
                                                }
                                                logger.info(f"Extracted product data: {product_data}")
                                        except Exception as e:
                                            logger.warning(f"Failed to extract product data from tool response: {e}")
                
                #Only extract from the final response
                if event.is_final_response() and event.content and event.content.role == 'model':
                    if event.content and event.content.parts:
                        final_message = event.content.parts[0].text
                    logger.info(f"Final response: {final_message}")
                    
            # Build response data
            response_data = {
                "raw_events": raw_events[-1] if raw_events else None # Keep last raw event for context if needed
            }
            
            # Include product data if available, this will be the primary data source for product info
            if product_data:
                response_data["product"] = product_data
                    
            return {
                "message":final_message, # LLM's textual summary
                "status":"success",
                "data": response_data # Contains 'product' if tool ran, and 'raw_events'
            }
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return {
                "message":f"Error: {str(e)}",
                "status":"error",
                "data":{}  
            }



