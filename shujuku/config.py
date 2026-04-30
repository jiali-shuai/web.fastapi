
from fastapi import FastAPI
from tortoise import Tortoise
from contextlib import asynccontextmanager
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv(), override=True)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# MySQL数据库配置
DATABASE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT")),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "database": os.getenv("DB_NAME"),
            }
        }
    },
    "apps": {
        "models": {
            "models": ["muban.muban"],
            "default_connection": "default",
        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await Tortoise.init(config=DATABASE_CONFIG)
        await Tortoise.generate_schemas()
        print("[OK] 数据库连接成功")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        raise
    yield
    await Tortoise.close_connections()


app1 = FastAPI(lifespan=lifespan)
