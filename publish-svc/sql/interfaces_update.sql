-- 完整的 interfaces 表结构（重建版本）
DROP TABLE IF EXISTS `interfaces`;

CREATE TABLE `interfaces` (
  `id` VARCHAR(64) NOT NULL DEFAULT (UUID()) COMMENT '界面ID',
  `name` VARCHAR(100) NOT NULL COMMENT '界面名称',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '界面描述',
  `json_file_path` VARCHAR(500) DEFAULT NULL COMMENT 'JSON文件在MinIO中的存储路径',
  `file_size` BIGINT DEFAULT NULL COMMENT 'JSON文件大小（字节）',
  `file_md5` VARCHAR(32) DEFAULT NULL COMMENT 'JSON文件MD5值',
  `thumbnail` VARCHAR(500) DEFAULT NULL COMMENT '缩略图URL',
  `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_user` VARCHAR(36) NOT NULL COMMENT '创建人ID',
  `last_edit_user` VARCHAR(36) DEFAULT NULL COMMENT '最后编辑人ID',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否删除 0-否 1-是',
  PRIMARY KEY (`id`),
  INDEX `idx_name` (`name`),
  INDEX `idx_create_user` (`create_user`),
  INDEX `idx_create_time` (`create_time`),
  INDEX `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='界面管理表';
