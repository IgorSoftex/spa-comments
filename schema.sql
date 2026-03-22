-- SPA Comments - Database Schema for MySQL Workbench
-- Compatible with: MySQL 8.0+
-- https://github.com/IgorSoftex/spa-comments

-- ------------------------------------------------------------
-- Schema
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `spa_comments`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `spa_comments`;

-- ------------------------------------------------------------
-- django_content_type
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id`        INT          NOT NULL AUTO_INCREMENT,
  `app_label` VARCHAR(100) NOT NULL,
  `model`     VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_content_type` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_permission
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id`              INT          NOT NULL AUTO_INCREMENT,
  `name`            VARCHAR(255) NOT NULL,
  `content_type_id` INT          NOT NULL,
  `codename`        VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_permission` (`content_type_id`, `codename`),
  CONSTRAINT `fk_permission_content_type`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `django_content_type` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_group
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id`   INT          NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_group_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_group_permissions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id`            BIGINT NOT NULL AUTO_INCREMENT,
  `group_id`      INT    NOT NULL,
  `permission_id` INT    NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_group_perm` (`group_id`, `permission_id`),
  CONSTRAINT `fk_gp_group`
    FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_gp_permission`
    FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_user
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id`           INT          NOT NULL AUTO_INCREMENT,
  `password`     VARCHAR(128) NOT NULL,
  `last_login`   DATETIME     NULL,
  `is_superuser` TINYINT(1)   NOT NULL DEFAULT 0,
  `username`     VARCHAR(150) NOT NULL,
  `first_name`   VARCHAR(150) NOT NULL DEFAULT '',
  `last_name`    VARCHAR(150) NOT NULL DEFAULT '',
  `email`        VARCHAR(254) NOT NULL DEFAULT '',
  `is_staff`     TINYINT(1)   NOT NULL DEFAULT 0,
  `is_active`    TINYINT(1)   NOT NULL DEFAULT 1,
  `date_joined`  DATETIME     NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_user_groups
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id`       BIGINT NOT NULL AUTO_INCREMENT,
  `user_id`  INT    NOT NULL,
  `group_id` INT    NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_group` (`user_id`, `group_id`),
  CONSTRAINT `fk_ug_user`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ug_group`
    FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- auth_user_user_permissions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id`            BIGINT NOT NULL AUTO_INCREMENT,
  `user_id`       INT    NOT NULL,
  `permission_id` INT    NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_perm` (`user_id`, `permission_id`),
  CONSTRAINT `fk_up_user`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_up_permission`
    FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- django_session
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key`  VARCHAR(40) NOT NULL,
  `session_data` LONGTEXT    NOT NULL,
  `expire_date`  DATETIME    NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `idx_session_expire` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- django_admin_log
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id`              INT          NOT NULL AUTO_INCREMENT,
  `action_time`     DATETIME     NOT NULL,
  `object_id`       LONGTEXT     NULL,
  `object_repr`     VARCHAR(200) NOT NULL,
  `action_flag`     SMALLINT     NOT NULL,
  `change_message`  LONGTEXT     NOT NULL,
  `content_type_id` INT          NULL,
  `user_id`         INT          NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_log_content_type`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `django_content_type` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_log_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- django_migrations
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id`      BIGINT       NOT NULL AUTO_INCREMENT,
  `app`     VARCHAR(255) NOT NULL,
  `name`    VARCHAR(255) NOT NULL,
  `applied` DATETIME     NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- comments_comment  (main application table)
-- backend/apps/comments/models.py :: class Comment
-- ============================================================
CREATE TABLE IF NOT EXISTS `comments_comment` (
  `id`         BIGINT       NOT NULL AUTO_INCREMENT,
  `user_name`  VARCHAR(255) NOT NULL,
  `email`      VARCHAR(254) NOT NULL,
  `home_page`  VARCHAR(200) NULL DEFAULT NULL,
  `text`       LONGTEXT     NOT NULL,
  `image`      VARCHAR(100) NULL DEFAULT NULL,
  `attachment` VARCHAR(100) NULL DEFAULT NULL,
  `parent_id`  BIGINT       NULL DEFAULT NULL,
  `created_at` DATETIME     NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_comment_created_at` (`created_at`),
  KEY `idx_comment_parent_id`  (`parent_id`),
  KEY `idx_comment_user_name`  (`user_name`),
  KEY `idx_comment_email`      (`email`),
  CONSTRAINT `fk_comment_parent`
    FOREIGN KEY (`parent_id`)
    REFERENCES `comments_comment` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
