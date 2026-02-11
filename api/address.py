from fastapi import APIRouter, Request, HTTPException
from tortoise.exceptions import DoesNotExist, IntegrityError
from typing import Optional
from pydantic import BaseModel
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.jwt import verify_and_get_token_data
from muban.muban import Address

router = APIRouter()

class AddressItem(BaseModel):
    userName: str
    userPhone: str
    provinceName: str
    cityName: str
    regionName: str
    detailAddress: str
    defaultFlag: Optional[int] = 0
    addressId: Optional[int] = None

@router.get("/address")
# 定义一个异步函数，用于获取地址列表
async def get_address_list(request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 根据token中的用户id，从数据库中获取地址列表
    addresses = await Address.filter(user_id=token_response["data"].user_id)
    # 返回地址列表
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": [{
            "addressId": addr.address_id,
            "userName": addr.user_name,
            "userPhone": addr.user_phone,
            "provinceName": addr.province_name,
            "cityName": addr.city_name,
            "regionName": addr.region_name,
            "detailAddress": addr.detail_address,
            "defaultFlag": addr.default_flag
        } for addr in addresses]
    }

@router.get("/address/default")
# 定义一个异步函数，用于获取默认地址
async def get_default_address(request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 根据token中的用户id，获取默认地址
    address = await Address.get_or_none(
        user_id=token_response["data"].user_id,
        default_flag=1
    )
    # 如果没有默认地址，返回错误信息
    if not address:
        return {
            "resultCode": 404,
            "message": "没有默认地址,请先添加地址",
            "data": None
        }
    
    # 返回默认地址信息
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
             "addressId": address.address_id,
            "userName": address.user_name,
            "userPhone": address.user_phone,
            "provinceName": address.province_name,
            "cityName": address.city_name,
            "regionName": address.region_name,
            "detailAddress": address.detail_address,
            "defaultFlag": address.default_flag
        }
    }

@router.get("/address/{address_id}")
# 定义一个异步函数，用于获取地址详情
async def get_address_detail(address_id: int, request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 根据地址id和用户id查询地址信息
    address = await Address.get_or_none(
        address_id=address_id,
        user_id=token_response["data"].user_id
    )
    # 如果地址不存在，返回错误信息
    if not address:
        return {
            "resultCode": 404,
            "message": "地址不存在",
            "data": None
        }
    
    # 返回地址详情
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
             "addressId": address.address_id,
            "userName": address.user_name,
            "userPhone": address.user_phone,
            "provinceName": address.province_name,
            "cityName": address.city_name,
            "regionName": address.region_name,
            "detailAddress": address.detail_address,
            "defaultFlag": address.default_flag
        }
    }

@router.post("/address")
async def add_address(item: AddressItem, request: Request):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    try:
        # 如果设置为默认地址，先取消其他默认地址
        if item.defaultFlag == 1:
            await Address.filter(
                user_id=token_response["data"].user_id,
                default_flag=1
            ).update(default_flag=0)

        # 创建新的地址
        address = await Address.create(
            user_id=token_response["data"].user_id,
            user_name=item.userName,
            user_phone=item.userPhone,
            province_name=item.provinceName,
            city_name=item.cityName,
            region_name=item.regionName,
            detail_address=item.detailAddress,
            default_flag=item.defaultFlag
        )
        # 返回成功信息
        return {
            "resultCode": 200,
            "message": "添加成功",
            "data": {
                "addressId": address.address_id
            }
        }
    except Exception as e:
    
        # 捕获异常，返回错误信息
        return {
            "resultCode": 500,
            "message": f"修改失败: {str(e)}",
            "data": None
        }

@router.put("/address")
async def edit_address(item: AddressItem, request: Request):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    try:
        # 如果设置为默认地址，先取消其他默认地址
        if item.defaultFlag == 1:
            await Address.filter(
                user_id=token_response["data"].user_id,
                default_flag=1
            ).update(default_flag=0)

        # 更新地址信息
        await Address.filter(
            address_id=item.addressId,
            user_id=token_response["data"].user_id
        ).update(
            user_name=item.userName,
            user_phone=item.userPhone,
            province_name=item.provinceName,
            city_name=item.cityName,
            region_name=item.regionName,
            detail_address=item.detailAddress,
            default_flag=item.defaultFlag
        )
        # 返回修改成功信息
        return {
            "resultCode": 200,
            "message": "修改成功",
            "data": None
        }
    except DoesNotExist:
        # 如果地址不存在，返回错误信息
        return {
            "resultCode": 404,
            "message": "地址不存在",
            "data": None
        }
    except Exception as e:
        # 如果修改失败，返回错误信息
        return {
            "resultCode": 500,
            "message": f"修改失败: {str(e)}",
            "data": None
        }

@router.delete("/address/{address_id}")
async def delete_address(address_id: int, request: Request):
    token = request.headers.get("token")
    token_response = verify_and_get_token_data(token)
    if token_response["resultCode"] != 200:
        return token_response

    try:
        await Address.filter(
            address_id=address_id,
            user_id=token_response["data"].user_id
        ).delete()
        return {
            "resultCode": 200,
            "message": "删除成功",
            "data": None
        }
    except Exception as e:
        return {
            "resultCode": 500,
            "message": f"删除失败: {str(e)}",
            "data": None
        }