from fastapi import FastAPI, HTTPException
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from muban.muban import Goods


router = APIRouter() 

class ProductListResponse(BaseModel):
    # 定义响应模型字段
    id: int
    name: str
    price: float
class GoodsDetail(BaseModel):
    id: int  # 修改字段名
    goods_name: str  # 修改字段名
    selling_price: float  # 修改字段名
    detail_content: Optional[str] = None
    goods_detail_content: Optional[str] = None

    class Config:
        from_attributes = True



@router.get("/goods/detail/{goods_id}")
async def get_goods_detail(goods_id: int):
    goods = await Goods.get_or_none(goodsId=goods_id)
    if goods is None:
        return {
            "resultCode": 404,
            "message": "商品不存在", 
            "data": None
        }
    
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
            "goodsId": goods.goodsId,
            "goodsName": goods.goodsName,
            "goodsIntro": goods.goodsIntro if hasattr(goods, 'goodsIntro') else "",
            "goodsCoverImg": goods.goodsCoverImg,
            "sellingPrice": float(goods.sellingPrice),
            "goodsCarouselList": [goods.goodsCoverImg],
            "goodsDetailContent":goods.goods_detail_images,
            "ISBN": goods.ISBN if hasattr(goods, 'ISBN') else "",
            "author": goods.author if hasattr(goods, 'author') else "",
            "press": goods.press if hasattr(goods, 'press') else ""
        }
    }


@router.get("/search")
async def search_products(
    pageNumber: int = Query(1, gt=0, description="当前页码"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    orderBy: Optional[str] = Query(None, description="排序方式")
):
    """
    商品搜索接口
    根据商品名称搜索商品
    """
    page_size = 10
    offset = (pageNumber - 1) * page_size
    
    # 构建查询条件
    query = Goods.all()
    if keyword:
        query = query.filter(goodsName__icontains=keyword)
    
    # 处理排序
    if orderBy == "price_asc":
        query = query.order_by("sellingPrice")
    elif orderBy == "price_desc":
        query = query.order_by("-sellingPrice")
    
    # 获取总数和分页数据
    total = await query.count()
    goods_list = await query.offset(offset).limit(page_size)
    
    # 格式化返回数据
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
            "list": [{
                "goodsId": goods.goodsId,
                "goodsName": goods.goodsName,
                "goodsCoverImg": goods.goodsCoverImg,
                "sellingPrice": float(goods.sellingPrice)
            } for goods in goods_list],
            "totalPage": (total + page_size - 1) // page_size,
            "totalCount": total
        }
    }





    