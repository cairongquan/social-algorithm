# Social Algorithm Service

Python3 后台服务基础框架，基于 FastAPI。

## 快速开始

### 1. 创建虚拟环境

```bash
cd service
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 根据需要编辑 .env 文件
```

### 4. 启动服务

```bash
python app/main.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- API文档：http://localhost:8000/api/v1/docs
- ReDoc：http://localhost:8000/api/v1/redoc

## 项目结构

```
service/
├── app/
│   ├── api/v1/          # API路由
│   ├── core/            # 配置和核心功能
│   ├── models/          # Pydantic模型
│   ├── services/        # 业务逻辑
│   └── main.py          # 应用入口
├── tests/               # 测试文件
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量示例
└── README.md
```

## 测试

```bash
pytest
pytest tests/test_api.py::test_health_check  # 运行单个测试
```
