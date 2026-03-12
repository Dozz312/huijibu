# 回家不 🏠

> 今晚谁回家，一目了然。

家庭成员回家状态共享应用 —— 默认回家，一键标记不回家。再也不用挨个问"今晚回来吃饭吗"。

## 快速启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 启动服务
python run.py
```

浏览器打开 http://localhost:8000 即可使用。

API 文档：http://localhost:8000/docs

## 项目结构

```
回家不/
├── PRD.md                    # 产品需求文档
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── run.py                # 启动入口
│   └── app/
│       ├── main.py           # FastAPI 应用 + 定时任务
│       ├── config.py         # 配置
│       ├── database.py       # 数据库连接
│       ├── models.py         # 数据模型
│       ├── schemas.py        # 请求/响应 Schema
│       ├── auth.py           # JWT + API Token 认证
│       └── routers/
│           ├── auth.py       # 注册/登录/Token 管理
│           ├── family.py     # 家庭 创建/加入/管理
│           └── status.py     # 回家状态 查询/更新
├── frontend/
│   └── index.html            # 单页应用 (Alpine.js + Tailwind CSS)
```

## API 接口

所有接口均需 Bearer Token 认证（JWT 或 API Token）。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |
| GET | `/api/v1/family` | 列出我的家庭 |
| POST | `/api/v1/family` | 创建家庭 |
| POST | `/api/v1/family/join` | 通过邀请码加入家庭 |
| GET | `/api/v1/status` | 获取所有家庭今日状态 |
| PUT | `/api/v1/status/me` | 更新回家状态 |

### AI 调用示例

```bash
# 今晚不回家
curl -X PUT http://localhost:8000/api/v1/status/me \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"going_home": false, "reason": "加班"}'

# 查看家庭状态
curl http://localhost:8000/api/v1/status \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## 核心规则

- **默认回家**：不操作 = 今晚回家
- **每日重置**：凌晨 4:00 自动重置所有状态
- **只改自己**：只能修改自己的状态
- **API 等价**：API 操作与 App 操作完全等价
