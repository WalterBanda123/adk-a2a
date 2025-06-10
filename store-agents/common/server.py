import os
import json
import inspect
import base64
from typing import Dict, Any, Callable, Optional, List

from fastapi import FastAPI, Body, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
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
    name: str,
    description: str,
    task_manager: Any,
    endpoints: Optional[Dict[str, Callable]] = None,
    well_known_path: Optional[str] = None
) -> FastAPI:
    app = FastAPI(title=f"{name} Agent", description=description)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8100",
            "http://127.0.0.1:8100",
            "https://localhost:8100",
            "https://127.0.0.1:8100"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    if well_known_path is None:
        module = inspect.getmodule(inspect.stack()[1][0])
        if module and module.__file__:
            module_path = module.__file__
            well_known_path = os.path.join(os.path.dirname(module_path), ".well-known")
        else:
            well_known_path = ".well-known"
    
    os.makedirs(well_known_path, exist_ok=True)
    
    # Generate agent.json if it doesn't exist
    agent_json_path = os.path.join(well_known_path, "agent.json")
    if not os.path.exists(agent_json_path):
        endpoint_names = ["run"]
        if endpoints:
            endpoint_names.extend(endpoints.keys())
        
        agent_metadata = {
            "name": name,
            "description": description,
            "endpoints": endpoint_names,
            "version": "1.0.0"
        }
        
        with open(agent_json_path, "w") as f:
            json.dump(agent_metadata, f, indent=2)
    
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
            
    @app.get("/.well-known/agent.json")
    async def get_metadata():
        with open(agent_json_path, "r") as f:
            return JSONResponse(content=json.load(f))
    
    # Add PDF serving endpoints
    @app.get("/reports/{filename}")
    async def serve_pdf(filename: str):
        """Serve PDF files from the reports directory"""
        # Get the reports directory path
        current_frame = inspect.currentframe()
        if current_frame is None:
            raise RuntimeError("Failed to retrieve the current frame.")
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(current_frame))), "reports")
        file_path = os.path.join(reports_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    @app.get("/reports")
    async def list_reports():
        """List available PDF reports"""
        # Get the reports directory path
        current_frame = inspect.currentframe()
        if current_frame is None:
            raise RuntimeError("Failed to retrieve the current frame.")
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(current_frame))), "reports")
        reports = []
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.endswith('.pdf'):
                    file_path = os.path.join(reports_dir, file)
                    stat = os.stat(file_path)
                    reports.append({
                        "filename": file,
                        "size": stat.st_size,
                        "created": stat.st_ctime,
                        "download_url": f"/reports/{file}"
                    })
        
        return {"reports": reports}
    
    @app.get("/reports/{filename}/download")
    async def get_pdf_base64(filename: str):
        """Get PDF content as base64 for direct download/display"""
        # Get the reports directory path
        current_frame = inspect.currentframe()
        if current_frame is None:
            raise RuntimeError("Failed to retrieve the current frame.")
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(current_frame))), "reports")
        file_path = os.path.join(reports_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read PDF file and encode as base64
        with open(file_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return {
            "filename": filename,
            "content_type": "application/pdf",
            "size": len(pdf_content),
            "data": pdf_base64,
            "download_url": f"data:application/pdf;base64,{pdf_base64}"
        }
    
    if endpoints:
        for path, handler in endpoints.items():
            app.add_api_route(f"/{path}", handler, methods=["POST"])
            
    return app