from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from muban.muban import Carousel, Goods

router = APIRouter()
class IndexInfosResponse(BaseModel):
    carousels: List[dict]
    hotGoodses: List[dict]

    class Config:
        from_attributes = True
class BaseResponse(BaseModel):
    # 定义一个基础响应类，继承自BaseModel
    resultCode: int
    # 定义一个整型属性，表示响应结果码
    message: str
    # 定义一个字符串属性，表示响应消息
    data: IndexInfosResponse
@router.get("/index-infos", response_model=BaseResponse)
async def get_index_infos():
    carousels = await Carousel.all().values()
    hot_goods = await Goods.all().limit(8).values()
    
    return {
        "resultCode": 200,
        "message": "SUCCESS",
        "data": {
            "carousels": [{
                "carouselUrl": item["carouselUrl"],
                "redirectUrl": item.get("redirectUrl", "")
            } for item in carousels],
            "hotGoodses": [{
                "goodsId": item["goodsId"],
                "goodsName": item["goodsName"],
                "goodsCoverImg": item["goodsCoverImg"],
                "sellingPrice": float(item["sellingPrice"])
            } for item in hot_goods]
        }
    }

    