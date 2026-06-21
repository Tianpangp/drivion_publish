# 发布系统后端服务 (publish-svc)

## 数据库设计总结

### 📋 概述

根据 API 文档设计的完整数据库架构，支持发布系统的所有核心功能模块。

---

### 🗂️ 数据库表结构

#### 1. **用户和认证模块** (3 张表)

| 表名               | 说明           | 核心字段                                    |
| ------------------ | -------------- | ------------------------------------------- |
| `users`            | 用户表         | id, username, password, role, email, avatar |
| `permissions`      | 权限表         | id, code, name, category                    |
| `user_permissions` | 用户权限关联表 | user_id, permission_id                      |

**支持功能：**

- JWT Token 认证
- 基于角色的权限控制 (RBAC)
- 管理员和普通用户角色区分

---

#### 2. **设施管理模块** (3 张表)

| 表名        | 说明   | 核心字段                                                             |
| ----------- | ------ | -------------------------------------------------------------------- |
| `factories` | 厂区表 | id, name, code, location, status, is_deleted, create_user_id         |
| `lines`     | 线体表 | id, factory_id, name, code, status, is_deleted, create_user_id       |
| `stations`  | 工位表 | id, line_id, name, code, ip, mac, status, is_deleted, create_user_id |

**支持功能：**

- 三级树形结构：厂区 → 线体 → 工位
- 软删除支持（is_deleted 标记）
- 创建人追溯（create_user_id）
- 级联删除和查询
- 支持设施编号、IP、MAC 等属性

---

#### 3. **AutoUnit 包管理模块** (2 张表)

| 表名                            | 说明               | 核心字段                                           |
| ------------------------------- | ------------------ | -------------------------------------------------- |
| `autounit_packages`             | AutoUnit 包表      | id, name, version, status, file_path, dependencies |
| `autounit_station_applications` | 包与工位应用关系表 | package_id, station_id, apply_time                 |

**支持功能：**

- Python 包上传和版本管理
- 包状态管理（已发布/未发布/测试中）
- 依赖声明 (JSON 格式)
- 包应用到工位（非绑定关系）
- MD5/SHA256 文件校验

---

#### 4. **驱动包管理模块** (2 张表)

| 表名                      | 说明                     | 核心字段                                        |
| ------------------------- | ------------------------ | ----------------------------------------------- |
| `driver_packages`         | 驱动包表                 | id, name, type, version, protocol, manufacturer |
| `driver_station_bindings` | 驱动包与工位绑定表(备用) | driver_id, station_id                           |

**支持功能：**

- 多类型驱动支持（Java/Python/C++）
- 发布/下架状态管理
- 设备厂商和型号信息
- 支持平台声明 (JSON 格式)
- API 文档 URL 关联

---

#### 5. **界面管理模块** (2 张表)

| 表名                         | 说明                 | 核心字段                    |
| ---------------------------- | -------------------- | --------------------------- |
| `interfaces`                 | 界面表               | id, name, config, thumbnail |
| `interface_station_bindings` | 界面与工位绑定关系表 | interface_id, station_id    |

**支持功能：**

- 界面配置存储 (JSON 格式，由界面编辑器生成)
- 界面与工位绑定关系
- 缩略图支持

---

#### 6. **部署清单管理模块** (2 张表)

| 表名                        | 说明                 | 核心字段                              |
| --------------------------- | -------------------- | ------------------------------------- |
| `deployment_manifests`      | 部署清单表           | id, name, version, file_path, content |
| `manifest_station_bindings` | 清单与工位绑定关系表 | manifest_id, station_id               |

**支持功能：**

- TOML 文件上传和管理
- 清单内容存储
- 清单与工位绑定关系
- 版本管理

---

#### 7. **日志管理模块** (1 张表)

| 表名             | 说明       | 核心字段                                           |
| ---------------- | ---------- | -------------------------------------------------- |
| `operation_logs` | 操作日志表 | operation, module, operator, result, time, changes |

**支持功能：**

- 完整的操作审计日志
- 操作类型和模块分类
- 成功/失败状态记录
- 变更详情 (JSON 格式)
- IP 地址和浏览器信息记录
- 支持日志导出（CSV 格式）

---

### 📊 数据库视图

为便于查询，创建了以下视图：

| 视图名                     | 说明                           |
| -------------------------- | ------------------------------ |
| `v_station_full_path`      | 工位完整路径（厂区/线体/工位） |
| `v_autounit_package_stats` | AutoUnit 包绑定统计            |
| `v_driver_package_stats`   | 驱动包绑定统计                 |
| `v_interface_stats`        | 界面绑定统计                   |

---

### 🔑 关键设计特性

#### 1. **绑定关系设计**

- ✅ 界面 → 工位：一对多绑定（`interface_station_bindings`）
- ✅ 部署清单 → 工位：一对多绑定（`manifest_station_bindings`）
- ✅ AutoUnit 包 → 工位：应用关系（`autounit_station_applications`）
- ⚠️ 驱动包：不绑定工位（保留表以备扩展）

#### 2. **软删除机制**

- 厂区、线体、工位支持软删除（`is_deleted` 字段）
- 软删除记录不会物理删除，仅标记为已删除
- 可追溯创建人（`create_user_id` 字段）

#### 3. **文件存储**

- 所有上传文件使用 `file_path` 字段存储物理路径
- 支持 MD5/SHA256 校验
- 支持文件大小无限制

#### 4. **权限系统**

- 12 个预定义权限
- 支持细粒度权限控制
- 管理员默认拥有所有权限

#### 5. **状态管理**

- 用户状态：active / inactive
- 设施状态：active / inactive
- 包状态：published / unpublished / testing

#### 6. **JSON 字段应用**

- AutoUnit 包依赖列表 (`dependencies`)
- 驱动包支持平台 (`supported_platforms`)
- 界面配置 (`config`)
- 操作日志变更详情 (`changes`)

---

### 🚀 使用方法

#### 初始化数据库

```bash
# MySQL/MariaDB
mysql -u root -p < init.sql

# 或者指定数据库
mysql -u root -p your_database_name < init.sql
```

#### 默认账号

- **用户名**: `admin`
- **密码**: `admin123` (需要根据实际加密算法修改 SQL 中的哈希值)
- **角色**: 管理员
- **权限**: 所有权限

---

### 📈 数据库统计

| 类别     | 数量  |
| -------- | ----- |
| 核心表   | 14 张 |
| 关系表   | 4 张  |
| 视图     | 4 个  |
| 默认权限 | 12 个 |

---

### 🔧 技术规范

- **字符集**: `utf8mb4`
- **排序规则**: `utf8mb4_unicode_ci`
- **存储引擎**: `InnoDB`
- **主键类型**: `varchar(64)`
- **时间格式**: `datetime`，自动维护 `create_time` 和 `update_time`

---

### 📝 注意事项

1. **密码加密**：默认管理员密码需要根据实际使用的加密算法（如 bcrypt）生成哈希值
2. **文件存储**：需要配置文件上传目录和访问路径
3. **外键约束**：当前未启用外键约束，建议根据实际需求添加
4. **索引优化**：已为常用查询字段添加索引，可根据实际查询模式调整
5. **JSON 字段**：需要 MySQL 5.7.8+ 或 MariaDB 10.2.7+ 支持

---

### 🔗 相关文档

- [API 文档](../API文档.md)
- [发布界面需求文档](../publish-ui/发布界面需求文档.md)

---

### 📅 版本信息

- **版本**: v1.0
- **创建时间**: 2025-01-15
- **兼容 API**: v1.0
