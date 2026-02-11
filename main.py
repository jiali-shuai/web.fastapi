from fastapi import FastAPI, Depends
from tortoise import Tortoise
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware import Middleware

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.kuayu import setup_cors  # 导入跨域设置函数
from core.jwt import verify_token  # 导入JWT验证函数
from shujuku.config import DATABASE_CONFIG, app1
from api.router import api_router



app = app1 # 将JWT验证函数注册为全局依赖
setup_cors(app)  # 应用跨域设置
app.include_router(api_router)  

if __name__ == "__main__":
    import uvicorn
    # 修改为使用模块导入字符串形式
    uvicorn.run("main:app", host="127.0.0.1", port=1090)
