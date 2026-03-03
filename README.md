# SiC Data Processing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

碳化硅JBS二极管试验数据一体化处理平台 - 整合5个数据处理模块的全栈Web应用

## 目录

- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [故障排除](#故障排除)

---

## 功能特性

### 五大处理模块

| 模块 | 功能描述 | 输入格式 | 输出格式 |
|------|----------|----------|----------|
| **参数检查数据处理** | Excel模板数据合并与智能匹配 | .xlsx/.xls | .xlsx |
| **变化率作图** | VF/BV/IR参数趋势图生成 | 数据输入/Excel | .png/.xlsx |
| **应力数据曲线** | 80通道漏电流趋势可视化 | .xlsx | .png |
| **正态分布分析** | 统计分析与3-sigma异常值处理 | .xlsx | .png/.xlsx |
| **测试报告生成** | Word报告自动填充生成 | .docx + .xlsx | .docx |

### 核心特性

- 🚀 **异步任务处理** - Celery + Redis 后台任务队列，支持长时间运行任务
- 📊 **实时进度反馈** - WebSocket风格的任务状态轮询
- 🔒 **安全设计** - 非root容器、文件验证、路径安全
- 🌐 **中文字体支持** - 内置文泉驿字体，图表中文完美显示
- 📱 **响应式UI** - Ant Design 5.x 蓝色主题，支持多分辨率

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 18)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │参数检查 │ │变化率   │ │应力曲线 │ │正态分布 │ │报告生成│ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│              TanStack Query + Zustand + ECharts              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    REST API Routes                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Async Task Layer (Celery)                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Processing Modules (5 Processors)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │PostgreSQL│        │  Redis   │        │  本地    │
    │  (Jobs)  │        │(Queue)   │        │ Storage  │
    └──────────┘        └──────────┘        └──────────┘
```

### 技术栈详情

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | React + TypeScript | 18.x |
| | Ant Design | 5.x |
| | TanStack Query | 5.x |
| | Vite | 5.x |
| **后端** | Python | 3.11 |
| | FastAPI | 0.109+ |
| | Celery | 5.3+ |
| | pandas, numpy, matplotlib | Latest |
| **数据库** | PostgreSQL | 15 |
| | Redis | 7 |
| **部署** | Docker + Docker Compose | Latest |

---

## 快速开始

### 前置条件

- [Docker](https://www.docker.com/get-started) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+
- 至少 8GB 可用内存

### 一键启动

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/sic-data-platform.git
cd sic-data-platform

# 2. 创建环境配置
cp .env.example .env
# 编辑 .env 设置安全的数据库密码

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端界面** | http://localhost:3000 | React Web应用 |
| **API文档** | http://localhost:8000/api/docs | Swagger UI |
| **健康检查** | http://localhost:8000/health | 服务状态 |

---

## 详细配置

### 环境变量

创建 `.env` 文件（从 `.env.example` 复制）：

```bash
# PostgreSQL 配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password  # 必须修改！
POSTGRES_DB=sic_platform

# 应用配置
DEBUG=false                              # 生产环境设为false
CORS_ORIGINS=http://localhost:3000       # 允许的前端域名

# Celery 配置
CELERY_CONCURRENCY=2                     # Worker并发数
```

### 资源限制

Docker Compose 已配置资源限制：

| 服务 | CPU | 内存 |
|------|-----|------|
| backend | 2核 | 4GB |
| worker | 4核 | 8GB |
| frontend | 0.5核 | 512MB |
| db | 1核 | 2GB |
| redis | 0.5核 | 2GB |

### 存储配置

文件存储在 `./storage/` 目录：

```
storage/
├── uploads/     # 上传的原始文件
│   └── {file_id}/
│       └── original_filename.xlsx
└── results/     # 处理结果文件
    └── {job_id}/
        ├── chart.png
        └── result.xlsx
```

---

## API文档

### 认证

当前版本无需认证，生产环境建议添加 JWT/API Key 认证。

### 主要端点

#### 参数检查处理

```http
POST /api/v1/parameter-check/upload
Content-Type: multipart/form-data

files: [Excel文件]
```

```http
POST /api/v1/parameter-check/process
Content-Type: application/json

{
  "input_directory": "/path/to/files",
  "output_directory": "/path/to/output",
  "file_ids": ["uuid1", "uuid2"]
}
```

#### 变化率作图

```http
POST /api/v1/trend-chart/vf
POST /api/v1/trend-chart/bv
POST /api/v1/trend-chart/ir
Content-Type: application/json

{
  "chart_type": "VF",
  "product_list": ["Product1", "Product2"],
  "time_labels": ["0h", "168h", "500h", "1000h"],
  "means": {
    "Product1": [1.5, 1.52, 1.55, 1.58],
    "Product2": [1.6, 1.62, 1.65, 1.68]
  },
  "stds": {
    "Product1": [0.01, 0.015, 0.02, 0.025],
    "Product2": [0.012, 0.017, 0.022, 0.027]
  }
}
```

#### 应力曲线分析

```http
POST /api/v1/stress-curve/analyze
Content-Type: application/json

{
  "file_id": "uuid",
  "time_start": 0,
  "time_end": 1000,
  "leakage_columns": "all",
  "show_legend": false,
  "smooth_data": true,
  "smooth_window": 5
}
```

#### 正态分布分析

```http
POST /api/v1/normal-distribution/analyze
Content-Type: application/json

{
  "file_id": "uuid",
  "params": ["VF", "IR", "BV"],
  "times": ["T0", "168h"],
  "enable_outlier_removal": true,
  "outlier_sigma": 3.0
}
```

#### 报告生成

```http
POST /api/v1/report/generate
Content-Type: application/json

{
  "template_id": "uuid",
  "data_file_id": "uuid",
  "report_type": "HTRB",
  "output_name": "report_20240101"
}
```

#### 任务状态查询

```http
GET /api/v1/jobs/{job_id}

Response:
{
  "job_id": "uuid",
  "job_type": "trend_chart_vf",
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "result": {
    "output_files": ["chart.png", "report.xlsx"]
  },
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:01:00"
}
```

```http
GET /api/v1/jobs/{job_id}/download

# 返回结果文件下载
```

---

## 开发指南

### 本地开发环境

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 启动 Celery Worker (新终端)
celery -A app.workers.celery_app worker --loglevel=info
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 项目结构

```
sic-data-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/      # API端点
│   │   │   │   ├── parameter_check.py
│   │   │   │   ├── trend_chart.py
│   │   │   │   ├── stress_curve.py
│   │   │   │   ├── normal_distribution.py
│   │   │   │   ├── report_generation.py
│   │   │   │   └── jobs.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── processors/     # 业务处理器
│   │   │   ├── processor_base.py
│   │   │   └── plot_base.py
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic模型
│   │   ├── services/
│   │   │   ├── file_service.py
│   │   │   └── job_service.py
│   │   ├── main.py
│   │   └── config.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   └── tasks/
│   │       └── processing_tasks.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Dockerfile.worker
├── frontend/
│   ├── src/
│   │   ├── api/                # API客户端
│   │   ├── components/
│   │   │   ├── common/         # 通用组件
│   │   │   └── layout/         # 布局组件
│   │   ├── views/              # 页面组件
│   │   ├── hooks/              # 自定义Hooks
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── storage/
│   ├── uploads/
│   └── results/
├── docker-compose.yml
├── .env.example
└── README.md
```

### 添加新模块

1. 创建处理器 `backend/app/core/processors/new_processor.py`:

```python
from app.core.processor_base import ProcessorBase

class NewProcessor(ProcessorBase):
    def process(self) -> dict:
        # 实现处理逻辑
        return {"output_files": [...]}
```

2. 创建API端点 `backend/app/api/endpoints/new_module.py`

3. 注册路由 `backend/app/api/router.py`

4. 创建前端页面 `frontend/src/views/NewModule.tsx`

---

## 部署指南

### 生产环境部署

#### 1. 安全配置

```bash
# 修改 .env
DEBUG=false
POSTGRES_PASSWORD=<强密码>
CORS_ORIGINS=https://your-domain.com
```

#### 2. 使用 HTTPS

建议使用 Nginx 反向代理配置 SSL：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. 数据备份

```bash
# PostgreSQL 备份
docker exec sic-db pg_dump -U postgres sic_platform > backup.sql

# Redis 备份
docker exec sic-redis redis-cli BGSAVE
```

#### 4. 日志管理

日志自动轮转配置在 `docker-compose.yml` 中：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 性能优化

1. **Worker 扩展**: 增加 `CELERY_CONCURRENCY` 或部署多个 Worker 容器
2. **Redis 内存**: 根据任务量调整 `maxmemory`
3. **数据库连接池**: 配置 SQLAlchemy 连接池参数

---

## 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 检查日志
docker-compose logs backend

# 常见原因：
# - 端口被占用：修改 docker-compose.yml 中的端口映射
# - 内存不足：增加 Docker 分配的内存
# - 环境变量未设置：检查 .env 文件
```

#### 2. 中文显示乱码

容器已预装文泉驿字体，如需使用其他字体：

```bash
# 在 backend/Dockerfile 中添加
RUN apt-get install -y fonts-your-font
```

并在 `.env` 中设置：
```
CHINESE_FONT_PATH=/path/to/font.ttf
```

#### 3. 任务卡在 pending 状态

```bash
# 检查 Worker 状态
docker-compose logs worker

# 重启 Worker
docker-compose restart worker
```

#### 4. 文件上传失败

- 检查文件大小（默认限制 50MB）
- 检查文件格式（支持 .xlsx, .xls, .docx）
- 检查 storage 目录权限

### 健康检查

```bash
# 检查所有服务状态
curl http://localhost:8000/health

# 预期响应
{
  "status": "healthy",
  "dependencies": {
    "redis": "connected",
    "storage": {"writable": true}
  }
}
```

---

## 许可证

[MIT License](LICENSE)

---

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 更新日志

### v1.0.0 (2024-01-01)

- 初始版本发布
- 实现5个数据处理模块
- Docker 容器化部署
- 响应式前端界面