CREATE DATABASE IF NOT EXISTS aops DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_bin;
use aops;
CREATE TABLE IF NOT EXISTS `domain` (
  `domain_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '业务域id',
  `domain_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '业务域名称',
  `cluster_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '集群id',
  `priority` tinyint(1) unsigned zerofill NOT NULL COMMENT '优先级(未用)',
  `sync_status` tinyint(1) unsigned zerofill NULL DEFAULT NULL,
  PRIMARY KEY (`domain_id`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `domain_conf_info` (
  `domain_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '业务域id',
  `conf_path` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '' COMMENT '配置名称',
  `conf_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '配置内容',
  PRIMARY KEY (`domain_id`,`conf_path`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `domain_host` (
  `host_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '主机id',
  `host_ip` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '' COMMENT '主机ip',
  `ipv6` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '' COMMENT '协议',
  `domain_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '业务域id',
  PRIMARY KEY (`host_id`,`domain_id`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `host_conf_sync_status`  (
  `host_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '主机id',
  `host_ip` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '' COMMENT '主机ip',
  `cluster_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '集群id',
  `domain_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '业务域id',
  `sync_status` tinyint(1) unsigned zerofill NULL DEFAULT NULL,
  PRIMARY KEY (`host_id`),
  INDEX `sync_status`(`sync_status`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `conf_trace_info` (
  `UUID` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `cluster_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `cluster_name` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `domain_name` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `host_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `host_ip` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `conf_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `conf_change_record` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`UUID`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;