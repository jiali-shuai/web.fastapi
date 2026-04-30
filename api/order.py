from fastapi import APIRouter,Request,Query
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.jwt import verify_and_get_token_data
from muban.muban import Order, OrderItem,Cart

router = APIRouter()

class OrderStatus:
    # 未支付状态
    UNPAID = 0
    # 已支付状态
    PAID = 1
    # 已发货状态
    SHIPPED = 2
    # 已完成状态
    COMPLETED = 3
    # 已取消状态
    CANCELLED = 4

class OrderItemCreate(BaseModel):
    goodsId: int
    goodsCount: int
    goodsName: str
    goodsCoverImg: str
    sellingPrice: float

class OrderCreate(BaseModel):
    addressId: int
    cartItemIds: List[int]
    totalPrice: Optional[float] = None
    items: Optional[List[OrderItemCreate]] = None


def get_order_status_string(status: int) -> str:
    status_map = {
        0: "待付款",
        1: "已付款",
        2: "已发货",
        3: "已完成",
        4: "已取消"
    }
    return status_map.get(status, "未知状态")


@router.post("/saveOrder")
async def create_order(
    request: Request,
    order_data: OrderCreate
):
    # 获取请求头中的token
    token = request.headers.get("token")
    token_response = verify_and_get_token_data(token)
    if token_response["resultCode"] != 200:
        return token_response
    
    # 验证必填字段
    if not order_data.cartItemIds:
        return {"resultCode": 400, "message": "购物车项不能为空", "data": None}
        
    # 获取购物车项信息并验证
    cart_items = await Cart.filter(
        user_id=token_response['data'].user_id,
        car_id__in=order_data.cartItemIds
    ).prefetch_related('goods')
    
    if len(cart_items) != len(order_data.cartItemIds):
        return {"resultCode": 400, "message": "部分购物车项不存在", "data": None}
        
    # 计算总价并设置订单项数据
    total_price = sum(item.goods.sellingPrice * item.goods_count for item in cart_items)
    order_data.items = [
        OrderItemCreate(
            goodsId=item.goods_id,
            goodsCount=item.goods_count,
            goodsName=item.goods.goodsName,
            goodsCoverImg=item.goods.goodsCoverImg,
            sellingPrice=item.goods.sellingPrice
        ) for item in cart_items
    ]
    order_data.totalPrice = total_price
        
    try:
        # 生成订单号
        order_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{int(token_response['data'].user_id):04d}"
        
        # 创建订单
        order = await Order.create(
            order_no=order_no,
            user_id=token_response['data'].user_id,
            total_price=order_data.totalPrice,
            order_status=OrderStatus.UNPAID,
            create_time=datetime.now()
        )
        
        for item in order_data.items:
            await OrderItem.create(
                order_id=order.order_id,
                goods_id=item.goodsId,
                goods_count=item.goodsCount,
                goods_name=item.goodsName,
                goods_cover_img=item.goodsCoverImg,
                selling_price=item.sellingPrice
            )
        
        # 删除购物车中的商品
        await Cart.filter(
            user_id=token_response['data'].user_id,
            car_id__in=order_data.cartItemIds
        ).delete()
        
        return {
            "resultCode": 200,
            "message": "订单创建成功",
            "data": order_no
        }
    except Exception as e:
        return {"resultCode": 500, "message": f"订单创建失败: {str(e)}", "data": None}

@router.get("/order")
async def get_order_list(
    request: Request,
    status: Optional[str] = None,
    pageSize: int = 10,  # 默认每页10条
    currPage: int = 1    # 默认第一页
):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response
    
    # 构建基础查询
    query = Order.filter(user_id=token_response['data'].user_id)
    
    # 根据status参数过滤订单
    if status is not None and status != '':  # 只有当status有值时才过滤
        query = query.filter(order_status=int(status))
    
    # 获取总订单数
    total_count = await query.count()
    
    # 计算总页数
    total_page = (total_count + pageSize - 1) // pageSize
    
    # 查询当前页数据
    orders = await query\
        .order_by("-create_time")\
        .offset((currPage - 1) * pageSize)\
        .limit(pageSize)\
        .prefetch_related("items")
    
    # 返回订单列表
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
            "totalCount": total_count,
            "pageSize": pageSize,
            "totalPage": total_page,
            "currPage": currPage,
            "list": [
                {
                    "orderId": order.order_id,
                    "orderNo": order.order_no,
                    "totalPrice": order.total_price,
                    "payType": getattr(order, 'pay_type', 0),
                    "orderStatus": order.order_status,
                    "orderStatusString": get_order_status_string(order.order_status),
                    "createTime": order.create_time,
                    "newBeeMallOrderItemVOS": [
                        {
                            "goodsId": item.goods_id,
                            "goodsCount": item.goods_count,
                            "goodsName": item.goods_name,
                            "goodsCoverImg": item.goods_cover_img,
                            "sellingPrice": item.selling_price
                        }
                        for item in order.items
                    ]
                }
                for order in orders
            ]
        }
    }

@router.get("/order/{order_no}")
# 定义一个异步函数，用于获取订单详情
async def get_order_detail(
    # 订单号
    order_no: str,
    # 请求对象
    request: Request
):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response
    # 根据订单号和用户id查询订单
    order = await Order.get_or_none(
        order_no=order_no,
        user_id=token_response['data'].user_id
    ).prefetch_related("items")
    
    # 如果订单不存在，返回错误信息
    if not order:
        return {"resultCode": 404, "message": "订单不存在", "data": None}
    
    # 返回订单详情
    return {
        "resultCode": 200,
        "message": "成功",
        "data": {
            "orderNo": order.order_no,
            "totalPrice": order.total_price,
            "payStatus": order.pay_status,
            "payType": order.pay_type,
            "payTypeString": "微信支付" if order.pay_type == 2 else "支付宝" if order.pay_type == 1 else "银行卡",
            "payTime": order.pay_time,
            "orderStatus": order.order_status,
            "orderStatusString": get_order_status_string(order.order_status),
            "createTime": order.create_time,
            "newBeeMallOrderItemVOS": [
                {
                    "goodsId": item.goods_id,
                    "goodsCount": item.goods_count,
                    "goodsName": item.goods_name,
                    "goodsCoverImg": item.goods_cover_img,
                    "sellingPrice": item.selling_price
                }
                for item in order.items
            ]
        }
    }

@router.put("/order/{order_no}/cancel")
# 定义一个异步函数，用于取消订单
async def cancel_order(
    # 订单号
    order_no: str,
    # 请求对象
    request: Request
):
    # 获取请求头中的token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败
    if token_response["resultCode"] != 200:
        # 返回token验证结果
        return token_response
    # 根据订单号和用户id获取订单
    order = await Order.get_or_none(
        order_no=order_no,
        user_id=token_response['data'].user_id
    )
    
    # 如果订单不存在
    if not order:
        # 返回订单不存在的错误信息
        return {"resultCode": 404, "message": "订单不存在", "data": None}
    
    # 如果订单状态不是未支付
    if order.order_status != OrderStatus.UNPAID:
        # 返回订单状态不可取消的错误信息
        return {"resultCode": 400, "message": "当前订单状态不可取消", "data": None}
    
    # 将订单状态改为已取消
    order.order_status = OrderStatus.CANCELLED
    # 保存订单
    await order.save()
    
    # 返回订单取消成功的消息
    return {"resultCode": 200, "message": "订单取消成功", "data": None}

@router.put("/order/{order_no}/finish")
# 定义一个异步函数，用于确认订单
async def confirm_order(
    order_no: str,  # 订单号
    request: Request  # 请求对象
):
    # 从请求头中获取token
    token = request.headers.get("token")
    # 验证token并获取token数据
    token_response = verify_and_get_token_data(token)
    # 如果token验证失败，返回错误信息
    if token_response["resultCode"] != 200:
        return token_response
    # 根据订单号和用户id获取订单信息
    order = await Order.get_or_none(
        order_no=order_no,
        user_id=token_response['data'].user_id
    )
    
    # 如果订单不存在，返回错误信息
    if not order:
        return {"resultCode": 404, "message": "订单不存在", "data": None}
    
    # 如果订单状态不是已发货，返回错误信息
    if order.order_status != OrderStatus.SHIPPED:
        return {"resultCode": 400, "message": "自动确认无需手动", "data": None}
    
    # 将订单状态改为已完成
    order.order_status = OrderStatus.COMPLETED
    # 保存订单信息
    await order.save()
    
    return {"resultCode": 200, "message": "确认收货成功", "data": None}

@router.get("/paySuccess")
async def pay_order(
    request: Request,
    orderNo: str = Query(...),
    payType: int = Query(default=2)
):
    token = request.headers.get("token")
    token_response = verify_and_get_token_data(token)
    if token_response["resultCode"] != 200:
        return token_response

    order = await Order.get_or_none(
        order_no=orderNo,
        user_id=token_response['data'].user_id
    ).prefetch_related("items__goods")
    
    if not order:
        return {"resultCode": 404, "message": "订单不存在", "data": None}
    
    if order.order_status != OrderStatus.UNPAID:
        return {"resultCode": 400, "message": "当前订单状态不可支付", "data": None}
    
    # 检查所有商品库存是否足够
    for item in order.items:
        goods = item.goods
        if goods.stock < item.goods_count:
            return {
                "resultCode": 400,
                "message": f"商品 {goods.goodsName} 库存不足",
                "data": None
            }
    
    # 减少商品库存
    for item in order.items:
        goods = item.goods
        goods.stock -= item.goods_count
        await goods.save()
    
    # 更新订单状态
    order.order_status = OrderStatus.PAID
    order.pay_type = payType
    order.pay_time = datetime.now()
    await order.save()
    
    return {
        "resultCode": 200,
        "message": "支付成功",
        "data": {
            "orderNo": orderNo,
            "payType": payType
        }
    }