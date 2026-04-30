# FastAPI 电商后端

一个基于 FastAPI 构建的电商后端服务，提供完整的电商功能接口。

## 功能特性

- 用户管理（注册、登录、个人信息）
- 商品管理（商品列表、详情、搜索）
- 购物车功能
- 收货地址管理
- 订单管理（下单、支付、取消）
- 轮播图展示

## 技术栈

- **Web 框架**：FastAPI
- **数据库 ORM**：Tortoise-ORM
- **数据库**：MySQL
- **身份认证**：JWT

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的配置
   ```

3. 运行项目：
   ```bash
   python main.py
   ```

4. 访问接口文档：
   - Swagger UI: http://localhost:1090/docs
   - ReDoc: http://localhost:1090/redoc
