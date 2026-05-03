# Social Algorithm

一个基于 `FastAPI + SQLite + Vue 3` 的社交化文章系统，支持用户认证、文章发布、标签管理、图片上传、点赞评论、关注关系、推荐排序与管理员分析能力。

## 功能概览

- 用户模块：注册、登录、个人信息查询与更新、头像上传
- 内容模块：文章增删改查、标签绑定、广场流推荐
- 互动模块：点赞、评论、关注、浏览行为记录、停留时长上报
- 推荐模块：基于行为与热度的混合排序，支持算法参数调优
- 管理模块：算法参数管理、离线实验报告导出、社交拓扑图、停留指标统计

## 项目结构

```text
social-algorithm/
├── service/                    # Python 后端（FastAPI + SQLite）
│   ├── app/
│   │   ├── api/v1/             # API 路由（auth/articles/tags/uploads/social/topology/admin）
│   │   ├── core/               # 配置、数据库、安全
│   │   ├── models/             # Pydantic 模型（示例）
│   │   ├── services/           # 推荐与业务服务
│   │   └── main.py             # FastAPI 应用入口
│   ├── reports/                # 管理端导出的实验报告（CSV/MD/PNG）
│   ├── uploads/                # 上传文件存储目录
│   ├── requirements.txt
│   └── run.py                  # 后端启动脚本
│
└── app/                        # Vue 3 前端（Vite + TypeScript）
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## 快速启动

### 1) 启动后端

在仓库根目录执行：

```bash
cd service
```

创建虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境：

- Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

- Windows (CMD)

```bat
.venv\Scripts\activate.bat
```

- macOS / Linux

```bash
source .venv/bin/activate
```

安装依赖并启动：

```bash
pip install -r requirements.txt
python run.py
```

后端地址：`http://localhost:8000`

接口文档：`http://localhost:8000/api/v1/docs`

### 2) 启动前端

在仓库根目录执行：

```bash
cd app
npm install
npm run dev
```

前端地址：`http://localhost:5173`

## 默认账号

系统初始化会自动创建管理员账号：

- 用户名：`admin`
- 密码：`admin`

建议仅用于本地开发演示，生产环境请立即修改。

## 核心 API 概览

以下为主要接口分组（完整参数请以 Swagger 文档为准）：

### Auth

- `POST /api/v1/auth/register`：注册
- `POST /api/v1/auth/login`：登录
- `GET /api/v1/auth/me`：当前用户资料
- `PUT /api/v1/auth/me`：更新用户名/密码
- `POST /api/v1/auth/avatar`：上传头像

### Articles

- `GET /api/v1/articles`：文章列表
- `POST /api/v1/articles`：创建文章
- `GET /api/v1/articles/{article_id}`：文章详情
- `PUT /api/v1/articles/{article_id}`：更新文章
- `DELETE /api/v1/articles/{article_id}`：删除文章
- `GET /api/v1/articles/square`：推荐广场
- `POST /api/v1/articles/{article_id}/view`：记录浏览
- `POST /api/v1/articles/{article_id}/dwell`：上报停留时长
- `POST /api/v1/articles/{article_id}/like`：点赞/取消点赞
- `GET /api/v1/articles/{article_id}/comments`：评论列表
- `POST /api/v1/articles/{article_id}/comments`：发表评论
- `DELETE /api/v1/articles/{article_id}/comments/{comment_id}`：删除评论

### Tags

- `GET /api/v1/tags`：标签列表
- `POST /api/v1/tags`：创建标签
- `PUT /api/v1/tags/{tag_id}`：更新标签
- `DELETE /api/v1/tags/{tag_id}`：删除标签
- `GET /api/v1/tags/preview/push-users?name=...`：标签推送用户预览

### Uploads

- `POST /api/v1/uploads/upload`：上传文件
- `GET /api/v1/uploads/{filename}`：获取文件
- `GET /api/v1/uploads`：当前用户上传列表

### Social

- `GET /api/v1/social/users`：用户列表（含是否已关注）
- `POST /api/v1/social/follow/{target_user_id}`：关注/取消关注

### Topology

- `GET /api/v1/topology/overview`：关系概览
- `GET /api/v1/topology/graph`：社交拓扑图数据

### Admin

- `GET /api/v1/admin/algorithm-settings`：获取算法参数（管理员）
- `GET /api/v1/admin/algorithm-settings/current`：获取当前参数（登录用户）
- `PUT /api/v1/admin/algorithm-settings`：更新算法参数（管理员）
- `POST /api/v1/admin/algorithm-settings/reset`：重置算法参数（管理员）
- `POST /api/v1/admin/experiment-report`：生成离线实验报告（管理员）
- `GET /api/v1/admin/experiment-report/files/{filename}`：下载报告文件（管理员）
- `GET /api/v1/admin/metrics/dwell`：停留指标统计（管理员）

## 技术栈

后端：

- `FastAPI`
- `SQLite3`
- `Pydantic`
- `PyJWT`
- `Uvicorn`
- `Pillow`（实验图表生成）

前端：

- `Vue 3`
- `TypeScript`
- `Vite`
- `Pinia`
- `Vue Router`
- `Axios`
- `TinyMCE`

## 开发说明

- 数据库文件默认位于 `service/social_algorithm.db`
- 首次启动会自动执行数据库初始化
- 推荐算法参数存储在 `algorithm_settings` 表
- 如需调试接口，优先使用 `http://localhost:8000/api/v1/docs`
