-- MySQL dump 10.13  Distrib 9.3.0, for macos15.2 (arm64)
--
-- Host: localhost    Database: drivion_db
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `autounit_packages`
--

DROP TABLE IF EXISTS `autounit_packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `autounit_packages` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '包ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '包名称',
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件名',
  `version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件存储路径',
  `status` enum('published','unpublished','testing') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unpublished' COMMENT '状态：published-已发布, unpublished-未发布, testing-测试中',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '包描述',
  `python_version` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Python版本要求',
  `dependencies` json DEFAULT NULL COMMENT 'Python依赖列表（JSON数组）',
  `readme` text COLLATE utf8mb4_unicode_ci COMMENT 'README内容',
  `changelog` text COLLATE utf8mb4_unicode_ci COMMENT '更新日志',
  `md5` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件MD5',
  `sha256` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文件SHA256',
  `upload_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `publish_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布用户ID',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_version` (`name`,`version`),
  KEY `idx_status` (`status`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AutoUnit包表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autounit_packages`
--

LOCK TABLES `autounit_packages` WRITE;
/*!40000 ALTER TABLE `autounit_packages` DISABLE KEYS */;
/*!40000 ALTER TABLE `autounit_packages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autounit_station_applications`
--

DROP TABLE IF EXISTS `autounit_station_applications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `autounit_station_applications` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID',
  `package_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'AutoUnit包ID',
  `station_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工位ID',
  `apply_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '应用时间',
  `apply_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '应用操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_package_station` (`package_id`,`station_id`),
  KEY `idx_package_id` (`package_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AutoUnit包与工位应用关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autounit_station_applications`
--

LOCK TABLES `autounit_station_applications` WRITE;
/*!40000 ALTER TABLE `autounit_station_applications` DISABLE KEYS */;
/*!40000 ALTER TABLE `autounit_station_applications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deployment_manifests`
--

DROP TABLE IF EXISTS `deployment_manifests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `deployment_manifests` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部署清单ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '清单名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '清单描述',
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件名',
  `version` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件存储路径',
  `content` longtext COLLATE utf8mb4_unicode_ci COMMENT 'TOML文件内容',
  `md5` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件MD5',
  `upload_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部署清单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deployment_manifests`
--

LOCK TABLES `deployment_manifests` WRITE;
/*!40000 ALTER TABLE `deployment_manifests` DISABLE KEYS */;
/*!40000 ALTER TABLE `deployment_manifests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `driver_packages`
--

DROP TABLE IF EXISTS `driver_packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `driver_packages` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '驱动包ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '驱动名称',
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件名',
  `type` enum('java','python','cpp') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '驱动类型：java, python, cpp',
  `version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `size` bigint NOT NULL COMMENT '文件大小（字节）',
  `file_path` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件存储路径',
  `status` enum('published','unpublished','testing') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unpublished' COMMENT '状态：published-已发布, unpublished-未发布, testing-测试中',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '驱动描述',
  `protocol` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支持的协议',
  `manufacturer` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备厂商',
  `device_model` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备型号',
  `supported_platforms` json DEFAULT NULL COMMENT '支持的平台（JSON数组）',
  `api_doc_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API文档地址',
  `readme` text COLLATE utf8mb4_unicode_ci COMMENT 'README内容',
  `md5` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件MD5',
  `sha256` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文件SHA256',
  `upload_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '上传用户ID',
  `upload_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `publish_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布用户ID',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `unpublish_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '下架用户ID',
  `unpublish_time` datetime DEFAULT NULL COMMENT '下架时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name_version_type` (`name`,`version`,`type`),
  KEY `idx_type` (`type`),
  KEY `idx_status` (`status`),
  KEY `idx_upload_user_id` (`upload_user_id`),
  KEY `idx_upload_time` (`upload_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='驱动包表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `driver_packages`
--

LOCK TABLES `driver_packages` WRITE;
/*!40000 ALTER TABLE `driver_packages` DISABLE KEYS */;
/*!40000 ALTER TABLE `driver_packages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `factories`
--

DROP TABLE IF EXISTS `factories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `factories` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '厂区ID',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '厂区名称',
  `code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '厂区编号',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '厂区描述',
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '地址',
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建人ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_status` (`status`),
  KEY `idx_name` (`name`),
  KEY `idx_is_deleted` (`is_deleted`),
  KEY `idx_create_user_id` (`create_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='厂区表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `factories`
--

LOCK TABLES `factories` WRITE;
/*!40000 ALTER TABLE `factories` DISABLE KEYS */;
/*!40000 ALTER TABLE `factories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `interface_station_bindings`
--

DROP TABLE IF EXISTS `interface_station_bindings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interface_station_bindings` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID',
  `interface_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '界面ID',
  `station_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工位ID',
  `bind_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `bind_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '绑定操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_interface_station` (`interface_id`,`station_id`),
  KEY `idx_interface_id` (`interface_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='界面与工位绑定关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `interface_station_bindings`
--

LOCK TABLES `interface_station_bindings` WRITE;
/*!40000 ALTER TABLE `interface_station_bindings` DISABLE KEYS */;
/*!40000 ALTER TABLE `interface_station_bindings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `interfaces`
--

DROP TABLE IF EXISTS `interfaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interfaces` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '界面ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '界面名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '界面描述',
  `config` json DEFAULT NULL COMMENT '界面配置（JSON格式，由界面编辑器生成）',
  `thumbnail` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '缩略图URL',
  `create_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建用户ID',
  `last_edit_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最后编辑用户ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_create_user_id` (`create_user_id`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='界面表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `interfaces`
--

LOCK TABLES `interfaces` WRITE;
/*!40000 ALTER TABLE `interfaces` DISABLE KEYS */;
/*!40000 ALTER TABLE `interfaces` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lines`
--

DROP TABLE IF EXISTS `lines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lines` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '线体ID',
  `factory_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属厂区ID',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '线体名称',
  `code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '线体编号',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '线体描述',
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建人ID',
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lines`
--

LOCK TABLES `lines` WRITE;
/*!40000 ALTER TABLE `lines` DISABLE KEYS */;
/*!40000 ALTER TABLE `lines` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manifest_station_bindings`
--

DROP TABLE IF EXISTS `manifest_station_bindings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `manifest_station_bindings` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID',
  `manifest_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部署清单ID',
  `station_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工位ID',
  `bind_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `bind_user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '绑定操作人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_manifest_station` (`manifest_id`,`station_id`),
  KEY `idx_manifest_id` (`manifest_id`),
  KEY `idx_station_id` (`station_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部署清单与工位绑定关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manifest_station_bindings`
--

LOCK TABLES `manifest_station_bindings` WRITE;
/*!40000 ALTER TABLE `manifest_station_bindings` DISABLE KEYS */;
/*!40000 ALTER TABLE `manifest_station_bindings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation_logs`
--

DROP TABLE IF EXISTS `operation_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operation_logs` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志ID',
  `operation` enum('create','update','delete','upload','bind','unbind','publish','unpublish','apply','recall') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型',
  `module` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作模块：厂区管理/线体管理/工位管理/驱动包管理/AutoUnit包/界面管理/部署清单管理',
  `operator_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作人ID',
  `operator` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作人用户名',
  `role` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作人角色',
  `result` enum('success','failed') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作结果：success-成功, failed-失败',
  `time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '操作描述',
  `ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端IP地址',
  `user_agent` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理（浏览器信息）',
  `changes` json DEFAULT NULL COMMENT '变更详情（JSON格式）',
  `error` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息（失败时）',
  `request_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求URL',
  `request_method` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求方法：GET/POST/PUT/DELETE',
  `response_time` int DEFAULT NULL COMMENT '响应时间（毫秒）',
  `target_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作目标ID',
  `target_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作目标类型：factory/line/station/package/interface等',
  PRIMARY KEY (`id`),
  KEY `idx_operation` (`operation`),
  KEY `idx_module` (`module`),
  KEY `idx_operator_id` (`operator_id`),
  KEY `idx_result` (`result`),
  KEY `idx_time` (`time`),
  KEY `idx_target` (`target_type`,`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_logs`
--

LOCK TABLES `operation_logs` WRITE;
/*!40000 ALTER TABLE `operation_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `operation_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限ID',
  `code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限代码，如：facility:create',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限名称',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '权限描述',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '权限分类',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions`
--

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` VALUES ('perm-001','facility:create','创建设施','创建厂区/线体/工位','设施管理','2025-10-07 16:31:02'),('perm-002','facility:edit','编辑设施','编辑厂区/线体/工位信息','设施管理','2025-10-07 16:31:02'),('perm-003','facility:delete','删除设施','删除厂区/线体/工位','设施管理','2025-10-07 16:31:02'),('perm-004','package:upload','上传包','上传AutoUnit包和驱动包','包管理','2025-10-07 16:31:02'),('perm-005','package:publish','发布包','发布AutoUnit包和驱动包','包管理','2025-10-07 16:31:02'),('perm-006','interface:create','创建界面','创建新的界面','界面管理','2025-10-07 16:31:02'),('perm-007','interface:edit','编辑界面','编辑界面配置','界面管理','2025-10-07 16:31:02'),('perm-008','interface:delete','删除界面','删除界面','界面管理','2025-10-07 16:31:02'),('perm-009','deployment:upload','上传部署清单','上传部署清单文件','部署管理','2025-10-07 16:31:02'),('perm-010','deployment:bind','绑定部署清单','绑定部署清单到工位','部署管理','2025-10-07 16:31:02'),('perm-011','log:view','查看日志','查看操作日志','日志管理','2025-10-07 16:31:02'),('perm-012','log:export','导出日志','导出日志文件','日志管理','2025-10-07 16:31:02');
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stations`
--

DROP TABLE IF EXISTS `stations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stations` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工位ID',
  `line_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属线体ID',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工位名称',
  `code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '工位编号',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '工位描述',
  `ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '工位设备IP',
  `mac` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '工位设备MAC地址',
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除：0-未删除, 1-已删除',
  `create_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建人ID',
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stations`
--

LOCK TABLES `stations` WRITE;
/*!40000 ALTER TABLE `stations` DISABLE KEYS */;
/*!40000 ALTER TABLE `stations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_permissions`
--

DROP TABLE IF EXISTS `user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_permissions` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID',
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `permission_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_permission` (`user_id`,`permission_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户权限关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_permissions`
--

LOCK TABLES `user_permissions` WRITE;
/*!40000 ALTER TABLE `user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码（加密存储）',
  `nickname` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '昵称',
  `email` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `avatar` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像URL',
  `role` BIGINT UNSIGNED COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 6 COMMENT '角色，参看roles表',
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '状态：active-启用, inactive-停用',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('3885cc7e-a401-11f0-b32d-769587e4e1ba','testuser','$2b$12$XWT.gWITkLzER8.tgBGSzu/XVkP2igEJB3wy6zJDgbp3ZNAxz5OZC','测试用户','test@example.com',NULL,'user','active','2025-10-08 04:42:40','2025-10-08 04:42:40');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `v_autounit_package_stats`
--

DROP TABLE IF EXISTS `v_autounit_package_stats`;
/*!50001 DROP VIEW IF EXISTS `v_autounit_package_stats`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_autounit_package_stats` AS SELECT 
 1 AS `id`,
 1 AS `name`,
 1 AS `version`,
 1 AS `status`,
 1 AS `upload_time`,
 1 AS `bound_station_count`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_driver_package_stats`
--

DROP TABLE IF EXISTS `v_driver_package_stats`;
/*!50001 DROP VIEW IF EXISTS `v_driver_package_stats`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_driver_package_stats` AS SELECT 
 1 AS `id`,
 1 AS `name`,
 1 AS `type`,
 1 AS `version`,
 1 AS `status`,
 1 AS `upload_time`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_interface_stats`
--

DROP TABLE IF EXISTS `v_interface_stats`;
/*!50001 DROP VIEW IF EXISTS `v_interface_stats`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_interface_stats` AS SELECT 
 1 AS `id`,
 1 AS `name`,
 1 AS `create_time`,
 1 AS `bound_station_count`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `v_autounit_package_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_autounit_package_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_autounit_package_stats` AS select `p`.`id` AS `id`,`p`.`name` AS `name`,`p`.`version` AS `version`,`p`.`status` AS `status`,`p`.`upload_time` AS `upload_time`,count(`a`.`station_id`) AS `bound_station_count` from (`autounit_packages` `p` left join `autounit_station_applications` `a` on((`p`.`id` = `a`.`package_id`))) group by `p`.`id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_driver_package_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_driver_package_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_driver_package_stats` AS select `p`.`id` AS `id`,`p`.`name` AS `name`,`p`.`type` AS `type`,`p`.`version` AS `version`,`p`.`status` AS `status`,`p`.`upload_time` AS `upload_time` from `driver_packages` `p` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_interface_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_interface_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_interface_stats` AS select `i`.`id` AS `id`,`i`.`name` AS `name`,`i`.`create_time` AS `create_time`,count(`b`.`station_id`) AS `bound_station_count` from (`interfaces` `i` left join `interface_station_bindings` `b` on((`i`.`id` = `b`.`interface_id`))) group by `i`.`id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-08 14:49:55
