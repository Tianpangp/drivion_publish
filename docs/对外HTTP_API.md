# Publish 对外 HTTP API

## 1. 通用约定

- Base URL：`http(s)://<publish-host>/publish/api/v1/exe`
- JSON 编码：UTF-8
- 鉴权：`Authorization: Bearer <credential>`
- 时间：`generatedAt` 为 ISO 8601 UTC；管理数据时间字段为 `YYYY-MM-DD HH:mm:ss`
- 制品上传上限：100 MiB（104,857,600 bytes）

JSON 成功响应：

```json
{"code": 200, "message": "操作成功", "data": {}}
```

FastAPI 参数/鉴权错误：

```json
{"detail": "错误说明"}
```

客户端必须以 HTTP 状态码为主，不应只判断 JSON `code`。

## 2. 接口列表

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/equipment/{equipmentId}/deployment` | 查询设备层级和当前 AutoUnit 绑定 |
| `GET` | `/equipment/{equipmentId}/autounit/download` | 下载设备当前绑定的 AutoUnit |
| `GET` | `/equipment/{equipmentId}/hal?name=&version=` | 按精确名称/版本获取 HAL 元数据 |
| `GET` | `/equipment/{equipmentId}/hal/download?name=&version=` | 按精确名称/版本下载 HAL |
| `POST` | `/artifacts/autounit` | 提交新 AutoUnit 版本 |
| `PUT` | `/artifacts/autounit/{artifactId}` | 覆盖更新待测试 AutoUnit 版本 |
| `POST` | `/artifacts/hal` | 提交新 HAL 版本 |
| `PUT` | `/artifacts/hal/{artifactId}` | 覆盖更新待测试 HAL 版本 |

`GET /stations/{stationId}/bundle` 是旧的工位/部署清单模型兼容接口，已废弃。新 Exe 不得基于它开发。

## 3. 设备部署查询

```http
GET /equipment/{equipmentId}/deployment
```

SSO Permission：`platform.equipment.read`，并校验设备或上级资源 scope。

`data.autoUnit` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | Publish 内部精确版本 ID |
| `name` | string | 展示名称 |
| `packageId` | string | AutoUnit 稳定包标识 |
| `version` | string | 精确版本 |
| `module` | string | Python 模块名 |
| `status` | string | Publish 生命周期状态 |
| `published` | boolean | 是否为 `published` |
| `releaseWarning` | string/null | 未发布绑定的警告 |
| `fileName` | string | 原始上传文件名 |
| `size` | integer | 文件字节数 |
| `md5` | string | MD5，主要用于兼容 |
| `sha256` | string | SHA-256，Exe 必须校验 |
| `downloadApiPath` | string | 同一 Publish Host 上的下载路径 |
| `metadata.dependencies` | array | AutoUnit 声明的依赖 |

`autoUnit=null` 表示未绑定。`409` 表示绑定指向了已删除/已下架版本，应由 Publish 管理员修复。

## 4. AutoUnit 下载

```http
GET /equipment/{equipmentId}/autounit/download
```

SSO Permission：`platform.equipment.read` + `artifact.package.download`，两项都需匹配设备或上级资源 scope。

成功返回 `application/octet-stream`：

```http
Content-Disposition: attachment; filename*=UTF-8''<encoded-name>
ETag: "<sha256-or-md5>"
X-Artifact-SHA256: <sha256>
X-Artifact-MD5: <md5>
```

设备未绑定时返回 `404`。

## 5. HAL 解析与下载

```http
GET /equipment/{equipmentId}/hal?name=<name>&version=<version>
```

SSO Permission：`platform.equipment.read` + `artifact.package.read`。响应 `data.downloadApiPath` 已带 URL 编码后的名称和版本。

```http
GET /equipment/{equipmentId}/hal/download?name=<name>&version=<version>
```

SSO Permission：`platform.equipment.read` + `artifact.package.download`。成功响应头与 AutoUnit 下载一致。

HAL 已下架或不存在时返回 `404`。未发布但未下架的精确版本仍会返回，并在 `status` 中显示真实状态。

## 6. 制品提交

AutoUnit：

```http
POST /artifacts/autounit
Content-Type: multipart/form-data

file=<archive>
```

SSO Permission：`autounit.definition.publish`。

HAL：

```http
POST /artifacts/hal
Content-Type: multipart/form-data

file=<archive>
```

SSO Permission：`hal.driver.publish`。两个提交接口都不校验资源 scope，但会做高风险 introspection。

成功时 `data.status=pending_testing`。常见错误：

| HTTP | 原因 |
| --- | --- |
| `400` | 空文件、元数据缺失/错误、缺少 HAL entry point |
| `403` | 缺少对应 Publish Permission，或权限已撤销 |
| `409` | 相同制品身份和版本已存在 |
| `413` | 压缩包超过 100 MiB |
| `503` | 未配置本地 API Key，或 SSO introspection 不可用 |

## 7. 待测试版本更新

```http
PUT /artifacts/autounit/{artifactId}
PUT /artifacts/hal/{artifactId}
Content-Type: multipart/form-data

file=<archive>
```

权限与各自的 `POST` 相同。只允许更新 `pending_testing` 版本。身份/版本不一致或版本已锁定时返回 `400`，`artifactId` 不存在返回 `404`。

## 8. 健康检查与 OpenAPI

以下路径不属于 Exe API 前缀：

- `GET /health`：Publish 进程健康检查。
- `GET /openapi.json`：OpenAPI Schema。
- `GET /docs`：Swagger UI。
