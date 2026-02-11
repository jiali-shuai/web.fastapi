from fastapi import APIRouter, Request
from tortoise.exceptions import IntegrityError
from typing import List,Optional
from pydantic import BaseModel
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.jwt import verify_and_get_token_data
from muban.muban import Cart, Goods

router = APIRouter()

class CartItem(BaseModel):
    cartItemId: Optional[int] = None
    goodsId: Optional[int] = None
    goodsCount: int

@router.get("/shop-cart")
# 异步获取购物车信息
async def get_cart(request: Request):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 根据token中的用户id查询购物车信息，并预加载商品信息
    carts = await Cart.filter(user_id=token_response["data"].user_id).prefetch_related('goods')
    # 返回购物车信息
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": [{
            "cartItemId": cart.car_id,  # 购物车项id
            "goodsId": cart.goods_id,  # 商品id
            "goodsCount": cart.goods_count,  # 商品数量
            "goodsName": cart.goods.goodsName,  # 修改为goodsName
            "goodsCoverImg": cart.goods.goodsCoverImg,  # 保持原样
            "sellingPrice": float(cart.goods.sellingPrice)  # 保持原样
        } for cart in carts]
    }

@router.post("/shop-cart")
# 定义一个异步函数add_cart，用于添加商品到购物车
async def add_cart(item: CartItem, request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    try:
        # 先检查商品是否已在购物车中
        exists = await Cart.exists(
            user_id=token_response["data"].user_id,
            goods_id=item.goodsId
        )
        if exists:
            return {"resultCode": 400, "message": "商品已在购物车", "data": None}
            
        await Cart.create(
            user_id=token_response["data"].user_id,
            goods_id=item.goodsId,
            goods_count=item.goodsCount
        )
        return {"resultCode": 200, "message": "添加成功", "data": None}
    except Exception as e:
        return {"resultCode": 500, "message": f"添加失败: {str(e)}", "data": None}

@router.put("/shop-cart")
async def modify_cart(item: CartItem, request: Request):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    try:
        # 根据用户id和购物车项id获取购物车信息
        cart = await Cart.get(
            user_id=token_response["data"].user_id,
            car_id=item.cartItemId
        )
        # 确保商品数量是整数
        cart.goods_count = int(item.goodsCount)
        # 保存修改后的购物车信息
        await cart.save()
        # 返回修改成功信息
        return {"resultCode": 200, "message": "修改成功", "data": None}
    except DoesNotExist:
        # 如果购物车商品不存在，返回错误信息
        return {"resultCode": 404, "message": "购物车商品不存在", "data": None}
    except Exception as e:
        # 如果修改失败，返回错误信息
        return {"resultCode": 500, "message": f"修改失败: {str(e)}", "data": None}

@router.delete("/shop-cart/{id}")
# 异步删除购物车
async def delete_cart(id: int, request: Request):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 删除购物车中对应id的商品
    await Cart.filter(
        user_id=token_response["data"].user_id,
        car_id=id  # 修改为car_id
    ).delete()
    # 返回删除成功的消息
    return {"resultCode": 200, "message": "删除成功", "data": None}

@router.get("/shop-cart/settle")
# 定义一个异步函数，用于获取结算购物车
async def get_settle_cart(cartItemIds: str, request: Request):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response

    # 将ids字符串转换为id列表
    id_list = [int(id) for id in cartItemIds.split(',')]
    # 从数据库中获取购物车信息
    carts = await Cart.filter(
        user_id=token_response["data"].user_id,
        car_id__in=id_list  # 修改为car_id
    ).prefetch_related('goods')
    # 返回购物车信息
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": [{
            "cartItemId": cart.car_id,  # 修改为car_id
            "goodsId": cart.goods_id,
            "goodsCount": cart.goods_count,
            "goodsName": cart.goods.goodsName,
            "goodsCoverImg": cart.goods.goodsCoverImg,
            "sellingPrice": float(cart.goods.sellingPrice)
        } for cart in carts]   }