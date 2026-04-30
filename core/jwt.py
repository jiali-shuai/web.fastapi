
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv(), override=True)

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM_JWT")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES"))


class TokenData(BaseModel):
    user_id: str
    exp: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if not token or not isinstance(token, str):
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    return token_data


def verify_and_get_token_data(token: str):
    if not token:
        return {"resultCode": 401, "message": "未登录", "data": None}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
            return {"resultCode": 401, "message": "token已过期", "data": None}
        token_data = verify_token(token)
        return {"resultCode": 200, "message": "成功", "data": token_data}
    except jwt.PyJWTError:
        return {"resultCode": 401, "message": "未登录", "data": None}
