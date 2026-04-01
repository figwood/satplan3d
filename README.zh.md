# SatPlan3D API

SatPlan3D 是一个面向卫星规划场景的 FastAPI 后端服务。它将用户认证、卫星与载荷管理、基于 TLE 的轨道传播、预计算轨迹生成、观测机会搜索以及订单管理整合到一个基于 MySQL 的 API 服务中。

这个仓库不是一个通用的 FastAPI 模板，而是一个偏业务化的卫星规划后端。如果你正在对接前端系统，或者希望围绕对地观测规划构建自动化流程，这个项目提供了核心后端能力。

## 项目亮点

- 基于 JWT 的身份认证，写操作支持管理员权限控制。
- 支持通过 TLE 数据注册卫星。
- 在 TLE 更新后自动预计算一周的轨迹和传感器扫幅路径。
- 轨迹查询优先读取预计算数据，缺失时可回退到实时轨道计算。
- 支持在给定地理范围内搜索可观测机会。
- 支持订单的创建、查询、详情查看、更新和删除。
- 提供 `init.sql` 用于初始化 MySQL 示例数据，并在启动时自动创建 ORM 中定义的表。

## 当前 API 范围

应用目前包含以下功能模块：

- **认证**
  - `POST /api/login`
  - `POST /change-password`
- **卫星与 TLE 管理**
  - `GET /api/satellite/list`
  - `POST /api/satellite`
  - `PUT /api/satellite/{noard_id}`
  - `PUT /api/tle`
- **轨迹与传感器路径**
  - `GET /api/track-points`
  - `GET /api/path-points`
- **覆盖与排程**
  - `GET /api/coverage`
  - `POST /api/schedule`
- **订单**
  - `GET /api/order/list`
  - `POST /api/order`
  - `GET /api/order/{order_id}/info`
  - `PUT /api/order/{order_id}`
  - `DELETE /api/order/{order_id}`

服务启动后，可以通过 FastAPI 自动生成的接口文档进行查看和调试：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## 项目结构

```text
satplan3d
├── app
│   ├── main.py                 # FastAPI 入口和路由注册
│   ├── database.py             # SQLAlchemy 引擎和会话配置
│   ├── models.py               # ORM 模型定义
│   ├── dependencies.py         # 认证和权限依赖
│   ├── security.py             # 密码哈希和 JWT 工具
│   ├── routers
│   │   ├── auth.py             # 登录和修改密码
│   │   ├── satellites.py       # 卫星、TLE 和传感器相关操作
│   │   ├── tracks.py           # 轨迹与路径查询
│   │   ├── coverage.py         # 覆盖计算接口骨架
│   │   ├── schedule.py         # 观测机会搜索
│   │   └── orders.py           # 订单增删改查
│   ├── schemas
│   │   └── base.py             # Pydantic 请求和响应模型
│   └── utils
│       └── coordinate_transform.py
├── init.sql                    # MySQL 示例结构和种子数据
├── requirements.txt            # Python 依赖
├── Dockerfile                  # 容器构建文件
├── README.md                   # 英文文档
└── README.zh.md                # 中文文档
```

## 技术栈

- **FastAPI**：提供 Web API 和 OpenAPI 文档。
- **SQLAlchemy**：负责 ORM 和数据库会话管理。
- **MySQL**：使用 `mysql-connector-python` 作为数据库驱动。
- **pyorbital**：用于基于 TLE 的轨道传播计算。
- **NumPy** 和 **SciPy**：提供数值计算支持。
- **python-jose** 和 **passlib**：用于 JWT 认证和密码哈希。

## 快速开始

### 1. 克隆仓库

```bash
git clone <repository-url>
cd satplan3d
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate
```

Windows 下：

```bash
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置数据库连接

在项目根目录创建 `.env` 文件：

```env
DB_USER=root
DB_PASSWORD=123456
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=satplan3d
```

`app/database.py` 会读取这些变量并拼接 SQLAlchemy 连接串。

### 5. 初始化数据库

你可以先将仓库提供的 `init.sql` 导入 MySQL，以初始化示例表结构和测试数据。

示例：

```bash
mysql -u root -p satplan3d < init.sql
```

应用启动时还会执行 `models.Base.metadata.create_all(bind=engine)`，自动补齐 ORM 中定义但数据库尚不存在的表。

### 6. 启动服务

```bash
uvicorn app.main:app --reload
```

### 7. 验证服务

- API 根路径：`http://127.0.0.1:8000/api`
- Swagger UI：`http://127.0.0.1:8000/docs`

## 认证模型

- `POST /api/login` 返回 Bearer Token。
- 卫星创建、TLE 更新等受保护写操作需要携带有效 JWT。
- OAuth2 Bearer Token 的提取逻辑定义在 `app/dependencies.py` 中。

当前 JWT 相关配置，例如 `SECRET_KEY` 和 `ALGORITHM`，仍然直接定义在 `app/security.py` 中，而不是从环境变量加载。

## 典型规划流程

一个典型的后端处理流程如下：

1. 通过 TLE 数据导入或创建卫星。
2. 将解析后的 TLE 持久化到数据库。
3. 以 20 秒步长预计算一周的轨迹点和传感器路径。
4. 按时间窗口查询轨迹点或传感器路径。
5. 在目标区域内搜索可观测机会。
6. 将选定的观测机会保存为规划订单。

这种设计使常用查询场景可以直接命中预计算结果，同时在缓存轨迹缺失时仍然可以通过实时轨道传播提供结果。

## 开发说明

- 路由注册位于 `app/main.py`。
- 公共请求和响应模型定义在 `app/schemas/base.py`。
- 数据库实体定义在 `app/models.py`。
- 坐标相关计算逻辑位于 `app/utils/coordinate_transform.py`。
- 日志基于 Python 标准库 `logging` 模块配置。

## 已知缺口

- `GET /api/coverage` 目前仍是占位实现，返回空列表。
- 一些本应放在环境变量中的配置，当前仍硬编码在 `app/security.py` 中。
- 仓库中没有迁移工具配置，当前数据库结构演进主要依赖手工维护。
- 仓库暂未包含自动化测试。

## 常见问题

### 如何添加新路由？

在 `app/routers` 下新增 router 模块，并在 `app/main.py` 中注册。

### 轨迹是如何生成的？

在创建或更新 TLE 后，服务会以 20 秒为步长预计算一周的轨迹点和传感器路径。

### 轨迹查询是实时计算的吗？

是的。`GET /api/track-points` 会优先查询数据库中的预计算轨迹；如果没有命中，就回退到实时轨道计算。

### 这个项目可以直接用于生产吗？

当前已经具备可用的后端功能，但在生产环境中仍建议补齐配置管理、数据库迁移、测试覆盖和未完成接口等方面的能力。