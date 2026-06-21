# 发布界面后端 API 文档

> 版本：v1.0  
> 更新时间：2025-01-15  
> 基础路径：`/publish/api/v1`

---

## 目录

- [1. 认证相关](#1-认证相关)
- [2. 设施管理（厂区/线体/工位）](#2-设施管理厂区线体工位)
- [3. AutoUnit 包管理](#3-autounit-包管理)
- [4. 驱动包管理](#4-驱动包管理)
- [5. 界面管理](#5-界面管理)
- [6. 部署清单管理](#6-部署清单管理)
- [7. 工位绑定管理](#7-工位绑定管理)
- [8. 日志管理](#8-日志管理)
- [9. 通用说明](#9-通用说明)

---

## 1. 认证相关

### 1.1 用户注册

**接口说明：** 用户通过用户名和密码注册新账号

**请求方式：** `POST`

**请求路径：** `/auth/register`

**请求参数：**

```json
{
  "username": "newuser", // 必填，用户名（3-32个字符，只能包含字母、数字、下划线和连字符）
  "password": "password123", // 必填，密码（6-32个字符）
  "nickname": "新用户", // 可选，昵称
  "email": "newuser@example.com" // 可选，邮箱地址
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000", // MySQL UUID() 生成的 ID
    "username": "newuser",
    "nickname": "新用户",
    "role": "user", // 默认为普通用户
    "email": "newuser@example.com",
    "avatar": null,
    "permissions": [] // 新用户暂无权限
  }
}
```

**失败响应：**

```json
{
  "code": 409,
  "message": "用户名已存在",
  "data": null
}
```

或

```json
{
  "code": 409,
  "message": "邮箱已被注册",
  "data": null
}
```

或

```json
{
  "code": 422,
  "message": "请求参数验证失败",
  "data": {
    "detail": [
      {
        "loc": ["body", "username"],
        "msg": "用户名只能包含字母、数字、下划线和连字符",
        "type": "value_error"
      }
    ]
  }
}
```

---

### 1.2 用户登录

**接口说明：** 用户通过用户名和密码登录系统

**请求方式：** `POST`

**请求路径：** `/auth/login`

**请求参数：**

```json
{
  "username": "admin", // 必填，用户名
  "password": "admin123" // 必填，密码
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // JWT Token
    "userInfo": {
      "id": "user-001",
      "username": "admin",
      "nickname": "管理员",
      "role": "admin", // admin: 管理员, user: 普通用户
      "email": "admin@example.com",
      "avatar": "https://example.com/avatar.jpg",
      "permissions": [
        // 权限列表
        "facility:create",
        "facility:edit",
        "facility:delete",
        "package:upload",
        "package:publish",
        "interface:create",
        "interface:edit"
      ]
    },
    "expiresIn": 7200 // Token 过期时间（秒）
  }
}
```

**响应头（Set-Cookie）：**

```
Set-Cookie: token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...; Path=/; HttpOnly; Max-Age=7200
```

**说明：**

- 首次登录时，Token 会同时在响应体的 `data.token` 字段返回，并通过 `Set-Cookie` 设置到 Cookie 中
- 前端需要保存响应体中的 Token（用于首次请求）
- 后续请求会自动携带 Cookie 中的 Token

**失败响应：**

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

---

### 1.3 用户登出

**接口说明：** 用户退出登录

**请求方式：** `POST`

**请求路径：** `/auth/logout`

**请求头：**

```
Authorization: Bearer <token>
Cookie: token=<JWT_TOKEN>
```

**说明：** 首次登录后使用 Authorization 头携带 Token，后续请求会自动携带 Cookie

**成功响应：**

```json
{
  "code": 200,
  "message": "退出成功",
  "data": null
}
```

---

### 1.4 获取当前用户信息

**接口说明：** 获取当前登录用户的详细信息

**请求方式：** `GET`

**请求路径：** `/auth/userInfo`

**请求头：**

```
Authorization: Bearer <token>
Cookie: token=<JWT_TOKEN>
```

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "user-001",
    "username": "admin",
    "nickname": "管理员",
    "role": "admin",
    "email": "admin@example.com",
    "avatar": "https://example.com/avatar.jpg",
    "permissions": ["facility:create", "package:upload"]
  }
}
```

---

### 1.5 用户列表模糊搜索

**接口说明：** 根据关键词模糊搜索用户列表（支持用户名、昵称、邮箱搜索）

**请求方式：** `GET`

**请求路径：** `/auth/users/search`

**请求头：**

```
Authorization: Bearer <token>
Cookie: token=<JWT_TOKEN>
```

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                                 |
| -------- | ------ | ---- | ------------------------------------ |
| keyword  | string | 否   | 搜索关键词（匹配用户名、昵称、邮箱） |
| role     | string | 否   | 角色代码筛选                         |
| status   | string | 否   | 状态筛选：`active` / `inactive`      |
| page     | number | 否   | 页码，默认 1                         |
| pageSize | number | 否   | 每页条数，默认 20                    |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "user-001",
        "username": "admin",
        "nickname": "管理员",
        "role": "admin",
        "email": "admin@example.com",
        "avatar": "https://example.com/avatar.jpg",
        "status": "active",
        "createTime": "2025-01-15 10:30:00",
        "updateTime": "2025-01-15 10:30:00"
      },
      {
        "id": "user-002",
        "username": "user1",
        "nickname": "普通用户1",
        "role": "user",
        "email": "user1@example.com",
        "avatar": null,
        "status": "active",
        "createTime": "2025-01-15 11:00:00",
        "updateTime": "2025-01-15 11:00:00"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20
  }
}
```

---

## 2. 设施管理（厂区/线体/工位）

### 2.1 获取设施树形结构

**接口说明：** 获取完整的厂区-线体-工位树形结构数据

**请求方式：** `GET`

**请求路径：** `/facilities/tree`

**查询参数：**

| 参数名 | 类型   | 必填 | 说明                       |
| ------ | ------ | ---- | -------------------------- |
| search | string | 否   | 搜索关键词（名称模糊查询） |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": "factory-1",
      "name": "上海工厂",
      "type": "factory",
      "code": "SH-01", // 可选，厂区编号
      "description": "上海浦东新区工厂",
      "location": "上海市浦东新区", // 可选，地址
      "status": "active", // active: 启用, inactive: 停用
      "createTime": "2025-01-15 10:30:00",
      "updateTime": "2025-01-15 10:30:00",
      "children": [
        {
          "id": "line-1-1",
          "name": "生产线 A",
          "type": "line",
          "code": "LINE-A",
          "description": "主生产线",
          "status": "active",
          "createTime": "2025-01-15 10:35:00",
          "updateTime": "2025-01-15 10:35:00",
          "children": [
            {
              "id": "station-1-1-1",
              "name": "工位 A1",
              "type": "station",
              "code": "ST-A1",
              "description": "第一工位",
              "status": "active",
              "ip": "192.168.1.101", // 可选，工位设备 IP
              "mac": "00:1A:2B:3C:4D:5E", // 可选，工位设备 MAC
              "createTime": "2025-01-15 10:40:00",
              "updateTime": "2025-01-15 10:40:00"
            }
          ]
        }
      ]
    }
  ]
}
```

---

### 2.2 创建厂区

**接口说明：** 创建新的厂区

**请求方式：** `POST`

**请求路径：** `/facilities/factory`

**请求参数：**

```json
{
  "name": "深圳工厂", // 必填，厂区名称
  "code": "SZ-01", // 可选，厂区编号
  "description": "深圳南山区工厂", // 可选，描述
  "location": "深圳市南山区", // 可选，地址
  "status": "active" // 可选，默认 active
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": "factory-2",
    "name": "深圳工厂",
    "type": "factory",
    "code": "SZ-01",
    "description": "深圳南山区工厂",
    "location": "深圳市南山区",
    "status": "active",
    "createTime": "2025-01-15 11:00:00",
    "updateTime": "2025-01-15 11:00:00"
  }
}
```

---

### 2.3 创建线体

**接口说明：** 在指定厂区下创建新的线体

**请求方式：** `POST`

**请求路径：** `/facilities/line`

**请求参数：**

```json
{
  "factoryId": "factory-1", // 必填，所属厂区 ID
  "name": "生产线 B", // 必填，线体名称
  "code": "LINE-B", // 可选，线体编号
  "description": "副生产线", // 可选，描述
  "status": "active" // 可选，默认 active
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": "line-1-2",
    "factoryId": "factory-1",
    "name": "生产线 B",
    "type": "line",
    "code": "LINE-B",
    "description": "副生产线",
    "status": "active",
    "createTime": "2025-01-15 11:05:00",
    "updateTime": "2025-01-15 11:05:00"
  }
}
```

---

### 2.4 创建工位

**接口说明：** 在指定线体下创建新的工位

**请求方式：** `POST`

**请求路径：** `/facilities/station`

**请求参数：**

```json
{
  "lineId": "line-1-1", // 必填，所属线体 ID
  "name": "工位 A3", // 必填，工位名称
  "code": "ST-A3", // 可选，工位编号
  "description": "第三工位", // 可选，描述
  "ip": "192.168.1.103", // 可选，工位设备 IP
  "mac": "00:1A:2B:3C:4D:5F", // 可选，工位设备 MAC
  "status": "active" // 可选，默认 active
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": "station-1-1-3",
    "lineId": "line-1-1",
    "name": "工位 A3",
    "type": "station",
    "code": "ST-A3",
    "description": "第三工位",
    "ip": "192.168.1.103",
    "mac": "00:1A:2B:3C:4D:5F",
    "status": "active",
    "createTime": "2025-01-15 11:10:00",
    "updateTime": "2025-01-15 11:10:00"
  }
}
```

---

### 2.5 更新厂区

**接口说明：** 更新厂区信息

**请求方式：** `PUT`

**请求路径：** `/facilities/factory/{id}`

**路径参数：**

- `id`: 厂区 ID

**请求参数：**

```json
{
  "name": "更新后的厂区名称", // 可选
  "code": "NEW-CODE", // 可选
  "description": "更新后的描述", // 可选
  "status": "inactive", // 可选，active / inactive
  "location": "新地址" // 可选
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "factory-1",
    "name": "更新后的厂区名称",
    "type": "factory",
    "code": "NEW-CODE",
    "description": "更新后的描述",
    "location": "新地址",
    "status": "inactive",
    "createTime": "2025-01-15 10:30:00",
    "updateTime": "2025-01-15 11:15:00"
  }
}
```

---

### 2.6 更新线体

**接口说明：** 更新线体信息

**请求方式：** `PUT`

**请求路径：** `/facilities/line/{id}`

**路径参数：**

- `id`: 线体 ID

**请求参数：**

```json
{
  "name": "更新后的线体名称", // 可选
  "code": "NEW-LINE-CODE", // 可选
  "description": "更新后的描述", // 可选
  "status": "inactive" // 可选，active / inactive
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "line-1-1",
    "factoryId": "factory-1",
    "name": "更新后的线体名称",
    "type": "line",
    "code": "NEW-LINE-CODE",
    "description": "更新后的描述",
    "status": "inactive",
    "createTime": "2025-01-15 10:35:00",
    "updateTime": "2025-01-15 11:20:00"
  }
}
```

---

### 2.7 更新工位

**接口说明：** 更新工位信息

**请求方式：** `PUT`

**请求路径：** `/facilities/station/{id}`

**路径参数：**

- `id`: 工位 ID

**请求参数：**

```json
{
  "name": "更新后的工位名称", // 可选
  "code": "NEW-STATION-CODE", // 可选
  "description": "更新后的描述", // 可选
  "status": "inactive", // 可选，active / inactive
  "ip": "192.168.1.200", // 可选
  "mac": "00:1A:2B:3C:4D:60" // 可选
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "station-1-1-1",
    "lineId": "line-1-1",
    "name": "更新后的工位名称",
    "type": "station",
    "code": "NEW-STATION-CODE",
    "description": "更新后的描述",
    "ip": "192.168.1.200",
    "mac": "00:1A:2B:3C:4D:60",
    "status": "inactive",
    "createTime": "2025-01-15 10:40:00",
    "updateTime": "2025-01-15 11:25:00"
  }
}
```

---

### 2.8 删除厂区

**接口说明：** 删除指定厂区

**请求方式：** `DELETE`

**请求路径：** `/facilities/factory/{id}`

**路径参数：**

- `id`: 厂区 ID

**注意事项：**

- 删除厂区会级联删除其下所有线体和工位

**成功响应：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 2.9 删除线体

**接口说明：** 删除指定线体

**请求方式：** `DELETE`

**请求路径：** `/facilities/line/{id}`

**路径参数：**

- `id`: 线体 ID

**注意事项：**

- 删除线体会级联删除其下所有工位

**成功响应：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 2.10 删除工位

**接口说明：** 删除指定工位

**请求方式：** `DELETE`

**请求路径：** `/facilities/station/{id}`

**路径参数：**

- `id`: 工位 ID

**注意事项：**

- 如果工位已绑定界面/驱动/AutoUnit，需要先解绑才能删除（或后端强制级联解绑）

**成功响应：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

**失败响应（存在依赖）：**

```json
{
  "code": 400,
  "message": "该工位已绑定界面，请先解绑后再删除",
  "data": {
    "boundInterfaces": ["界面名称1", "界面名称2"]
  }
}
```

---

### 2.11 工位模糊搜索

**接口说明：** 根据关键词模糊搜索工位列表（支持工位名称、编号搜索）

**请求方式：** `GET`

**请求路径：** `/facilities/stations/search`

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                             |
| -------- | ------ | ---- | -------------------------------- |
| keyword  | string | 否   | 搜索关键词（匹配工位名称、编号） |
| page     | number | 否   | 页码，默认 1                     |
| pageSize | number | 否   | 每页条数，默认 20                |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1",
        "description": "第一工位",
        "ip": "192.168.1.101",
        "mac": "00:1A:2B:3C:4D:5E",
        "status": "active",
        "path": "上海工厂 / 生产线 A / 工位 A1",
        "factoryId": "factory-1",
        "factoryName": "上海工厂",
        "lineId": "line-1-1",
        "lineName": "生产线 A",
        "createTime": "2025-01-15 10:40:00",
        "updateTime": "2025-01-15 10:40:00"
      },
      {
        "id": "station-1-1-2",
        "name": "工位 A2",
        "code": "ST-A2",
        "description": "第二工位",
        "ip": "192.168.1.102",
        "mac": "00:1A:2B:3C:4D:5F",
        "status": "active",
        "path": "上海工厂 / 生产线 A / 工位 A2",
        "factoryId": "factory-1",
        "factoryName": "上海工厂",
        "lineId": "line-1-1",
        "lineName": "生产线 A",
        "createTime": "2025-01-15 10:45:00",
        "updateTime": "2025-01-15 10:45:00"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20
  }
}
```

---

## 3. AutoUnit 包管理

### 3.1 获取 AutoUnit 包列表

**接口说明：** 获取 AutoUnit 包列表（支持筛选和搜索）

**请求方式：** `GET`

**请求路径：** `/autounit/packages`

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                                              |
| -------- | ------ | ---- | ------------------------------------------------- |
| page     | number | 否   | 页码，默认 1                                      |
| pageSize | number | 否   | 每页条数，默认 20                                 |
| search   | string | 否   | 搜索关键词（包名称/文件名）                       |
| status   | string | 否   | 发布状态：`published` / `unpublished` / `testing` |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "pkg-001",
        "name": "AutoUnit Core",
        "fileName": "autounit-core-1.2.0.tar.gz",
        "version": "1.2.0",
        "size": 3145728, // 文件大小（字节）
        "uploadTime": "2025-01-15 10:30:00",
        "uploadUser": "admin", // 上传者
        "status": "published", // published: 已发布, unpublished: 未发布, testing: 测试中
        "description": "AutoUnit 核心包，包含基础功能模块",
        "boundStations": [
          // 绑定的工位
          {
            "id": "station-1-1-1",
            "name": "工位 A1",
            "code": "ST-A1"
          },
          {
            "id": "station-1-1-2",
            "name": "工位 A2",
            "code": "ST-A2"
          }
        ],
        "dependencies": [
          // Python 依赖
          "numpy>=1.20.0",
          "pandas>=1.3.0",
          "requests>=2.26.0"
        ],
        "pythonVersion": "3.8", // Python 版本要求
        "downloadCount": 150, // 下载次数
        "md5": "d41d8cd98f00b204e9800998ecf8427e", // 文件 MD5
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" // 文件 SHA256
      }
    ],
    "total": 50, // 总记录数
    "page": 1,
    "pageSize": 10
  }
}
```

---

### 3.2 上传 AutoUnit 包

**接口说明：** 上传新的 AutoUnit Python 包

**请求方式：** `POST`

**请求路径：** `/autounit/packages/upload`

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

表单数据（FormData）：

| 参数名        | 类型   | 必填 | 说明                      |
| ------------- | ------ | ---- | ------------------------- |
| file          | File   | 是   | 包文件（.zip 或 .tar.gz） |
| name          | string | 是   | 包名称                    |
| version       | string | 是   | 版本号（格式：x.y.z）     |
| description   | string | 否   | 包描述                    |
| pythonVersion | string | 否   | Python 版本要求           |

**文件大小限制：** 无限制

**文件格式要求：**

- 支持 .zip 和 .tar.gz 格式
- 必须包含 `setup.py` 或 `pyproject.toml`
- 包结构需符合 Python 标准包规范

**成功响应：**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": "pkg-002",
    "name": "AutoUnit Vision",
    "fileName": "autounit-vision-2.0.1.zip",
    "version": "2.0.1",
    "size": 5242880,
    "uploadTime": "2025-01-15 11:20:00",
    "uploadUser": "admin",
    "status": "unpublished",
    "description": "视觉处理模块",
    "dependencies": ["opencv-python>=4.5.0", "pillow>=8.0.0"],
    "pythonVersion": "3.8",
    "md5": "abc123...",
    "sha256": "def456..."
  }
}
```

**失败响应：**

```json
{
  "code": 400,
  "message": "包结构校验失败：缺少 setup.py 文件",
  "data": {
    "errors": ["Missing setup.py file", "Invalid package structure"]
  }
}
```

---

### 3.3 更新 AutoUnit 包状态

**接口说明：** 更新 AutoUnit 包的状态（发布/测试/未发布）

**请求方式：** `PUT`

**请求路径：** `/autounit/packages/{id}/status`

**路径参数：**

- `id`: 包 ID

**请求参数：**

```json
{
  "status": "published" // 可选值：published / unpublished / testing
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "状态更新成功",
  "data": {
    "id": "pkg-001",
    "status": "published",
    "updateTime": "2025-01-15 11:25:00"
  }
}
```

**说明：**

- 状态由后端流程控制，前端仅展示和同步状态
- 转测、发布等流程操作由后端管理，前端调用此接口获取最新状态

---

### 3.4 撤回 AutoUnit 包

**接口说明：** 撤回并删除 AutoUnit 包

**请求方式：** `DELETE`

**请求路径：** `/autounit/packages/{id}/recall`

**路径参数：**

- `id`: 包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "撤回成功",
  "data": null
}
```

---

### 3.5 下载 AutoUnit 包

**接口说明：** 下载指定的 AutoUnit 包文件

**请求方式：** `GET`

**请求路径：** `/autounit/packages/{id}/download`

**路径参数：**

- `id`: 包 ID

**响应类型：** 文件流

**响应头：**

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="autounit-core-1.2.0.tar.gz"
Content-Length: 3145728
```

**响应体：**

```
<文件二进制流>
```

---

### 3.6 获取 AutoUnit 包详情

**接口说明：** 获取指定 AutoUnit 包的详细信息

**请求方式：** `GET`

**请求路径：** `/autounit/packages/{id}`

**路径参数：**

- `id`: 包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "pkg-001",
    "name": "AutoUnit Core",
    "fileName": "autounit-core-1.2.0.tar.gz",
    "version": "1.2.0",
    "size": 3145728,
    "uploadTime": "2025-01-15 10:30:00",
    "uploadUser": "admin",
    "status": "published",
    "publishTime": "2025-01-15 10:35:00",
    "publishUser": "admin",
    "description": "AutoUnit 核心包，包含基础功能模块",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1",
        "path": "上海工厂 / 生产线 A / 工位 A1"
      }
    ],
    "dependencies": ["numpy>=1.20.0", "pandas>=1.3.0"],
    "pythonVersion": "3.8",
    "downloadCount": 150,
    "md5": "d41d8cd98f00b204e9800998ecf8427e",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "readme": "# AutoUnit Core\n\n核心功能包...", // README 内容
    "changelog": "## v1.2.0\n- 新增功能..." // 更新日志
  }
}
```

---

## 4. 驱动包管理

### 4.1 获取驱动包列表

**接口说明：** 获取驱动包列表（支持筛选和搜索）

**请求方式：** `GET`

**请求路径：** `/drivers/packages`

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                                              |
| -------- | ------ | ---- | ------------------------------------------------- |
| page     | number | 否   | 页码，默认 1                                      |
| pageSize | number | 否   | 每页条数，默认 10                                 |
| search   | string | 否   | 搜索关键词（驱动名称/文件名）                     |
| type     | string | 否   | 驱动类型：`java` / `python` / `cpp`               |
| status   | string | 否   | 发布状态：`published` / `unpublished` / `testing` |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "driver-001",
        "name": "PLC 驱动",
        "fileName": "plc-driver-1.0.0.zip",
        "type": "java", // java / python / cpp
        "version": "1.0.0",
        "size": 2048000,
        "uploadTime": "2025-01-15 10:30:00",
        "uploadUser": "admin",
        "status": "published",
        "description": "西门子 PLC 驱动",
        "boundStations": [
          {
            "id": "station-1-1-1",
            "name": "工位 A1",
            "code": "ST-A1"
          }
        ],
        "protocol": "Modbus TCP", // 支持的协议
        "manufacturer": "Siemens", // 设备厂商
        "deviceModel": "S7-1200", // 设备型号
        "downloadCount": 80,
        "md5": "abc123..."
      }
    ],
    "total": 30,
    "page": 1,
    "pageSize": 10
  }
}
```

---

### 4.2 上传驱动包

**接口说明：** 上传新的驱动包

**请求方式：** `POST`

**请求路径：** `/drivers/packages/upload`

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

表单数据（FormData）：

| 参数名       | 类型   | 必填 | 说明                                |
| ------------ | ------ | ---- | ----------------------------------- |
| file         | File   | 是   | 驱动文件                            |
| type         | string | 是   | 驱动类型：`java` / `python` / `cpp` |
| name         | string | 是   | 驱动名称                            |
| version      | string | 是   | 版本号                              |
| description  | string | 否   | 驱动描述                            |
| protocol     | string | 否   | 支持的协议                          |
| manufacturer | string | 否   | 设备厂商                            |
| deviceModel  | string | 否   | 设备型号                            |

**文件格式要求：**

- Java 驱动：.zip 文件（Maven 项目打包）
- Python 驱动：.zip 或 .tar.gz 文件
- C++ 驱动：.dll 文件（Windows）或 .so 文件（Linux）

**文件大小限制：** 无限制

**成功响应：**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": "driver-002",
    "name": "Modbus 驱动",
    "fileName": "modbus-driver.tar.gz",
    "type": "python",
    "version": "2.3.1",
    "size": 1024000,
    "uploadTime": "2025-01-15 11:30:00",
    "uploadUser": "admin",
    "status": "unpublished",
    "description": "Modbus RTU/TCP 驱动",
    "protocol": "Modbus RTU/TCP",
    "md5": "def456..."
  }
}
```

---

### 4.3 发布驱动包

**接口说明：** 发布驱动包到生产环境

**请求方式：** `POST`

**请求路径：** `/drivers/packages/{id}/publish`

**路径参数：**

- `id`: 驱动包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "发布成功",
  "data": {
    "id": "driver-001",
    "status": "published",
    "publishTime": "2025-01-15 11:35:00",
    "publishUser": "admin"
  }
}
```

---

### 4.4 下架驱动包

**接口说明：** 下架已发布的驱动包（不删除，只改变状态）

**请求方式：** `POST`

**请求路径：** `/drivers/packages/{id}/unpublish`

**路径参数：**

- `id`: 驱动包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "下架成功",
  "data": {
    "id": "driver-001",
    "status": "unpublished",
    "unpublishTime": "2025-01-15 11:40:00",
    "unpublishUser": "admin"
  }
}
```

---

### 4.5 撤回驱动包

**接口说明：** 撤回并删除驱动包

**请求方式：** `DELETE`

**请求路径：** `/drivers/packages/{id}/recall`

**路径参数：**

- `id`: 驱动包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "撤回成功",
  "data": null
}
```

---

### 4.6 下载驱动包

**接口说明：** 下载指定的驱动包文件

**请求方式：** `GET`

**请求路径：** `/drivers/packages/{id}/download`

**路径参数：**

- `id`: 驱动包 ID

**响应类型：** 文件流

**响应头：**

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="plc-driver-1.0.0.zip"
Content-Length: 2048000
```

**响应体：**

```
<文件二进制流>
```

---

### 4.7 获取驱动包详情

**接口说明：** 获取指定驱动包的详细信息

**请求方式：** `GET`

**请求路径：** `/drivers/packages/{id}`

**路径参数：**

- `id`: 驱动包 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "driver-001",
    "name": "PLC 驱动",
    "fileName": "plc-driver-1.0.0.zip",
    "type": "java",
    "version": "1.0.0",
    "size": 2048000,
    "uploadTime": "2025-01-15 10:30:00",
    "uploadUser": "admin",
    "status": "published",
    "publishTime": "2025-01-15 10:35:00",
    "description": "西门子 PLC 驱动",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1",
        "path": "上海工厂 / 生产线 A / 工位 A1"
      }
    ],
    "protocol": "Modbus TCP",
    "manufacturer": "Siemens",
    "deviceModel": "S7-1200",
    "downloadCount": 80,
    "md5": "abc123...",
    "supportedPlatforms": ["Windows", "Linux"], // 支持的平台
    "apiDocUrl": "https://docs.example.com/plc-driver/api", // API 文档地址
    "readme": "# PLC 驱动\n\n使用说明..."
  }
}
```

---

## 5. 界面管理

### 5.1 获取界面列表

**接口说明：** 获取界面列表（支持搜索）

**请求方式：** `GET`

**请求路径：** `/interfaces`

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                        |
| -------- | ------ | ---- | --------------------------- |
| page     | number | 否   | 页码，默认 1                |
| pageSize | number | 否   | 每页条数，默认 10           |
| search   | string | 否   | 搜索关键词（界面名称/描述） |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "interface-001",
        "name": "生产监控界面",
        "description": "实时监控生产线运行状态，显示关键指标和设备状态",
        "layout": "grid", // 布局类型：single / double / grid / custom
        "thumbnail": "https://example.com/thumbnails/interface-001.png", // 缩略图
        "boundStations": [
          {
            "id": "station-1-1-1",
            "name": "工位 A1",
            "code": "ST-A1",
            "path": "上海工厂 / 生产线 A / 工位 A1"
          },
          {
            "id": "station-1-1-2",
            "name": "工位 A2",
            "code": "ST-A2",
            "path": "上海工厂 / 生产线 A / 工位 A2"
          }
        ],
        "createTime": "2025-01-15 10:30:00",
        "updateTime": "2025-01-15 10:30:00",
        "createUser": "admin"
      }
    ],
    "total": 15,
    "page": 1,
    "pageSize": 10
  }
}
```

---

### 5.2 创建界面

**接口说明：** 创建新的界面

**请求方式：** `POST`

**请求路径：** `/interfaces`

**请求参数：**

**请求类型：** `multipart/form-data`

| 参数名      | 类型   | 必填 | 说明                                                 |
| ----------- | ------ | ---- | ---------------------------------------------------- |
| file        | File   | 是   | JSON 配置文件                                        |
| name        | string | 是   | 界面名称                                             |
| description | string | 否   | 界面描述                                             |
| stationIds  | string | 否   | 工位 ID 列表(JSON 字符串)，例如：`["station-1-2-1"]` |

**成功响应：**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": "interface-002",
    "name": "质量检测界面",
    "description": "产品质量检测数据展示和分析",
    "thumbnail": null,
    "boundStations": [
      {
        "id": "station-1-2-1",
        "name": "工位 B1",
        "code": "ST-B1",
        "path": "上海工厂 / 生产线 B / 工位 B1"
      }
    ],
    "createTime": "2025-01-15 11:45:00",
    "updateTime": "2025-01-15 11:45:00",
    "createUser": "admin"
  }
}
```

---

### 5.3 更新界面信息

**接口说明：** 更新界面的基本信息（名称、描述等，不包括配置）

**请求方式：** `PUT`

**请求路径：** `/interfaces/{id}/info`

**路径参数：**

- `id`: 界面 ID

**请求参数：**

```json
{
  "name": "新的界面名称", // 可选
  "description": "新的界面描述", // 可选
  "stationIds": [
    // 可选，初始绑定的工位 ID 列表
    "station-1-2-1"
  ]
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "interface-002",
    "name": "质量检测界面",
    "description": "产品质量检测数据展示和分析",
    "thumbnail": null,
    "boundStations": [
      {
        "id": "station-1-2-1",
        "name": "工位 B1",
        "code": "ST-B1",
        "path": "上海工厂 / 生产线 B / 工位 B1"
      }
    ],
    "createTime": "2025-01-15 11:45:00",
    "updateTime": "2025-01-15 11:45:00",
    "createUser": "admin"
  }
}
```

**说明：**

- 界面是由界面编辑器编辑，界面信息（控件、位置、布局、交互等信息）都体现在导出的 json 文件中
- 发布平台只针对界面导出的 json 文件做管理（比如工站的绑定）和上传，不参与具体的编辑工作

---

### 5.5 删除界面

**接口说明：** 删除指定界面

**请求方式：** `DELETE`

**请求路径：** `/interfaces/{id}`

**路径参数：**

- `id`: 界面 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 5.6 获取界面详情

**接口说明：** 获取指定界面的详细信息和配置

**请求方式：** `GET`

**请求路径：** `/interfaces/{id}`

**路径参数：**

- `id`: 界面 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "interface-001",
    "name": "生产监控界面",
    "description": "实时监控生产线运行状态",
    "layout": "grid",
    "config": {
      "components": [
        /* ... */
      ],
      "theme": "light",
      "refreshInterval": 5000
    },
    "thumbnail": "https://example.com/thumbnails/interface-001.png",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1",
        "path": "上海工厂 / 生产线 A / 工位 A1"
      }
    ],
    "createTime": "2025-01-15 10:30:00",
    "updateTime": "2025-01-15 10:30:00",
    "createUser": "admin",
    "lastEditUser": "admin"
  }
}
```

---

### 5.7 预览界面

**接口说明：** 获取界面预览的渲染数据（用于预览功能）

**请求方式：** `GET`

**请求路径：** `/interfaces/{id}/preview`

**路径参数：**

- `id`: 界面 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "interface-001",
    "name": "生产监控界面",
    "config": {
      /* 界面完整配置 */
    },
    "previewUrl": "https://preview.example.com/interface-001" // 可选，预览地址
  }
}
```

---

### 5.8 下载界面配置文件

**接口说明：** 下载指定界面的 JSON 配置文件

**请求方式：** `GET`

**请求路径：** `/interfaces/{id}/download`

**路径参数：**

- `id`: 界面 ID

**响应类型：** 文件流

**响应头：**

```
Content-Type: application/json
Content-Disposition: attachment; filename*=UTF-8''%E7%94%9F%E4%BA%A7%E7%9B%91%E6%8E%A7%E7%95%8C%E9%9D%A2.json
Content-Length: <文件大小>
```

**说明：**

- 文件名使用 RFC 5987 标准编码（`filename*=UTF-8''<URL编码的文件名>`），以支持中文文件名
- 浏览器会自动解码为正常的中文文件名

**响应体：**

```
<JSON 文件流>
```

**失败响应：**

```json
{
  "code": 404,
  "message": "界面不存在",
  "data": null
}
```

或

```json
{
  "code": 500,
  "message": "文件下载失败",
  "data": {
    "error": "文件不存在或已损坏"
  }
}
```

---

## 6. 部署清单管理

### 6.1 获取部署清单列表

**接口说明：** 获取部署清单列表（支持搜索）

**请求方式：** `GET`

**请求路径：** `/deployment/manifests`

**查询参数：**

| 参数名   | 类型   | 必填 | 说明                        |
| -------- | ------ | ---- | --------------------------- |
| page     | number | 否   | 页码，默认 1                |
| pageSize | number | 否   | 每页条数，默认 20           |
| search   | string | 否   | 搜索关键词（清单名称/描述） |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "manifest-001",
        "name": "生产线A部署清单",
        "description": "生产线A的完整部署配置",
        "fileName": "production-line-a.toml",
        "version": "1.0.0",
        "size": 2048, // 文件大小（字节）
        "uploadTime": "2025-01-15 10:30:00",
        "uploadUser": "admin",
        "boundStations": [
          // 绑定的工位
          {
            "id": "station-1-1-1",
            "name": "工位 A1",
            "code": "ST-A1"
          },
          {
            "id": "station-1-1-2",
            "name": "工位 A2",
            "code": "ST-A2"
          }
        ],
        "md5": "d41d8cd98f00b204e9800998ecf8427e"
      }
    ],
    "total": 20,
    "page": 1,
    "pageSize": 20
  }
}
```

---

### 6.2 上传部署清单

**接口说明：** 上传新的部署清单文件

**请求方式：** `POST`

**请求路径：** `/deployment/manifests/upload`

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

表单数据（FormData）：

| 参数名      | 类型   | 必填 | 说明                  |
| ----------- | ------ | ---- | --------------------- |
| file        | File   | 是   | TOML 文件             |
| name        | string | 是   | 清单名称              |
| version     | string | 否   | 版本号（格式：x.y.z） |
| description | string | 否   | 清单描述              |

**文件格式要求：**

- 仅支持 .toml 格式
- 文件大小无限制

**成功响应：**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": "manifest-002",
    "name": "生产线B部署清单",
    "description": "生产线B的完整部署配置",
    "fileName": "production-line-b.toml",
    "version": "1.0.0",
    "size": 2048,
    "uploadTime": "2025-01-15 11:20:00",
    "uploadUser": "admin",
    "md5": "abc123..."
  }
}
```

**失败响应：**

```json
{
  "code": 400,
  "message": "文件格式错误：必须为 TOML 格式",
  "data": {
    "errors": ["Invalid file format: expected .toml"]
  }
}
```

---

### 6.3 获取部署清单详情

**接口说明：** 获取指定部署清单的详细信息

**请求方式：** `GET`

**请求路径：** `/deployment/manifests/{id}`

**路径参数：**

- `id`: 清单 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "manifest-001",
    "name": "生产线A部署清单",
    "description": "生产线A的完整部署配置",
    "fileName": "production-line-a.toml",
    "version": "1.0.0",
    "size": 2048,
    "uploadTime": "2025-01-15 10:30:00",
    "uploadUser": "admin",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1",
        "path": "上海工厂 / 生产线 A / 工位 A1"
      }
    ],
    "md5": "d41d8cd98f00b204e9800998ecf8427e",
    "content": "[deployment]\nname = \"production-line-a\"\nversion = \"1.0.0\"\n...", // TOML 文件内容
    "downloadCount": 50
  }
}
```

---

### 6.4 更新部署清单信息

**接口说明：** 更新部署清单的基本信息（名称、描述等）

**请求方式：** `PUT`

**请求路径：** `/deployment/manifests/{id}`

**路径参数：**

- `id`: 清单 ID

**请求参数：**

```json
{
  "name": "新的清单名称", // 可选
  "description": "新的清单描述", // 可选
  "version": "1.1.0" // 可选
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "manifest-001",
    "name": "新的清单名称",
    "description": "新的清单描述",
    "version": "1.1.0",
    "updateTime": "2025-01-15 11:50:00"
  }
}
```

---

### 6.5 删除部署清单

**接口说明：** 删除指定的部署清单

**请求方式：** `DELETE`

**请求路径：** `/deployment/manifests/{id}`

**路径参数：**

- `id`: 清单 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

**失败响应（已绑定工位）：**

```json
{
  "code": 400,
  "message": "该部署清单已绑定工位，请先解绑后再删除",
  "data": {
    "boundStations": ["工位 A1", "工位 A2"]
  }
}
```

---

### 6.6 下载部署清单

**接口说明：** 下载指定的部署清单文件

**请求方式：** `GET`

**请求路径：** `/deployment/manifests/{id}/download`

**路径参数：**

- `id`: 清单 ID

**响应类型：** 文件流

**响应头：**

```
Content-Type: application/toml
Content-Disposition: attachment; filename="production-line-a.toml"
Content-Length: 2048
```

**响应体：**

```
<TOML 文件流>
```

---

### 6.7 绑定部署清单到工位

**接口说明：** 将部署清单绑定到一个或多个工位

**请求方式：** `POST`

**请求路径：** `/deployment/manifests/{id}/bind`

**路径参数：**

- `id`: 清单 ID

**请求参数：**

```json
{
  "stationIds": [
    // 必填，工位 ID 列表
    "station-1-1-1",
    "station-1-1-2"
  ]
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "绑定成功",
  "data": {
    "manifestId": "manifest-001",
    "manifestName": "生产线A部署清单",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1"
      },
      {
        "id": "station-1-1-2",
        "name": "工位 A2",
        "code": "ST-A2"
      }
    ],
    "bindTime": "2025-01-15 12:00:00"
  }
}
```

---

### 6.8 解绑部署清单与工位

**接口说明：** 解绑部署清单与工位的绑定关系

**请求方式：** `DELETE`

**请求路径：** `/deployment/manifests/{id}/bind`

**路径参数：**

- `id`: 清单 ID

**请求参数：**

```json
{
  "stationIds": [
    // 必填，要解绑的工位 ID 列表
    "station-1-1-2"
  ]
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "解绑成功",
  "data": null
}
```

---

## 7. 工位绑定管理

**说明：**

- **界面绑定**：界面需要绑定到工位，作为该工位的自动化界面提供用户交互
- **部署清单绑定**：部署清单需要绑定到工位，提供工位的部署配置
- **AutoUnit 包应用**：AutoUnit 包不是绑定，而是应用到指定工位
- **驱动包**：驱动包不需要绑定工位

### 7.1 绑定界面到工位

**接口说明：** 将界面绑定到一个或多个工位，作为工位的自动化交互界面

**请求方式：** `POST`

**请求路径：** `/bindings/interface`

**请求参数：**

```json
{
  "interfaceId": "interface-001", // 必填，界面 ID
  "stationIds": [
    // 必填，工位 ID 列表
    "station-1-1-1",
    "station-1-1-2"
  ]
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "绑定成功",
  "data": {
    "interfaceId": "interface-001",
    "interfaceName": "生产监控界面",
    "boundStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1"
      },
      {
        "id": "station-1-1-2",
        "name": "工位 A2",
        "code": "ST-A2"
      }
    ],
    "bindTime": "2025-01-15 12:00:00"
  }
}
```

---

### 7.2 解绑界面与工位

**接口说明：** 解绑界面与工位的绑定关系

**请求方式：** `DELETE`

**请求路径：** `/bindings/interface`

**请求参数：**

```json
{
  "interfaceId": "interface-001", // 必填，界面 ID
  "stationIds": [
    // 必填，要解绑的工位 ID 列表
    "station-1-1-2"
  ]
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "解绑成功",
  "data": null
}
```

---

### 7.3 应用 AutoUnit 包到工位

**接口说明：** 将 AutoUnit 包应用到一个或多个工位

**请求方式：** `POST`

**请求路径：** `/autounit/packages/{id}/apply`

**路径参数：**

- `id`: AutoUnit 包 ID

**请求参数：**

```json
{
  "stationIds": ["station-1-1-1", "station-1-1-2"] // 必填，要应用的工位 ID 列表
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "应用成功",
  "data": {
    "packageId": "pkg-001",
    "packageName": "AutoUnit Core",
    "appliedStations": [
      {
        "id": "station-1-1-1",
        "name": "工位 A1",
        "code": "ST-A1"
      },
      {
        "id": "station-1-1-2",
        "name": "工位 A2",
        "code": "ST-A2"
      }
    ],
    "applyTime": "2025-01-15 12:10:00"
  }
}
```

---

### 7.4 取消 AutoUnit 包在工位的应用

**接口说明：** 取消 AutoUnit 包在指定工位的应用

**请求方式：** `DELETE`

**请求路径：** `/autounit/packages/{id}/apply`

**路径参数：**

- `id`: AutoUnit 包 ID

**请求参数：**

```json
{
  "stationIds": ["station-1-1-2"] // 必填，要取消应用的工位 ID 列表
}
```

**成功响应：**

```json
{
  "code": 200,
  "message": "取消应用成功",
  "data": null
}
```

---

### 7.5 获取工位的所有绑定信息

**接口说明：** 获取指定工位绑定的界面、部署清单和应用的 AutoUnit 包

**请求方式：** `GET`

**请求路径：** `/stations/{stationId}/bindings`

**路径参数：**

- `stationId`: 工位 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "stationId": "station-1-1-1",
    "stationName": "工位 A1",
    "stationCode": "ST-A1",
    "stationPath": "上海工厂 / 生产线 A / 工位 A1",
    "interfaces": [
      {
        "id": "interface-001",
        "name": "生产监控界面",
        "layout": "grid",
        "bindTime": "2025-01-15 10:30:00"
      }
    ],
    "deploymentManifests": [
      {
        "id": "manifest-001",
        "name": "生产线A部署清单",
        "version": "1.0.0",
        "bindTime": "2025-01-15 10:35:00"
      }
    ],
    "autounitPackages": [
      {
        "id": "pkg-001",
        "name": "AutoUnit Core",
        "version": "1.2.0",
        "applyTime": "2025-01-15 10:40:00"
      }
    ]
  }
}
```

**说明：**

- 驱动包不绑定工位，因此不返回驱动包信息

---

## 8. 日志管理

### 8.1 获取操作日志列表

**接口说明：** 获取系统操作日志列表（支持筛选和搜索）

**请求方式：** `GET`

**请求路径：** `/logs`

**查询参数：**

| 参数名    | 类型   | 必填 | 说明                                                                                                       |
| --------- | ------ | ---- | ---------------------------------------------------------------------------------------------------------- |
| page      | number | 否   | 页码，默认 1                                                                                               |
| pageSize  | number | 否   | 每页条数，默认 20                                                                                          |
| search    | string | 否   | 搜索关键词（操作人/描述）                                                                                  |
| operation | string | 否   | 操作类型：`create` / `update` / `delete` / `upload` / `bind` / `unbind`                                    |
| result    | string | 否   | 操作结果：`success` / `failed`                                                                             |
| startTime | string | 否   | 开始时间（格式：YYYY-MM-DD HH:mm:ss）                                                                      |
| endTime   | string | 否   | 结束时间（格式：YYYY-MM-DD HH:mm:ss）                                                                      |
| module    | string | 否   | 操作模块：`厂区管理` / `线体管理` / `工位管理` / `驱动包管理` / `AutoUnit包` / `界面管理` / `部署清单管理` |

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "id": "log-001",
        "operation": "create", // 操作类型
        "module": "厂区管理", // 操作模块
        "operator": "admin", // 操作人
        "operatorId": "user-001", // 操作人 ID
        "role": "管理员", // 操作人角色
        "result": "success", // 操作结果：success / failed
        "time": "2025-01-15 10:30:15",
        "description": "创建厂区 \"上海工厂\"",
        "ip": "192.168.1.100", // 客户端 IP
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
        "changes": {
          // 变更详情
          "name": "上海工厂",
          "location": "上海浦东新区",
          "status": "active"
        },
        "error": null // 错误信息（失败时）
      },
      {
        "id": "log-002",
        "operation": "upload",
        "module": "驱动包管理",
        "operator": "user1",
        "operatorId": "user-002",
        "role": "普通用户",
        "result": "success",
        "time": "2025-01-15 09:45:30",
        "description": "上传 Java 驱动包 \"PLC 驱动 v1.0.0\"",
        "ip": "192.168.1.101",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
        "changes": {
          "fileName": "plc-driver-1.0.0.zip",
          "type": "java",
          "version": "1.0.0",
          "size": 2048000
        },
        "error": null
      },
      {
        "id": "log-003",
        "operation": "update",
        "module": "工位管理",
        "operator": "user2",
        "operatorId": "user-003",
        "role": "普通用户",
        "result": "failed",
        "time": "2025-01-14 14:10:05",
        "description": "尝试更新工位 \"工位 B1\" 配置",
        "ip": "192.168.1.102",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
        "changes": null,
        "error": "Permission denied: User does not have edit permission for this station"
      }
    ],
    "total": 150,
    "page": 1,
    "pageSize": 15
  }
}
```

---

### 8.2 获取日志详情

**接口说明：** 获取指定日志的详细信息

**请求方式：** `GET`

**请求路径：** `/logs/{id}`

**路径参数：**

- `id`: 日志 ID

**成功响应：**

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "log-001",
    "operation": "create",
    "module": "厂区管理",
    "operator": "admin",
    "operatorId": "user-001",
    "role": "管理员",
    "result": "success",
    "time": "2025-01-15 10:30:15",
    "description": "创建厂区 \"上海工厂\"",
    "ip": "192.168.1.100",
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "changes": {
      "name": "上海工厂",
      "location": "上海浦东新区",
      "status": "active"
    },
    "error": null,
    "requestUrl": "/api/v1/facilities/factory",
    "requestMethod": "POST",
    "responseTime": 150, // 响应时间（毫秒）
    "targetId": "factory-1", // 操作目标 ID
    "targetType": "factory" // 操作目标类型
  }
}
```

---

### 8.3 导出日志

**接口说明：** 导出日志文件为 CSV 格式

**请求方式：** `POST`

**请求路径：** `/logs/export`

**请求参数：**

```json
{
  "filters": {
    // 可选，筛选条件（与列表接口相同）
    "operation": "create",
    "result": "success",
    "startTime": "2025-01-01 00:00:00",
    "endTime": "2025-01-31 23:59:59",
    "module": "厂区管理"
  }
}
```

**成功响应（文件流）：**

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="logs_20250115.csv"

<CSV 文件流>
```

**CSV 文件格式示例：**

```csv
"日志ID","操作类型","操作模块","操作人","角色","结果","时间","描述","IP地址"
"log-001","创建","厂区管理","admin","管理员","成功","2025-01-15 10:30:15","创建厂区 \"上海工厂\"","192.168.1.100"
"log-002","上传","驱动包管理","user1","普通用户","成功","2025-01-15 09:45:30","上传 Java 驱动包 \"PLC 驱动 v1.0.0\"","192.168.1.101"
```

---

## 9. 通用说明

### 9.1 统一响应格式

所有 API 响应均遵循统一格式：

**成功响应：**

```json
{
  "code": 200, // 状态码
  "message": "操作成功", // 提示信息
  "data": {
    /* ... */
  } // 响应数据
}
```

**失败响应：**

```json
{
  "code": 400, // 错误码
  "message": "错误信息", // 错误描述
  "data": null // 可选的错误详情
}
```

---

### 9.2 HTTP 状态码

| 状态码 | 说明                   |
| ------ | ---------------------- |
| 200    | 请求成功               |
| 201    | 创建成功               |
| 400    | 请求参数错误           |
| 401    | 未认证或认证失败       |
| 403    | 无权限访问             |
| 404    | 资源不存在             |
| 409    | 资源冲突（如重复上传） |
| 500    | 服务器内部错误         |

---

### 9.3 业务错误码

| 错误码 | 说明                    |
| ------ | ----------------------- |
| 1001   | 用户名或密码错误        |
| 1002   | Token 无效或已过期      |
| 1003   | 无操作权限              |
| 1004   | 用户名已存在            |
| 1005   | 邮箱已被注册            |
| 2001   | 厂区不存在              |
| 2002   | 线体不存在              |
| 2003   | 工位不存在              |
| 2004   | 设施已绑定，无法删除    |
| 3001   | AutoUnit 包不存在       |
| 3002   | AutoUnit 包结构校验失败 |
| 3003   | AutoUnit 包版本冲突     |
| 4001   | 驱动包不存在            |
| 4002   | 驱动包格式不支持        |
| 4003   | 驱动包版本冲突          |
| 5001   | 界面不存在              |
| 5002   | 界面配置格式错误        |
| 6001   | 部署清单不存在          |
| 6002   | 部署清单格式错误        |
| 7001   | 绑定关系已存在          |
| 7002   | 绑定关系不存在          |
| 8001   | 文件大小超出限制        |
| 8002   | 文件格式不支持          |
| 8003   | 文件上传失败            |

---

### 9.4 认证机制

**JWT Token + Cookie 混合方式**

**首次登录：**

1. 调用登录接口 `POST /auth/login`
2. 服务器返回 Token（在响应体的 `data.token` 字段）
3. 服务器同时通过 `Set-Cookie` 设置 Token 到 Cookie
4. 前端保存响应体中的 Token

**后续请求：**

请求头格式：

```
Authorization: Bearer <JWT_TOKEN>
Cookie: token=<JWT_TOKEN>
```

**说明：**

- 首次请求使用 `Authorization` 头携带 Token
- 浏览器会自动携带 Cookie 中的 Token
- 后端优先验证 Cookie 中的 Token
- Token 过期后需要重新登录

---

### 9.5 分页参数

**标准分页参数：**

| 参数名   | 类型   | 默认值 | 说明              |
| -------- | ------ | ------ | ----------------- |
| page     | number | 1      | 页码（从 1 开始） |
| pageSize | number | 20     | 每页条数          |

**分页响应格式：**

```json
{
  "list": [
    /* 数据列表 */
  ],
  "total": 100, // 总记录数
  "page": 1, // 当前页码
  "pageSize": 10, // 每页条数
  "totalPages": 10 // 总页数（可选）
}
```

---

### 9.6 文件上传限制

| 文件类型    | 大小限制 | 支持格式      |
| ----------- | -------- | ------------- |
| AutoUnit 包 | 无限制   | .zip, .tar.gz |
| Java 驱动   | 无限制   | .zip          |
| Python 驱动 | 无限制   | .zip, .tar.gz |
| C++ 驱动    | 无限制   | .dll, .so     |
| 部署清单    | 无限制   | .toml         |

---

### 9.7 时间格式

所有时间字段统一使用以下格式：

```
YYYY-MM-DD HH:mm:ss

示例：2025-01-15 10:30:00
```

---

### 9.8 排序参数（可选）

如果列表接口支持排序，可使用以下参数：

| 参数名    | 类型   | 说明                     |
| --------- | ------ | ------------------------ |
| sortBy    | string | 排序字段                 |
| sortOrder | string | 排序方式：`asc` / `desc` |

示例：

```
GET /autounit/packages?sortBy=uploadTime&sortOrder=desc
```

---

### 9.9 请求限流

暂无请求频率限制。

---

### 9.10 跨域配置

前后端分离部署，后端需支持 CORS。

**CORS 响应头：**

```
Access-Control-Allow-Origin: <前端域名>
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

---

## 已确认的关键设计

1. ✅ **Base URL**：`/publish/api/v1`
2. ✅ **认证方式**：JWT Token，首次登录 Token 在响应头，后续请求自动携带 Cookie
3. ✅ **发布操作**：状态由后端流程控制，前端仅展示和同步状态
4. ✅ **下载方式**：所有包的下载都返回文件流
5. ✅ **界面配置**：由独立的界面编辑器项目生成，本系统仅透传存储
6. ✅ **绑定关系**：
   - 界面需要绑定到工位（作为工位交互界面）
   - 部署清单需要绑定到工位（提供工位部署配置）
   - AutoUnit 包是应用到工位，而非绑定
   - 驱动包不绑定工位
7. ✅ **文件限制**：无文件大小限制
8. ✅ **分页参数**：page（默认 1）、pageSize（默认 20）
9. ✅ **日志导出**：仅支持 CSV 格式
10. ✅ **请求限流**：暂无限流

---

## 附录

### A. 完整的接口列表

#### 认证相关

- `POST /publish/api/v1/auth/register` - 用户注册
- `POST /publish/api/v1/auth/login` - 用户登录
- `POST /publish/api/v1/auth/logout` - 用户登出
- `GET /publish/api/v1/auth/userInfo` - 获取当前用户信息
- `GET /publish/api/v1/auth/users/search` - 用户列表模糊搜索

#### 设施管理

- `GET /publish/api/v1/facilities/tree` - 获取设施树
- `POST /publish/api/v1/facilities/factory` - 创建厂区
- `PUT /publish/api/v1/facilities/factory/{id}` - 更新厂区
- `DELETE /publish/api/v1/facilities/factory/{id}` - 删除厂区
- `POST /publish/api/v1/facilities/line` - 创建线体
- `PUT /publish/api/v1/facilities/line/{id}` - 更新线体
- `DELETE /publish/api/v1/facilities/line/{id}` - 删除线体
- `POST /publish/api/v1/facilities/station` - 创建工位
- `PUT /publish/api/v1/facilities/station/{id}` - 更新工位
- `DELETE /publish/api/v1/facilities/station/{id}` - 删除工位
- `GET /publish/api/v1/facilities/stations/search` - 工位模糊搜索

#### AutoUnit 包管理

- `GET /publish/api/v1/autounit/packages` - 获取包列表
- `POST /publish/api/v1/autounit/packages/upload` - 上传包
- `PUT /publish/api/v1/autounit/packages/{id}/status` - 更新包状态
- `DELETE /publish/api/v1/autounit/packages/{id}/recall` - 撤回包
- `GET /publish/api/v1/autounit/packages/{id}/download` - 下载包
- `GET /publish/api/v1/autounit/packages/{id}` - 获取包详情
- `POST /publish/api/v1/autounit/packages/{id}/apply` - 应用包到工位
- `DELETE /publish/api/v1/autounit/packages/{id}/apply` - 取消包在工位的应用

#### 驱动包管理

- `GET /publish/api/v1/drivers/packages` - 获取驱动包列表
- `POST /publish/api/v1/drivers/packages/upload` - 上传驱动包
- `POST /publish/api/v1/drivers/packages/{id}/publish` - 发布驱动包
- `POST /publish/api/v1/drivers/packages/{id}/unpublish` - 下架驱动包
- `DELETE /publish/api/v1/drivers/packages/{id}/recall` - 撤回驱动包
- `GET /publish/api/v1/drivers/packages/{id}/download` - 下载驱动包
- `GET /publish/api/v1/drivers/packages/{id}` - 获取驱动包详情

#### 界面管理

- `GET /publish/api/v1/interfaces` - 获取界面列表
- `POST /publish/api/v1/interfaces` - 创建界面
- `PUT /publish/api/v1/interfaces/{id}/info` - 更新界面信息
- `PUT /publish/api/v1/interfaces/{id}/config` - 更新界面配置
- `DELETE /publish/api/v1/interfaces/{id}` - 删除界面
- `GET /publish/api/v1/interfaces/{id}` - 获取界面详情
- `GET /publish/api/v1/interfaces/{id}/preview` - 预览界面
- `GET /publish/api/v1/interfaces/{id}/download` - 下载界面配置文件

#### 部署清单管理

- `GET /publish/api/v1/deployment/manifests` - 获取部署清单列表
- `POST /publish/api/v1/deployment/manifests/upload` - 上传部署清单
- `GET /publish/api/v1/deployment/manifests/{id}` - 获取部署清单详情
- `PUT /publish/api/v1/deployment/manifests/{id}` - 更新部署清单信息
- `DELETE /publish/api/v1/deployment/manifests/{id}` - 删除部署清单
- `GET /publish/api/v1/deployment/manifests/{id}/download` - 下载部署清单
- `POST /publish/api/v1/deployment/manifests/{id}/bind` - 绑定部署清单到工位
- `DELETE /publish/api/v1/deployment/manifests/{id}/bind` - 解绑部署清单

#### 工位绑定

- `POST /publish/api/v1/bindings/interface` - 绑定界面到工位
- `DELETE /publish/api/v1/bindings/interface` - 解绑界面
- `GET /publish/api/v1/stations/{stationId}/bindings` - 获取工位的绑定信息

#### 日志管理

- `GET /publish/api/v1/logs` - 获取日志列表
- `GET /publish/api/v1/logs/{id}` - 获取日志详情
- `POST /publish/api/v1/logs/export` - 导出日志

---

**文档版本：** v1.0  
**最后更新：** 2025-01-15  
**维护者：** [待填写]  
**联系方式：** [待填写]
