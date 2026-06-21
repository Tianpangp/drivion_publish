-- ========================================
-- 发布系统数据库初始化脚本
-- 版本: v1.0
-- 创建时间: 2025-01-15
-- 说明: 支持厂区/线体/工位管理、AutoUnit包、驱动包、界面、部署清单等功能
-- ========================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ========================================
-- 1. 用户和认证相关表
-- ========================================

-- 角色表
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `code` varchar(50) NOT NULL COMMENT '角色代码',
  `name` varchar(100) NOT NULL COMMENT '角色名称（中文）',
  `name_en` varchar(100) NOT NULL COMMENT '角色名称（英文）',
  `description` varchar(255) DEFAULT NULL COMMENT '角色描述',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统角色定义';

-- 用户表
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` varchar(64) NOT NULL COMMENT '用户ID',
  `username` varchar(64) NOT NULL COMMENT '用户名',
  `password` varchar(255) NOT NULL COMMENT '密码（加密存储）',
  `nickname` varchar(128) DEFAULT NULL COMMENT '昵称',
  `email` varchar(128) DEFAULT NULL COMMENT '邮箱',
  `avatar` varchar(512) DEFAULT NULL COMMENT '头像URL',
  `role` bigint unsigned NOT NULL DEFAULT 6 COMMENT '角色ID，参看roles表',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 权限表
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions` (
  `id` varchar(64) NOT NULL COMMENT '权限ID',
  `code` varchar(128) NOT NULL COMMENT '权限代码，如：facility:create',
  `name` varchar(128) NOT NULL COMMENT '权限名称',
  `description` varchar(255) DEFAULT NULL COMMENT '权限描述',
  `category` varchar(64) DEFAULT NULL COMMENT '权限分类',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- 用户权限关联表
DROP TABLE IF EXISTS `user_permissions`;
CREATE TABLE `user_permissions` (
  `id` varchar(64) NOT NULL COMMENT 'ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `permission_id` varchar(64) NOT NULL COMMENT '权限ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_permission` (`user_id`, `permission_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户权限关联表';

-- ========================================
-- 2. 设施管理相关表（厂区/线体/工位）
-- ========================================

-- 厂区表
DROP TABLE IF EXISTS `factories`;
CREATE TABLE `factories` (
  `id` varchar(64) NOT NULL COMMENT '厂区ID',
  `name` varchar(128) NOT NULL COMMENT '厂区名称',
  `code` varchar(64) DEFAULT NULL COMMENT '厂区编号',
  `description` text COMMENT '厂区描述',
  `location` varchar(255) DEFAULT NULL COMMENT '地址',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) NOT NULL COMMENT '创建人ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_status` (`status`),
  KEY `idx_name` (`name`),
  KEY `idx_is_deleted` (`is_deleted`),
  KEY `idx_create_user_id` (`create_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='厂区表';

-- 线体表
DROP TABLE IF EXISTS `lines`;
CREATE TABLE `lines` (
  `id` varchar(64) NOT NULL COMMENT '线体ID',
  `factory_id` varchar(64) NOT NULL COMMENT '所属厂区ID',
  `name` varchar(128) NOT NULL COMMENT '线体名称',
  `code` varchar(64) DEFAULT NULL COMMENT '线体编号',
  `description` text COMMENT '线体描述',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) NOT NULL COMMENT '创建人ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_factory_id` (`factory_id`),
  KEY `idx_status` (`status`),
  KEY `idx_name` (`name`),
  KEY `idx_is_deleted` (`is_deleted`),
  KEY `idx_create_user_id` (`create_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='线体表';

-- 工位表
DROP TABLE IF EXISTS `stations`;
CREATE TABLE `stations` (
  `id` varchar(64) NOT NULL COMMENT '工位ID',
  `line_id` varchar(64) NOT NULL COMMENT '所属线体ID',
  `name` varchar(128) NOT NULL COMMENT '工位名称',
  `code` varchar(64) DEFAULT NULL COMMENT '工位编号',
  `description` text COMMENT '工位描述',
  `ip` varchar(64) DEFAULT NULL COMMENT '工位设备IP',
  `mac` varchar(64) DEFAULT NULL COMMENT '工位设备MAC地址',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) NOT NULL COMMENT '创建人ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_line_id` (`line_id`),
  KEY `idx_status` (`status`),
  KEY `idx_name` (`name`),
  KEY `idx_is_deleted` (`is_deleted`),
  KEY `idx_create_user_id` (`create_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工位表';

-- ========================================
-- 3. AutoUnit 包管理相关表
-- ========================================

-- AutoUnit 包表
DROP TABLE IF EXISTS `autounit_packages`;
CREATE TABLE `autounit_packages` (
  `id` varchar(64) NOT NULL COMMENT '包ID',
  `name` varchar(255) NOT NULL COMMENT '包名称',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `version` varchar(64) NOT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) NOT NULL COMMENT '文件存储路径',
  `status` enum('published','unpublished','testing') NOT NULL DEFAULT 'unpublished' COMMENT '状态：published-已发布, unpublished-未发布, testing-测试中',
  `description` text COMMENT '包描述',
  `python_version` varchar(32) DEFAULT NULL COMMENT 'Python版本要求',
  `dependencies` json DEFAULT NULL COMMENT 'Python依赖列表（JSON数组）',
  `readme` text COMMENT 'README内容',
  `changelog` text COMMENT '更新日志',
  `md5` varchar(64) NOT NULL COMMENT '文件MD5',
  `sha256` varchar(128) DEFAULT NULL COMMENT '文件SHA256',
  `upload_user_id` varchar(64) NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `publish_user_id` varchar(64) DEFAULT NULL COMMENT '发布用户ID',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_version` (`name`, `version`),
  KEY `idx_status` (`status`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AutoUnit包表';

-- AutoUnit 包与工位应用关系表
DROP TABLE IF EXISTS `autounit_station_applications`;
CREATE TABLE `autounit_station_applications` (
  `id` varchar(64) NOT NULL COMMENT 'ID',
  `package_id` varchar(64) NOT NULL COMMENT 'AutoUnit包ID',
  `station_id` varchar(64) NOT NULL COMMENT '工位ID',
  `apply_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '应用时间',
  `apply_user_id` varchar(64) DEFAULT NULL COMMENT '应用操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_package_station` (`package_id`, `station_id`),
  KEY `idx_package_id` (`package_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AutoUnit包与工位应用关系表';

-- ========================================
-- 4. 驱动包管理相关表
-- ========================================

-- 驱动包表
DROP TABLE IF EXISTS `driver_packages`;
CREATE TABLE `driver_packages` (
  `id` varchar(64) NOT NULL COMMENT '驱动包ID',
  `name` varchar(255) NOT NULL COMMENT '驱动名称',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `type` enum('java','python','cpp') NOT NULL COMMENT '驱动类型：java, python, cpp',
  `version` varchar(64) NOT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) NOT NULL COMMENT '文件存储路径',
  `status` enum('published','unpublished','testing') NOT NULL DEFAULT 'unpublished' COMMENT '状态：published-已发布, unpublished-未发布, testing-测试中',
  `description` text COMMENT '驱动描述',
  `protocol` varchar(128) DEFAULT NULL COMMENT '支持的协议',
  `manufacturer` varchar(128) DEFAULT NULL COMMENT '设备厂商',
  `device_model` varchar(128) DEFAULT NULL COMMENT '设备型号',
  `supported_platforms` json DEFAULT NULL COMMENT '支持的平台（JSON数组）',
  `api_doc_url` varchar(512) DEFAULT NULL COMMENT 'API文档地址',
  `readme` text COMMENT 'README内容',
  `md5` varchar(64) NOT NULL COMMENT '文件MD5',
  `sha256` varchar(128) DEFAULT NULL COMMENT '文件SHA256',
  `upload_user_id` varchar(64) NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `publish_user_id` varchar(64) DEFAULT NULL COMMENT '发布用户ID',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `unpublish_user_id` varchar(64) DEFAULT NULL COMMENT '下架用户ID',
  `unpublish_time` datetime DEFAULT NULL COMMENT '下架时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_version_type` (`name`, `version`, `type`),
  KEY `idx_type` (`type`),
  KEY `idx_status` (`status`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='驱动包表';

-- ========================================
-- 5. 界面管理相关表
-- ========================================

-- 界面表
DROP TABLE IF EXISTS `interfaces`;
CREATE TABLE `interfaces` (
  `id` varchar(64) NOT NULL COMMENT '界面ID',
  `name` varchar(255) NOT NULL COMMENT '界面名称',
  `description` text COMMENT '界面描述',
  `json_file_path` varchar(512) DEFAULT NULL COMMENT 'JSON文件在对象存储中的路径',
  `file_size` bigint DEFAULT NULL COMMENT 'JSON文件大小（字节）',
  `file_md5` varchar(32) DEFAULT NULL COMMENT 'JSON文件MD5值',
  `thumbnail` varchar(512) DEFAULT NULL COMMENT '缩略图URL',
  `create_user` varchar(64) NOT NULL COMMENT '创建用户ID',
  `last_edit_user` varchar(64) DEFAULT NULL COMMENT '最后编辑用户ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_create_user` (`create_user`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='界面表';

-- 界面与工位绑定关系表
DROP TABLE IF EXISTS `interface_station_bindings`;
CREATE TABLE `interface_station_bindings` (
  `id` varchar(64) NOT NULL COMMENT 'ID',
  `interface_id` varchar(64) NOT NULL COMMENT '界面ID',
  `station_id` varchar(64) NOT NULL COMMENT '工位ID',
  `bind_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `bind_user_id` varchar(64) DEFAULT NULL COMMENT '绑定操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_interface_station` (`interface_id`, `station_id`),
  KEY `idx_interface_id` (`interface_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='界面与工位绑定关系表';

-- ========================================
-- 6. 部署清单管理相关表
-- ========================================

-- 部署清单表
DROP TABLE IF EXISTS `deployment_manifests`;
CREATE TABLE `deployment_manifests` (
  `id` varchar(64) NOT NULL COMMENT '部署清单ID',
  `name` varchar(255) NOT NULL COMMENT '清单名称',
  `description` text COMMENT '清单描述',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `version` varchar(64) DEFAULT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) NOT NULL COMMENT '文件存储路径',
  `content` longtext COMMENT 'TOML文件内容',
  `md5` varchar(64) NOT NULL COMMENT '文件MD5',
  `upload_user_id` varchar(64) NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部署清单表';

-- 部署清单与工位绑定关系表
DROP TABLE IF EXISTS `manifest_station_bindings`;
CREATE TABLE `manifest_station_bindings` (
  `id` varchar(64) NOT NULL COMMENT 'ID',
  `manifest_id` varchar(64) NOT NULL COMMENT '部署清单ID',
  `station_id` varchar(64) NOT NULL COMMENT '工位ID',
  `bind_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `bind_user_id` varchar(64) DEFAULT NULL COMMENT '绑定操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_manifest_station` (`manifest_id`, `station_id`),
  KEY `idx_manifest_id` (`manifest_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部署清单与工位绑定关系表';

-- ========================================
-- 7. 日志管理相关表
-- ========================================

-- 操作日志表
DROP TABLE IF EXISTS `operation_logs`;
CREATE TABLE `operation_logs` (
  `id` varchar(64) NOT NULL COMMENT '日志ID',
  `operation` enum('create','update','delete','upload','bind','unbind','publish','unpublish','apply','recall') NOT NULL COMMENT '操作类型',
  `module` varchar(64) NOT NULL COMMENT '操作模块：厂区管理/线体管理/工位管理/驱动包管理/AutoUnit包/界面管理/部署清单管理',
  `operator_id` varchar(64) NOT NULL COMMENT '操作人ID',
  `operator` varchar(128) NOT NULL COMMENT '操作人用户名',
  `role` varchar(64) DEFAULT NULL COMMENT '操作人角色',
  `result` enum('success','failed') NOT NULL COMMENT '操作结果：success-成功, failed-失败',
  `time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  `description` text COMMENT '操作描述',
  `ip` varchar(64) DEFAULT NULL COMMENT '客户端IP地址',
  `user_agent` varchar(512) DEFAULT NULL COMMENT '用户代理（浏览器信息）',
  `changes` json DEFAULT NULL COMMENT '变更详情（JSON格式）',
  `error` text COMMENT '错误信息（失败时）',
  `request_url` varchar(512) DEFAULT NULL COMMENT '请求URL',
  `request_method` varchar(16) DEFAULT NULL COMMENT '请求方法：GET/POST/PUT/DELETE',
  `response_time` int DEFAULT NULL COMMENT '响应时间（毫秒）',
  `target_id` varchar(64) DEFAULT NULL COMMENT '操作目标ID',
  `target_type` varchar(64) DEFAULT NULL COMMENT '操作目标类型：factory/line/station/package/interface等',
  PRIMARY KEY (`id`),
  KEY `idx_operation` (`operation`),
  KEY `idx_module` (`module`),
  KEY `idx_operator_id` (`operator_id`),
  KEY `idx_result` (`result`),
  KEY `idx_time` (`time`),
  KEY `idx_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ========================================
-- 8. 初始化数据
-- ========================================

-- 初始化角色
INSERT INTO `roles` (`id`, `code`, `name`, `name_en`, `description`, `enabled`) VALUES
(1, 'admin', '管理员', 'Administrator', '系统最高权限，管理用户、角色、配置', 1),
(2, 'developer', '开发', 'Developer', '开发人员，具备开发与部署相关权限', 1),
(3, 'tester', '测试', 'Tester', '测试人员，具备测试环境与用例管理权限', 1),
(4, 'project_manager', '项目经理', 'Project Manager', '项目管理与资源调度权限', 1),
(5, 'operator', '操作员', 'Operator', '一线操作人员，具备生产运行相关权限', 1),
(6, 'process_engineer', '工艺', 'Process Engineer', '工艺工程师，负责工艺参数与流程维护', 1);

-- 插入默认管理员用户（密码：admin123）
INSERT INTO `users` (`id`, `username`, `password`, `nickname`, `role`, `email`) VALUES
('user-001', 'admin', '$2b$12$lQDkom73vja5GkeUKGcV5u/RS.3uncDilyB/JFCzHaqxV0vzmAF0G', '管理员', 1, 'admin@example.com');

-- 插入默认权限
INSERT INTO `permissions` (`id`, `code`, `name`, `description`, `category`) VALUES
('perm-001', 'facility:create', '创建设施', '创建厂区/线体/工位', '设施管理'),
('perm-002', 'facility:edit', '编辑设施', '编辑厂区/线体/工位信息', '设施管理'),
('perm-003', 'facility:delete', '删除设施', '删除厂区/线体/工位', '设施管理'),
('perm-004', 'package:upload', '上传包', '上传AutoUnit包和驱动包', '包管理'),
('perm-005', 'package:publish', '发布包', '发布AutoUnit包和驱动包', '包管理'),
('perm-006', 'interface:create', '创建界面', '创建新的界面', '界面管理'),
('perm-007', 'interface:edit', '编辑界面', '编辑界面配置', '界面管理'),
('perm-008', 'interface:delete', '删除界面', '删除界面', '界面管理'),
('perm-009', 'deployment:upload', '上传部署清单', '上传部署清单文件', '部署管理'),
('perm-010', 'deployment:bind', '绑定部署清单', '绑定部署清单到工位', '部署管理'),
('perm-011', 'log:view', '查看日志', '查看操作日志', '日志管理'),
('perm-012', 'log:export', '导出日志', '导出日志文件', '日志管理');

-- 给管理员分配所有权限
INSERT INTO `user_permissions` (`id`, `user_id`, `permission_id`)
SELECT 
  CONCAT('up-', LPAD((@row_number:=@row_number + 1), 3, '0')) AS id,
  'user-001' AS user_id,
  `id` AS permission_id
FROM `permissions`, (SELECT @row_number:=0) AS t;

-- MVP 演示设施/包/绑定数据：用于真实 DB 路径验证 Exe bundle
INSERT INTO `factories` (`id`, `name`, `code`, `description`, `location`, `create_user_id`) VALUES
('factory-demo', 'Demo Factory', 'DEMO-FAC', 'MVP演示厂区', 'Localhost', 'user-001');

INSERT INTO `lines` (`id`, `factory_id`, `name`, `code`, `description`, `create_user_id`) VALUES
('line-demo', 'factory-demo', 'Demo Line', 'DEMO-LINE', 'MVP演示线体', 'user-001');

INSERT INTO `stations` (`id`, `line_id`, `name`, `code`, `description`, `ip`, `mac`, `create_user_id`) VALUES
('station-demo-db', 'line-demo', 'Demo DB Station', 'DEMO-DB-001', '通过真实数据库聚合的MVP演示工位', '127.0.0.1', '00:00:00:00:00:01', 'user-001');

INSERT INTO `autounit_packages` (`id`, `name`, `file_name`, `version`, `size`, `file_path`, `status`, `description`, `python_version`, `dependencies`, `md5`, `sha256`, `upload_user_id`, `publish_user_id`, `publish_time`) VALUES
('au-demo-db', 'demo-autounit-package', 'demo-autounit.zip', '0.1.0', 0, 'local/demo-autounit.zip', 'published', 'MVP演示AutoUnit包', '>=3.11', JSON_ARRAY(), 'demo-md5-au', 'demo-sha-au', 'user-001', 'user-001', CURRENT_TIMESTAMP);

INSERT INTO `driver_packages` (`id`, `name`, `file_name`, `type`, `version`, `size`, `file_path`, `status`, `description`, `protocol`, `manufacturer`, `device_model`, `supported_platforms`, `md5`, `sha256`, `upload_user_id`, `publish_user_id`, `publish_time`) VALUES
('drv-virtual-motion-db', 'virtual-motion-driver', 'virtual-motion-driver.zip', 'python', '0.1.0', 0, 'local/virtual-motion-driver.zip', 'published', '虚拟运动控制驱动', 'virtual', 'Drivion', 'VirtualMotion', JSON_ARRAY('macos', 'linux'), 'demo-md5-motion', 'demo-sha-motion', 'user-001', 'user-001', CURRENT_TIMESTAMP),
('drv-virtual-io-db', 'virtual-io-driver', 'virtual-io-driver.zip', 'python', '0.1.0', 0, 'local/virtual-io-driver.zip', 'published', '虚拟IO驱动', 'virtual', 'Drivion', 'VirtualIO', JSON_ARRAY('macos', 'linux'), 'demo-md5-io', 'demo-sha-io', 'user-001', 'user-001', CURRENT_TIMESTAMP),
('drv-virtual-camera-db', 'virtual-camera-driver', 'virtual-camera-driver.zip', 'python', '0.1.0', 0, 'local/virtual-camera-driver.zip', 'published', '虚拟相机驱动', 'virtual', 'Drivion', 'VirtualCamera', JSON_ARRAY('macos', 'linux'), 'demo-md5-camera', 'demo-sha-camera', 'user-001', 'user-001', CURRENT_TIMESTAMP);

INSERT INTO `interfaces` (`id`, `name`, `description`, `json_file_path`, `file_size`, `file_md5`, `thumbnail`, `create_user`, `last_edit_user`) VALUES
('ui-demo-db', 'Demo Operator UI', 'MVP演示操作界面', 'local/demo-ui.json', 0, 'demo-md5-ui', NULL, 'user-001', 'user-001');

INSERT INTO `deployment_manifests` (`id`, `name`, `description`, `file_name`, `version`, `size`, `file_path`, `content`, `md5`, `upload_user_id`) VALUES
('mf-demo-db', 'Publish DB Demo MVP', '通过真实数据库聚合的MVP演示部署清单', 'demo_manifest.toml', '0.1.0', 4096, 'local/demo_manifest.toml', '[manifest]
id = "publish-db-demo-mvp"
name = "Publish DB Demo MVP"
version = "0.1.0"
workstation_name = "station-demo-db"

drivers = [
  { name = "virtual-motion-driver" },
  { name = "virtual-io-driver" },
  { name = "virtual-camera-driver" }
]

[[autounits]]
id = "db-demo-pick"
name = "DB Demo Pick"
priority = 10
required_locks = ["axis_x", "axis_z", "gripper", "top_camera"]
preconditions = [
  { type = "machine_state", expected = "running" },
  { type = "flag", name = "calibrated", expected = true },
  { type = "io", name = "start_button", expected = true }
]
steps = [
  { name = "Move X to pick position", action = "axis_move", params = { axis = "axis_x", position = 100, speed = 50 } },
  { name = "Move Z down", action = "axis_move", params = { axis = "axis_z", position = 50, speed = 30 } },
  { name = "Close gripper", action = "gripper_close", params = { name = "gripper" } },
  { name = "Capture top image", action = "camera_capture", params = { camera = "top_camera" } },
  { name = "Mock vision confirmation", action = "vision_check", params = { workflow = "check_pick", passed = true, score = 0.98 } },
  { name = "Move Z home", action = "axis_move", params = { axis = "axis_z", position = 0, speed = 40 } }
]

[[autounits]]
id = "db-demo-place"
name = "DB Demo Place"
priority = 20
required_locks = ["axis_x", "axis_y", "axis_z", "gripper"]
preconditions = [
  { type = "machine_state", expected = "running" },
  { type = "flag", name = "material_ready", expected = true }
]
steps = [
  { name = "Move X to tray", action = "axis_move", params = { axis = "axis_x", position = 240, speed = 80 } },
  { name = "Move Y to tray", action = "axis_move", params = { axis = "axis_y", position = 120, speed = 80 } },
  { name = "Move Z place height", action = "axis_move", params = { axis = "axis_z", position = 35, speed = 30 } },
  { name = "Open gripper", action = "gripper_open", params = { name = "gripper" } },
  { name = "Move Z home", action = "axis_move", params = { axis = "axis_z", position = 0, speed = 40 } },
  { name = "Signal complete", action = "io_write", params = { name = "cycle_complete", value = true } }
]', 'demo-md5-mf', 'user-001');

INSERT INTO `autounit_station_applications` (`id`, `package_id`, `station_id`, `apply_user_id`) VALUES
('asa-demo-db', 'au-demo-db', 'station-demo-db', 'user-001');

INSERT INTO `manifest_station_bindings` (`id`, `manifest_id`, `station_id`, `bind_user_id`) VALUES
('msb-demo-db', 'mf-demo-db', 'station-demo-db', 'user-001');

INSERT INTO `interface_station_bindings` (`id`, `interface_id`, `station_id`, `bind_user_id`) VALUES
('isb-demo-db', 'ui-demo-db', 'station-demo-db', 'user-001');

-- ========================================
-- 9. 视图定义（可选，便于查询）
-- ========================================

-- 工位完整路径视图
DROP VIEW IF EXISTS `v_station_full_path`;
CREATE VIEW `v_station_full_path` AS
SELECT 
  s.id AS station_id,
  s.name AS station_name,
  s.code AS station_code,
  s.status AS station_status,
  l.id AS line_id,
  l.name AS line_name,
  l.code AS line_code,
  f.id AS factory_id,
  f.name AS factory_name,
  f.code AS factory_code,
  CONCAT(f.name, ' / ', l.name, ' / ', s.name) AS full_path
FROM `stations` s
JOIN `lines` l ON s.line_id = l.id
JOIN `factories` f ON l.factory_id = f.id;

-- AutoUnit包绑定工位统计视图
DROP VIEW IF EXISTS `v_autounit_package_stats`;
CREATE VIEW `v_autounit_package_stats` AS
SELECT 
  p.id,
  p.name,
  p.version,
  p.status,
  p.upload_time,
  COUNT(a.station_id) AS bound_station_count
FROM `autounit_packages` p
LEFT JOIN `autounit_station_applications` a ON p.id = a.package_id
GROUP BY p.id, p.name, p.version, p.status, p.upload_time;

-- 驱动包统计视图
DROP VIEW IF EXISTS `v_driver_package_stats`;
CREATE VIEW `v_driver_package_stats` AS
SELECT 
  p.id,
  p.name,
  p.type,
  p.version,
  p.status,
  p.upload_time
FROM `driver_packages` p;

-- 界面绑定统计视图
DROP VIEW IF EXISTS `v_interface_stats`;
CREATE VIEW `v_interface_stats` AS
SELECT 
  i.id,
  i.name,
  i.create_time,
  COUNT(b.station_id) AS bound_station_count
FROM `interfaces` i
LEFT JOIN `interface_station_bindings` b ON i.id = b.interface_id
GROUP BY i.id, i.name, i.create_time;

-- ========================================
-- 完成
-- ========================================

SET FOREIGN_KEY_CHECKS = 1;

-- 数据库初始化完成
SELECT '数据库初始化完成！' AS message;
