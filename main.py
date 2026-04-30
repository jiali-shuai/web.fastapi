import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.kuayu import setup_cors
from dotenv import load_dotenv, find_dotenv
import os

from shujuku.config import app1
from api.router import api_router

load_dotenv(find_dotenv(), override=True)

app = app1
setup_cors(app)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST")
    port = int(os.getenv("SERVER_PORT"))
    uvicorn.run("main:app", host=host, port=port)
