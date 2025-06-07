import os
import json
import inspect
from typing import Dict, Any, Callable, Optional, List

from fastapi import FastAPI, Body, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field



class AgentRequest(BaseModel):
    message: str = Field(..., description="The message to process")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the request")
    session_id: Optional[str] = Field(None, description="Session identifier for stateful interactions")


class AgentResponse(BaseModel):
    message: str = Field(..., description="The response message")
    status: str = Field(default="success", description="Status of the response (success, error)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data returned by the agent")
    session_id: Optional[str] = Field(None, description="Session identifier for stateful interactions")
    
    
def create_agent_server(
    name:str,
    description:str,
    task_manager:Any
)-> FastAPI:
    """
    .....
    """
    app = FastAPI(title=f"{name} Agent", description=description)
    
    @app.post("/run", response_model=AgentResponse)
    async def run(request: AgentRequest = Body(...)):
        try:
            result = await task_manager.process_task(request.message, request.context, request.session_id)
            
            return AgentResponse(
                message=result.get("message", "Task completed"),
                status="success",
                data=result.get("data", {}),
                session_id=request.session_id
            )
        except Exception as e:
            
            return AgentResponse(
                message=f"Error processing request: {str(e)}",
                status="error",
                data={"error_type": type(e).__name__},
                session_id=request.session_id
            )
            
    return app