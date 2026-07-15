# 擎动智造 Drivion — 发布平台 (Publish Platform)

> 工位线体注册 · 装备发布 · HAL 驱动管理 · AutoUnit 算子发布 · 部署清单下发  
> 企业级工业自动化 CI/CD 发布中心

---

## 定位

Publish 平台是 **Drivion 工业自动化生态** 的云端发布中枢。它负责管理工业现场的全量制品（驱动包、AutoUnit 自动化单元、操作界面、部署清单），并将它们按工位维度聚合后下发给运行在工控机上的 **InnoDrive Exe** 执行引擎。

```
┌─────────────────────────────────────────────────┐
│              Drivion Publish 发布平台             │
│                                                  │
│  设施拓扑 ─→ 驱动包 ─→ AutoUnit ─→ 界面 ─→ 清单  │
│                       │                         │
│                 工位聚合 Bundle                   │
│                       │                         │
│              ┌────────▼────────┐                 │
│              │  InnoDrive Exe  │                 │
│              │   (工控机端)     │                 │
│              └─────────────────┘                 │
└─────────────────────────────────────────────────┘
```

---

## 功能矩阵

| 模块 | 说明 | 状态 |
|------|------|:----:|
| **设施拓扑管理** | 厂区 → 线体 → 工位 三级树形结构，支持软删除与创建人追溯 | ✅ |
| **驱动包管理** | Java / Python / C++ 驱动注册、版本发布、下架，支持厂商/协议/平台声明 | ✅ |
| **AutoUnit 包管理** | Python 自动化单元上传、版本管理、状态控制 (published/unpublished/testing) | ✅ |
| **界面包管理** | UI 配置存储与版本管理，工位绑定 | ✅ |
| **部署清单管理** | TOML 部署清单上传，声明工位所需的驱动/AutoUnit/界面组合 | ✅ |
| **工位聚合 Bundle** | Exe 拉取接口：按 `station_id` 一次返回清单 + AutoUnit + 驱动 + 界面聚合视图 | ✅ |
| **工位绑定** | 工位与上位机绑定 / 解绑 | ✅ |
| **操作审计日志** | 全量操作记录，支持 CSV 导出 | ✅ |
| **RBAC 权限** | 四级角色 (admin/publisher/base/viewer)，12+ 细粒度权限 | ✅ |
| **JWT 认证** | RS256 非对称加密，Access Token + Cookie 双通道 | ✅ |
| **版本回滚** | 发布回退到历史版本 | ⬜ |
| **灰度发布** | 按比例 / 按工位灰度 | ⬜ |
| **审批流程** | 发布前多级审批 | ⬜ |
| **部署状态监控** | 实时部署进度 / 成功率面板 | ⬜ |

---

## 项目结构

```
publish/
├── publish-svc/                # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/v1/             # API 路由
│   │   │   ├── auth.py         #   认证 (注册/登录/登出/刷新)
│   │   │   ├── facilities.py   #   设施管理 (厂区/线体/工位 CRUD)
│   │   │   ├── drivers.py      #   驱动包管理
│   │   │   ├── autounit.py     #   AutoUnit 包管理
│   │   │   ├── interfaces.py   #   界面管理
│   │   │   ├── deployment.py   #   部署清单管理
│   │   │   ├── bindings.py     #   工位绑定
│   │   │   ├── exe.py          #   Exe 聚合拉取接口
│   │   │   └── logs.py         #   审计日志
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       #   配置 (Pydantic Settings)
│   │   │   ├── database.py     #   数据库 (SQLAlchemy async + aiomysql)
│   │   │   ├── security.py     #   JWT 认证
│   │   │   ├── permissions.py  #   RBAC 权限枚举 (12+ 权限)
│   │   │   ├── storage.py      #   MinIO 对象存储
│   │   │   └── utils.py        #   工具函数
│   │   ├── models/             # ORM 模型 (14 张表)
│   │   └── schemas/            # Pydantic 请求/响应模型
│   ├── sql/                    # 数据库初始化脚本
│   │   ├── init.sql            #   建表 + 权限初始化 + 默认管理员
│   │   ├── users.sql           #   用户数据
│   │   └── roles.sql           #   角色数据
│   ├── data/
│   │   └── demo_manifest.toml  #   Exe 演示清单
│   ├── main.py                 # 应用入口 (uvicorn)
│   ├── requirements.txt
│   ├── setup.sh                # 一键环境初始化
│   └── start.sh                # 启动脚本
│
├── publish-ui/                 # 前端 (Vue 3 + TypeScript)
│   ├── src/
│   │   ├── views/              # 页面
│   │   │   ├── Login.vue       #   登录
│   │   │   ├── Facilities.vue  #   设施管理 (树形结构)
│   │   │   ├── Drivers.vue     #   驱动包管理
│   │   │   ├── AutoUnit.vue    #   AutoUnit 包管理
│   │   │   ├── Interfaces.vue  #   界面管理
│   │   │   ├── Deployment.vue  #   部署清单
│   │   │   └── Logs.vue        #   操作日志
│   │   ├── api/                # API 封装层
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # 路由 + 守卫
│   │   ├── i18n/               # 国际化 (中/英)
│   │   └── utils/request.ts    # Axios 封装 (拦截器/错误处理)
│   ├── vite.config.ts          # Vite 构建配置 + API 代理
│   └── package.json
│
├── API文档.md                  # 完整 API 文档 (v1.0)
└── README.MD                   # 本文件
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.109 (async/await) |
| 前端框架 | Vue 3 (Composition API) + TypeScript |
| UI 组件 | Ant Design Vue 4 + Tailwind CSS 4 |
| 状态管理 | Pinia 2 |
| 构建工具 | Vite 5 |
| 数据库 | MySQL 8 (utf8mb4, InnoDB) |
| ORM | SQLAlchemy 2.0 (async) |
| 对象存储 | MinIO |
| 认证 | JWT RS256 (非对称加密) |
| 密码 | bcrypt |
| 国际化 | Vue I18n 9 |
| HTTP 客户端 | Axios |

---

## `config.toml` 配置指南

发布系统的主配置文件位于项目根目录 [`config.toml`](./config.toml)。后端启动时读取一次，修改后需要重启后端。

默认配置文件路径可以用 `PUBLISH_CONFIG_FILE` 环境变量覆盖：

```bash
PUBLISH_CONFIG_FILE=/etc/drivion/publish.toml \
  conda run -n service python publish-svc/main.py
```

### 完整配置示例

```toml
[server]
host = "0.0.0.0"
port = 8001
debug = true
cors_origins = ["http://localhost:5173"]

[database]
# sqlite / mysql / postgresql
type = "sqlite"
sqlite_path = "./data/publish.db"
host = "localhost"
port = 3306
name = "publish_system"
username = "root"
password = ""
charset = "utf8mb4"

[storage]
# local / minio / s3
provider = "local"
local_dir = "./uploads/objects"
endpoint = "http://192.168.3.68:9000"
access_key = "minioadmin"
secret_key = "minioadmin"
bucket = "publish-system"
region = "us-east-1"
secure = false

[auth]
# local: 使用发布系统内置用户和权限
# sso: 使用 Drivion SSO
mode = "local"

[integration]
api_key_env = "PUBLISH_INTEGRATION_API_KEY"

[auth.sso]
issuer = "http://localhost:8002"
client_id = "release"
client_secret_env = "RELEASE_OIDC_CLIENT_SECRET"
scope = "openid profile"
redirect_uri = "http://localhost:8001/publish/api/v1/auth/sso/callback"
frontend_redirect_uri = "http://localhost:5173/auth/callback"
session_secret_env = "PUBLISH_SSO_SESSION_SECRET"
session_cookie_name = "publish_sso_session"
transaction_cookie_name = "publish_sso_transaction"
cookie_secure = false
session_max_age_seconds = 604800
refresh_before_expiry_seconds = 60
http_timeout_seconds = 10
introspect_high_risk = true
```

### 服务配置

| 配置项 | 说明 |
|--------|------|
| `server.host` | 后端监听地址；容器或局域网部署通常使用 `0.0.0.0` |
| `server.port` | 后端端口，默认 `8001` |
| `server.debug` | 调试开关，生产环境应设为 `false` |
| `server.cors_origins` | 允许访问 API 的前端 Origin 列表，需填写完整的协议、主机和端口 |

### Exe / DevKit 接口配置

Publish 使用内置认证时，Exe Runtime 和 DevKit 通过独立 API Key 访问对外接口：

```toml
[integration]
api_key_env = "PUBLISH_INTEGRATION_API_KEY"
```

```bash
export PUBLISH_INTEGRATION_API_KEY="$(openssl rand -hex 32)"
```

SSO 模式下对外接口改用 OIDC Bearer Access Token，不使用该 API Key。完整的 Exe 拉取、DevKit 提交、Permission 和 scope 说明见 [对外接入文档](./docs/README.md)。

### 数据库配置

支持 `sqlite`、`mysql` 和 `postgresql`。本地开发推荐 SQLite，独立部署可换成 MySQL 或 PostgreSQL。

SQLite 只使用 `sqlite_path`：

```toml
[database]
type = "sqlite"
sqlite_path = "./data/publish.db"
```

MySQL 示例：

```toml
[database]
type = "mysql"
host = "192.168.3.68"
port = 3306
name = "publish_system"
username = "publish"
password = "change-me"
charset = "utf8mb4"
```

PostgreSQL 示例：

```toml
[database]
type = "postgresql"
host = "127.0.0.1"
port = 5432
name = "publish_system"
username = "publish"
password = "change-me"
```

也可以通过 `DATABASE_URL` 环境变量直接提供 SQLAlchemy 异步连接地址，并覆盖 `[database]` 中的连接参数：

```bash
export DATABASE_URL='mysql+aiomysql://publish:password@127.0.0.1:3306/publish_system?charset=utf8mb4'
```

`sqlite_path` 和本地存储路径为相对路径时，以后端进程的当前工作目录为基准。生产部署建议使用绝对路径。

### 制品存储配置

AutoUnit 和 HAL 压缩包可以存放在本地目录、MinIO 或 S3 兼容对象存储中。

本地存储：

```toml
[storage]
provider = "local"
local_dir = "/var/lib/drivion-publish/objects"
```

MinIO：

```toml
[storage]
provider = "minio"
endpoint = "http://192.168.3.68:9000"
access_key = "publish"
secret_key = "change-me"
bucket = "publish-system"
region = "us-east-1"
secure = false
```

AWS S3 或其他 S3 兼容服务：

```toml
[storage]
provider = "s3"
# AWS S3 可留空；其他 S3 兼容服务填写其 endpoint
endpoint = ""
access_key = "change-me"
secret_key = "change-me"
bucket = "publish-system"
region = "ap-southeast-1"
secure = true
```

对象存储的 bucket 不存在时，后端会尝试自动创建，因此所配置的账号需具备对应权限。生产环境不应使用示例中的默认密钥。

### 认证配置

#### 内置认证

```toml
[auth]
mode = "local"
```

`local` 模式使用发布系统自己的用户、角色申请和管理功能，不依赖 SSO。

#### Drivion SSO

```toml
[auth]
mode = "sso"

[auth.sso]
issuer = "https://sso.example.com"
client_id = "release"
client_secret_env = "RELEASE_OIDC_CLIENT_SECRET"
scope = "openid profile"
redirect_uri = "https://publish-api.example.com/publish/api/v1/auth/sso/callback"
frontend_redirect_uri = "https://publish.example.com/auth/callback"
session_secret_env = "PUBLISH_SSO_SESSION_SECRET"
session_cookie_name = "publish_sso_session"
transaction_cookie_name = "publish_sso_transaction"
cookie_secure = true
session_max_age_seconds = 604800
refresh_before_expiry_seconds = 60
http_timeout_seconds = 10
introspect_high_risk = true
```

SSO 客户端密钥和会话加密密钥从环境变量读取：

```bash
export RELEASE_OIDC_CLIENT_SECRET='SSO 中 release 客户端的密钥'
export PUBLISH_SSO_SESSION_SECRET="$(openssl rand -hex 32)"
conda run -n service python publish-svc/main.py
```

SSO 模式还需要在 SSO 的 `release` 客户端中登记与 `redirect_uri` **完全一致**的回调地址。后端不把 OIDC Token 传给浏览器，浏览器只保存 HttpOnly 会话 Cookie。

| 配置项 | 说明 |
|--------|------|
| `issuer` | SSO 服务根地址，用于 OIDC Discovery、JWKS、Token 和注销接口 |
| `client_id` | SSO 中为发布系统登记的客户端 ID，默认 `release` |
| `client_secret_env` | 保存客户端密钥的环境变量名 |
| `redirect_uri` | SSO 授权后回调的发布后端地址 |
| `frontend_redirect_uri` | 后端完成登录后跳转的前端地址 |
| `session_secret_env` | 保存服务端会话加密密钥的环境变量名 |
| `cookie_secure` | HTTPS 部署必须设为 `true`；仅本地 HTTP 开发使用 `false` |
| `session_max_age_seconds` | 发布系统 SSO 会话最长存活时间 |
| `refresh_before_expiry_seconds` | Access Token 距离过期少于该值时自动刷新 |
| `http_timeout_seconds` | 发布后端访问 SSO 的 HTTP 超时时间 |
| `introspect_high_risk` | 高风险写操作前实时向 SSO 校验 Token 和最新权限，生产环境建议保持 `true` |

发布系统在 SSO 模式下只使用 Token 中的 `permissions` 判定权限，不使用 scope 做厂区、线体或工位范围限制。其中 AutoUnit 写操作需要 `autounit.definition.publish`，HAL 写操作需要 `hal.driver.publish`；测试和发布审批使用对应的 SSO 审批权限。

### 生产配置检查

- 将 `server.debug` 设为 `false`，并只在 `cors_origins` 中保留实际前端地址。
- 使用 MySQL/PostgreSQL 和 MinIO/S3，或将 SQLite/本地制品目录挂载到持久化磁盘。
- 使用 HTTPS，并在 SSO 模式下将 `cookie_secure` 设为 `true`。
- 替换示例中的所有密码和对象存储密钥，限制配置文件的文件权限。
- 保持 `introspect_high_risk = true`，以便 SSO 权限被撤销后立即阻止高风险写操作。

---

## 快速开始

### 1. 后端 (publish-svc)

```bash
# 在 publish 根目录编辑 config.toml，然后使用 service 环境启动
conda run -n service python publish-svc/main.py
```

API 文档自动托管:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 2. 前端 (publish-ui)

```bash
cd publish-ui

# 安装依赖
npm install

# 启动开发服务器 (默认 :5173, 自动代理到 :8001)
npm run dev

# 生产构建
npm run build
```

### 3. 鉴权

所有 API 请求需携带 JWT Token（Cookie 或 Authorization Header），通过 `/publish/api/v1/auth/login` 获取。权限模型为 RBAC，参见[权限体系](#权限体系)。

### 4. Exe 聚合拉取

工控机端可通过以下接口获取当前部署聚合包：

```bash
# 真实工位 (需数据库已有该工位及绑定)
GET /publish/api/v1/exe/stations/{station_id}/bundle

# Demo 工位 (内置演示数据，无需数据库)
GET /publish/api/v1/exe/stations/demo-station/bundle
```

返回结构包含：工位信息 + 部署清单 + AutoUnit 列表 + 驱动列表 + 界面列表 + 警告信息。

---

## API 概览

| 路由前缀 | 说明 |
|---------|------|
| `/publish/api/v1/auth` | 认证：注册/登录/登出/刷新 Token |
| `/publish/api/v1/facilities` | 设施管理：厂区/线体/工位 CRUD + 树形查询 |
| `/publish/api/v1/drivers` | 驱动包：上传/发布/下架/下载/查询 |
| `/publish/api/v1/autounit` | AutoUnit 包：上传/发布/撤回/下载/应用到工位 |
| `/publish/api/v1/interfaces` | 界面：创建/编辑/删除/工位绑定/下载 |
| `/publish/api/v1/deployment` | 部署清单：上传/下载/工位绑定 |
| `/publish/api/v1/bindings` | 工位绑定：绑定/解绑 |
| `/publish/api/v1/exe` | Exe 拉取：按工位聚合 Bundle |
| `/publish/api/v1/logs` | 审计日志：查询/导出 |

完整文档见 [API文档.md](./API文档.md)。

---

## 数据库设计

14 张核心表 + 4 个查询视图：

| 模块 | 表 |
|------|-----|
| 用户 & 认证 | `users`, `permissions`, `user_permissions` |
| 设施拓扑 | `factories`, `lines`, `stations` |
| AutoUnit | `autounit_packages`, `autounit_station_applications` |
| 驱动包 | `driver_packages`, `driver_station_bindings` |
| 界面 | `interfaces`, `interface_station_bindings` |
| 部署清单 | `deployment_manifests`, `manifest_station_bindings` |
| 审计日志 | `operation_logs` |

设计要点：软删除 (is_deleted)、JSON 字段用于灵活配置、视图简化跨表查询。

---

## 权限体系

| 角色 | 权限范围 |
|------|---------|
| **admin** | 全部权限，包括用户管理 |
| **publisher** | 发布/下架/撤回各类包，设施管理 |
| **base** | 基本的查看和上传权限 |
| **viewer** | 只读权限 |

权限采用 `resource:action` 风格，例如 `facility:factory:create`、`autounit:publish`。

---

## 待实现

按优先级排列：

1. **版本回滚** — 支持将工位部署回退到历史版本
2. **灰度发布** — 按工位比例逐步推送新版本
3. **审批流程** — 发布操作前多级审批
4. **部署监控** — 实时反馈各工位部署进度与成功率
5. **包完整性校验** — MD5/SHA256 下载后自动校验
6. **安全加固** — Rate Limiting、IP 白名单、登录失败锁定
7. **WebSocket 推送** — 部署状态实时推送到前端

---

> **相关文档**  
> - [对外接入文档](./docs/README.md)
> - [Drivion 商业计划书 & 架构设计](../Drivion%20项目%20商业计划书%20·%20架构设计.md)  
> - [API 文档](./API文档.md)  
> - [后端 README](./publish-svc/README.md)  
> - [前端快速开始](./publish-ui/快速开始.md)  
> - [前端环境配置](./publish-ui/环境配置说明.md)
