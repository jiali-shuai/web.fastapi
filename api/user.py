from fastapi import APIRouter, Depends, Request
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib
from tortoise.exceptions import DoesNotExist, IntegrityError
from typing import Optional, Union

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.jwt import create_access_token, verify_and_get_token_data
from muban.muban import User

router = APIRouter()

class LoginRequest(BaseModel):
    loginName: str
    passwordMd5: str

class RegisterRequest(BaseModel):
    loginName: str 
    password: str

    class Config:
        from_attributes = True
    
class TokenData(BaseModel):
    user_id: str
    exp: Optional[str] = None



@router.post("/login")
# 定义一个异步函数login，参数为LoginRequest类型的request
async def login(request: LoginRequest):
    # 根据request中的loginName获取用户信息
    user = await User.get(login_name=request.loginName)
    # 如果用户密码不匹配，返回错误信息
    if user.password_md5 != request.passwordMd5.lower():
         return {
                "resultCode": 400, 
                "message": "用户名或密码错误",
                "data": None
            }
        
    
    # 生成用户token
    token = create_access_token({"sub": str(user.user_id)})
    # 返回登录成功信息，包括token
    return {
        "resultCode": 200, 
        "message": "登录成功",
        "data": token
    }
    

@router.post("/register") 
# 定义一个异步函数register，参数为RegisterRequest类型的request
async def register(request: RegisterRequest):
    try:
        # 将request中的password进行md5加密
        password_md5 = hashlib.md5(request.password.encode()).hexdigest()
        
        # 创建一个User对象，将request中的loginName、password_md5、nick_name赋值给User对象的对应属性
        await User.create(
            login_name=request.loginName,
            password_md5=password_md5,
            nick_name=request.loginName
        )
        # 返回注册成功的消息
        return  {"resultCode": 200, "message": "注册成功", "data": None}
        
    except IntegrityError:
        # 如果用户名已存在，返回用户名已存在的消息
        return  {"resultCode": 400, "message": "用户名已存在","data": None}
        

@router.get("/info")
# 定义一个异步函数，用于获取用户信息

async def get_user_info(request: Request):
    token = request.headers.get("token")
    token_response = verify_and_get_token_data(token)
    if token_response["resultCode"] != 200:
        return token_response
    user = await User.get(user_id=token_response["data"].user_id)
    # 返回用户信息
    return {
        "resultCode": 200,
        "message": "成功",
        "data": {
            "userId": user.user_id,
            "loginName": user.login_name,
            "nickName": user.nick_name
        }
    }

@router.put("/info")
# 定义一个异步函数，用于更新用户信息
async def update_user_info(request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response
    
    # 从请求体中获取json数据
    data = await request.json()
    # 根据token中的用户id获取用户信息
    user = await User.get(user_id=token_response["data"].user_id)
    await user.update_from_dict({"nick_name": data.get("nickName", user.nick_name)})
    await user.update_from_dict({"password_md5": data.get("passwordMd5", user.password_md5)})
    await user.save()
    # 返回更新成功的信息
    return {"resultCode": 200, "message": "更新成功", "data": None}

@router.post("/logout")
async def logout(request: Request):
    return {"resultCode": 200, "message": "退出成功"}
