import os
import sys
import logging
import uvicorn
import asyncio 
from dotenv import load_dotenv

# Add the parent directory to Python path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .task_manager import TaskManager
from .agent import root_agent
from common.server import create_agent_server


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_status = load_dotenv(dotenv_path=dotenv_path, override=True)

task_manager_instance: TaskManager | None = None



async def main():
    global task_manager_instance
    
    agent_instance, exit_stack = await root_agent()
    
    async with exit_stack:
        
        task_manager_instance  = TaskManager(agent=agent_instance)
        logger.info("TaskManager initialized with agent instance.")

        host = os.getenv("STORE_AGENTS_HOST", "127.0.0.1")
        port = int(os.getenv("STORE_AGENTS_PORT", 8004))  # Changed from 8003 to 8004
        
        app = create_agent_server(
            name=agent_instance.name,
            description=agent_instance.description,
            task_manager=task_manager_instance 
        )
        
        logger.info(f"Store Assistant Agent server starting on {host}:{port}")
        
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        await server.serve()

        logger.info("Store Assistant Agent  server stopped.")
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Speaker Agent server stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during server startup: {str(e)}", exc_info=True)
        sys.exit(1) 
