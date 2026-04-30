# Social Algorithm - 文章管理系统

## 项目结构

```
social-algorithm/
├── service/              # Python后端 (FastAPI + SQLite)
│   ├── app/
│   │   ├── api/v1/      # API路由（认证、文章、标签、上传）
│   │   ├── core/        # 配置、数据库、安全
│   │   ├── models/      # Pydantic模型
│   │   ├── services/    # 业务逻辑
│   │   └── main.py     # 入口文件
│   ├── uploads/         # 上传文件存储
│   ├── requirements.txt
│   └── run.py          # 启动脚本
│
└── app/                 # Vue3前端
    ├── src/
    │   ├── types/       # TypeScript类型
    │   ├── api/         # API调用
    │   ├── stores/      # Pinia状态管理
    │   ├── composables/ # 组合式函数
    │   ├── components/  # Vue组件
    │   ├── views/       # 页面视图
    │   ├── router/      # 路由配置
    │   ├── main.ts      # 入口
    │   └── App.vue     # 根组件
    ├── package.json
    └── vite.config.ts
```

## 快速启动

### 1. 启动后端

```bash
cd service
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run.py
```

后端启动后访问：http://localhost:8000/api/v1/docs

### 2. 启动前端

```bash
cd app
npm install
npm run dev
```

前端启动后访问：http://localhost:5173

## 功能说明

### 用户认证
- 注册：/register
- 登录：/login
- 使用JWT token认证

### 文章管理
- 文章列表：首页
- 创建文章：/articles/create
- 编辑文章：/articles/:id/edit
- 删除文章：文章卡片上的删除按钮
- 文章内容使用TinyMCE富文本编辑器
- 文章以base64存储到SQLite

### 标签管理
- 标签列表：/tags
- 创建标签、编辑标签、删除标签
- 删除标签时会清除关联文章的所有标签

### 图片上传
- 在TinyMCE编辑器中可直接上传图片
- 图片保存到service/uploads/目录

## API端点

### 认证
- POST /api/v1/auth/register - 注册
- POST /api/v1/auth/login - 登录

### 文章
- GET /api/v1/articles - 列表
- POST /api/v1/articles - 创建（需认证）
- GET /api/v1/articles/:id - 详情
- PUT /api/v1/articles/:id - 更新（需认证）
- DELETE /api/v1/articles/:id - 删除（需认证）

### 标签
- GET /api/v1/tags - 列表
- POST /api/v1/tags - 创建（需认证）
- PUT /api/v1/tags/:id - 更新（需认证）
- DELETE /api/v1/tags/:id - 删除（需认证）

### 上传
- POST /api/v1/uploads/upload - 上传图片（需认证）
- GET /api/v1/uploads/:filename - 获取图片

## 技术栈

**后端：**
- FastAPI - Web框架
- SQLite3 - 数据库
- Pydantic - 数据验证
- PyJWT - JWT认证
- Uvicorn - ASGI服务器

**前端：**
- Vue 3 - 渐进式框架
- TypeScript - 类型安全
- Vite 5 - 构建工具（兼容Node 18）
- Pinia - 状态管理
- Vue Router - 路由
- TinyMCE - 富文本编辑器
- Axios - HTTP客户端
# social-algorithm
