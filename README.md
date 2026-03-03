# SiC Data Processing Platform

碳化硅JBS二极管试验数据一体化处理平台

## 功能模块

| 模块 | 描述 | 原始脚本 |
|-----|------|---------|
| 参数检查数据处理 | Excel模板数据合并与智能匹配 | `process_data.py` |
| 变化率作图 | VF/BV/IR参数趋势图生成 | `VF.py`, `BV.py`, `IR.PY` |
| 应力数据曲线 | 漏电流趋势可视化(80通道) | `YLSJ.py` |
| 正态分布分析 | 统计分析与正态分布图 | `JTCS.py` |
| 测试报告生成 | Word报告自动生成 | `update_report_perfect.py` |

## 技术栈

### 后端
- Python 3.11
- FastAPI
- Celery + Redis
- PostgreSQL
- pandas, numpy, matplotlib, openpyxl, scipy, python-docx

### 前端
- React 18 + TypeScript
- Ant Design 5.x
- TanStack Query
- Zustand
- ECharts

## 快速开始

### Docker部署 (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

服务地址:
- 前端: http://localhost:3000
- API文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

### 开发模式

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 启动Celery Worker (新终端)
celery -A app.workers.celery_app worker --loglevel=info
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 目录结构

```
sic-data-platform/
├── backend/
│   ├── app/
│   │   ├── api/           # API端点
│   │   ├── core/          # 核心处理器
│   │   ├── models/        # 数据模型
│   │   └── services/      # 服务层
│   ├── workers/           # Celery任务
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # API客户端
│   │   ├── components/    # 组件
│   │   └── views/         # 页面
│   └── package.json
├── storage/               # 文件存储
│   ├── uploads/
│   └── results/
└── docker-compose.yml
```

## API文档

启动服务后访问: http://localhost:8000/api/docs

### 主要端点

- `POST /api/v1/parameter-check/process` - 参数检查处理
- `POST /api/v1/trend-chart/vf` - VF趋势图
- `POST /api/v1/trend-chart/bv` - BV趋势图
- `POST /api/v1/trend-chart/ir` - IR趋势图
- `POST /api/v1/stress-curve/analyze` - 应力曲线分析
- `POST /api/v1/normal-distribution/analyze` - 正态分布分析
- `POST /api/v1/report/generate` - 报告生成
- `GET /api/v1/jobs/{job_id}` - 任务状态查询

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|-----|--------|
| DATABASE_URL | PostgreSQL连接URL | - |
| REDIS_URL | Redis连接URL | - |
| UPLOAD_DIR | 上传文件目录 | /app/storage/uploads |
| RESULT_DIR | 结果文件目录 | /app/storage/results |
| MAX_UPLOAD_SIZE | 最大上传文件大小 | 50MB |
| CORS_ORIGINS | CORS允许的源 | - |

## 许可证

MIT License