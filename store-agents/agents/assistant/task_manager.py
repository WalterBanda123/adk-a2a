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
        
        # Use the message directly without adding user metadata
        request_content = adk_types.Content(role="user", parts=[adk_types.Part(text=message)])
        
        try:
            events = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=request_content
            )
            
            final_message="(No response generated)"
            raw_events=[]
            pdf_data = None
            
            #Process responses
            async for event in events:
                raw_events.append(event.model_dump(exclude_none=True))
                
                # Check for tool call responses that might contain PDF data
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            # Check if this is a function response with PDF data
                            if hasattr(part, 'function_response') and part.function_response:
                                try:
                                    import json
                                    response_data = part.function_response.response
                                    logger.info(f"Found function response: {type(response_data)}")
                                    
                                    # If it's a string, parse as JSON
                                    if isinstance(response_data, str):
                                        response_data = json.loads(response_data)
                                    
                                    # Check if response contains PDF data
                                    if isinstance(response_data, dict) and 'pdf_data' in response_data:
                                        pdf_data = response_data['pdf_data']
                                        logger.info(f"Extracted PDF data from tool response: {len(pdf_data.get('pdf_base64', '')) if pdf_data else 0} bytes")
                                    elif isinstance(response_data, dict):
                                        logger.info(f"Function response keys: {list(response_data.keys())}")
                                except Exception as e:
                                    logger.warning(f"Could not parse function response: {e}")
                
                #Only extract from the final response
                if event.is_final_response() and event.content and event.content.role == 'model':
                    if event.content and event.content.parts:
                        final_message = event.content.parts[0].text
                    logger.info(f"Final response: {final_message}")
                    
            response = {
                "message":final_message,
                "status":"success",
                "data":{
                    "raw_events": raw_events[-1] if raw_events else None
                }  
            }
            
            # Add PDF data if found
            if pdf_data:
                response["pdf_data"] = pdf_data
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return {
                "message":f"Error: {str(e)}",
                "status":"error",
                "data":{}  
            }
        
        
               