# FastAPI 项目说明

本项目是一个基于 FastAPI 的 Web 应用，连接到 MySQL 数据库，提供用户认证、权限管理以及卫星轨道计算功能。以下是项目的详细说明和开发指南。

## 项目结构

```
satplan3d
├── app
│   ├── main.py          # FastAPI 应用的入口文件
│   ├── database.py      # 数据库连接配置
│   ├── models.py        # 数据库模型定义
│   ├── routers          # 路由模块目录
│   │   ├── auth.py      # 用户认证相关路由
│   │   ├── orbit.py     # 卫星轨道计算相关路由
│   │   └── ...          # 其他路由模块
│   ├── dependencies.py  # 依赖注入模块
│   ├── security.py      # 安全相关功能（如密码加密、Token 生成）
│   └── orbit_calculator # 卫星轨道计算核心逻辑
├── .env                 # 环境变量配置文件
├── requirements.txt     # 项目依赖
├── Dockerfile           # Docker 镜像构建文件
└── README.md            # 项目文档
```

## 快速开始

1. **克隆代码库：**
   ```bash
   git clone <repository-url>
   cd satplan3d
   ```

2. **创建虚拟环境并安装依赖：**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows 使用 `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **配置环境变量：**
   在项目根目录创建 `.env` 文件，内容如下：
   ```
   DB_USER=root
   DB_PASSWORD=123456
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ```

4. **运行应用：**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **访问应用：**
   打开浏览器访问 `http://127.0.0.1:8000`。

## 核心功能

### 卫星轨道计算

本项目实现了卫星轨道计算功能，支持以下特性：
- 基于两行轨道元素（TLE）进行轨道预测。
- 提供卫星位置和速度的精确计算。
- 支持多种时间范围的轨道模拟和可视化。

卫星轨道计算的核心逻辑位于 `app/orbit_calculator` 目录下，使用了专业的轨道力学库和数学计算工具，确保计算的精度和性能。

## 技术栈说明

### 核心技术栈

- **FastAPI**：用于构建高性能的 Web API，支持异步操作，开发效率高。
- **SQLAlchemy**：用于数据库操作，支持 ORM 和原生 SQL 查询。
- **pyorbital**：用于卫星轨道计算，支持基于 TLE 的轨道预测。

### 选用原因

1. **FastAPI**：
   - 提供了现代化的开发体验，支持自动生成 API 文档。
   - 异步支持使其在高并发场景下表现优异。

2. **pyorbital**：
   - 专业的卫星轨道计算库，支持基于 TLE 的轨道预测。
   - 提供高精度的卫星位置和速度计算，适用于实际应用场景。

通过以上技术栈的组合，本项目能够高效、准确地完成卫星轨道计算任务，同时提供良好的扩展性和开发体验。

## 开发指南

- **数据库配置：** 数据库连接配置位于 `app/database.py`，可根据需要修改。
- **路由模块：** 所有路由定义在 `app/routers` 目录下，可根据需求添加新模块。
- **依赖注入：** 公共依赖定义在 `app/dependencies.py`，如用户认证和权限检查。
- **日志记录：** 使用 Python 的 `logging` 模块记录调试信息，日志配置可在 `app` 目录下添加。

## 注意事项

- 确保 MySQL 数据库已启动，并使用 `.env` 文件中提供的用户名和密码可以正常连接。
- 使用 `Dockerfile` 构建镜像时，请确保 `requirements.txt` 和代码文件完整无误。
- 更多信息请参考 [FastAPI 官方文档](https://fastapi.tiangolo.com/)。

## 常见问题

1. **如何添加新路由？**
   在 `app/routers` 目录下创建新的 Python 文件，定义路由后在 `app/main.py` 中引入即可。

2. **如何修改 Token 有效期？**
   在 `app/routers/auth.py` 中修改 `timedelta` 的值即可调整 Token 的过期时间。

3. **如何扩展数据库模型？**
   在 `app/models.py` 中定义新的模型类，并运行 Alembic 迁移脚本更新数据库。