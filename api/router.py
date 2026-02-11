from fastapi import FastAPI, APIRouter

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from api import good, user,home,cart,address,order
app = FastAPI()

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(cart.router, tags=["购物车接口"])
api_router.include_router(good.router,tags=["商品接口"])
api_router.include_router(user.router, prefix='/user', tags=["用户接口"])
api_router.include_router(order.router, tags=["订单接口"])
api_router.include_router(home.router,tags=["主页接口"])
api_router.include_router(address.router, tags=["地址接口"])



app.include_router(api_router)
