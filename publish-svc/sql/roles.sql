CREATE TABLE roles (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code         VARCHAR(50)     NOT NULL UNIQUE,  -- 角色编码（系统内唯一）
  name         VARCHAR(100)    NOT NULL,         -- 角色名称（中文）
  name_en      VARCHAR(100)    NOT NULL,         -- 角色英文名称
  description  VARCHAR(255)    NULL,             -- 描述
  enabled      TINYINT(1)      NOT NULL DEFAULT 1,
  created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统角色定义';

-- 初始化角色数据
INSERT INTO roles (code, name, name_en, description) VALUES
  ('admin',            '管理员',     'Administrator',   '系统最高权限，管理用户、角色、配置'),
  ('developer',        '开发',       'Developer',       '开发人员，具备开发与部署相关权限'),
  ('tester',           '测试',       'Tester',          '测试人员，具备测试环境与用例管理权限'),
  ('project_manager',  '项目经理',   'Project Manager', '项目管理与资源调度权限'),
  ('operator',         '操作员',     'Operator',        '一线操作人员，具备生产运行相关权限'),
  ('process_engineer', '工艺',       'Process Engineer','工艺工程师，负责工艺参数与流程维护');

  