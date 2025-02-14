# Telegram Bot V2

A telegram bot to hook AI agents.

数据库表建立:
```sql
-- 建库
DROP DATABASE IF EXISTS `telegram_bot_v2`;
CREATE DATABASE `telegram_bot_v2`;

USE `telegram_bot_v2`;

-- 用户建表
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
  `id` bigint PRIMARY KEY NOT NULL COMMENT 'id',
  `first_name` varchar(100) NOT NULL COMMENT '名',
  `last_name` varchar(100) NOT NULL COMMENT '姓',
  `full_name` varchar(200) NOT NULL COMMENT '全名',
  `is_bot` tinyint(1) NOT NULL COMMENT '是否是机器人',
  `language_code` varchar(50) NOT NULL COMMENT '语言代码',
  `remark` varchar(200) NOT NULL DEFAULT '' COMMENT '备注',
  `is_ban` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否被封禁',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 会话建表
DROP TABLE IF EXISTS `t_session`;
CREATE TABLE `t_session` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `user_id` bigint NOT NULL COMMENT '用户 id',
  `name` varchar(50) NOT NULL COMMENT '名称',
  `factory` varchar(50) NOT NULL COMMENT '工厂',
  `model` varchar(50) NOT NULL COMMENT '模型',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位',
  UNIQUE KEY `user_id_name` (`user_id`,`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 问题建表
DROP TABLE IF EXISTS `t_question`;
CREATE TABLE `t_question` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `session_id` bigint NOT NULL COMMENT '会话 id',
  `parent_id` bigint NOT NULL COMMENT '关联父级问题 id',
  `type` tinyint NOT NULL COMMENT '问题数据类型',
  `content` LONGTEXT NOT NULL COMMENT '问题内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;

-- 回复建表
DROP TABLE IF EXISTS `t_answer`;
CREATE TABLE `t_answer` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `session_id` bigint NOT NULL COMMENT '会话 id',
  `question_id` bigint NOT NULL COMMENT '问题 id',
  `type` tinyint NOT NULL COMMENT '回复数据类型',
  `content` LONGTEXT NOT NULL COMMENT '回复内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 灰度建表
DROP TABLE IF EXISTS `t_grey`;
CREATE TABLE `t_grey` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `grey_enum` tinyint NOT NULL DEFAULT '0' COMMENT '灰度枚举值',
  `user_id` bigint NOT NULL COMMENT '用户 id',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 分析建表
DROP TABLE IF EXISTS `t_analysis`;
CREATE TABLE `t_analysis` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `user_id` bigint NOT NULL COMMENT '用户 id',
  `month` tinyint NOT NULL COMMENT '月',
  `year` tinyint NOT NULL COMMENT '年',
  `domain` varchar(255) NOT NULL DEFAULT '' COMMENT '提问领域',
  `activity_index` tinyint NOT NULL COMMENT '活跃指数',
  `keyword` varchar(255) NOT NULL DEFAULT '' COMMENT '提问关键词',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 地区建表
DROP TABLE IF EXISTS `t_area`;
CREATE TABLE `t_area` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(20) NOT NULL COMMENT '名称',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 币种建表
DROP TABLE IF EXISTS `t_currency`;
CREATE TABLE `t_currency` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(20) NOT NULL COMMENT '名称',
  `area_id` bigint NOT NULL COMMENT '地区 id',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订阅计划建表
DROP TABLE IF EXISTS `t_subscription_plan`;
CREATE TABLE `t_subscription_plan` (
  `id` bigint PRIMARY KEY NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(50) NOT NULL COMMENT '名称',
  `price` int NOT NULL COMMENT '价格',
  `currency_id` bigint NOT NULL COMMENT '币种 id',
  `area_id` bigint NOT NULL COMMENT '地区 id',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 支付方式建表
DROP TABLE IF EXISTS `t_payment_account`;
CREATE TABLE `t_payment_account` (
  `id` bigint PRIMARY KEY NOT NULL COMMENT 'id',
  `user_id` bigint NOT NULL COMMENT '用户 id',
  `balance` bigint NOT NULL DEFAULT '0' COMMENT '余额',
  `lock_status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '锁状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 支付历史建表
DROP TABLE IF EXISTS `t_payment_history`;
CREATE TABLE `t_payment_history` (
  `id` bigint PRIMARY KEY NOT NULL COMMENT 'id',
  `bill_id` bigint NOT NULL DEFAULT '0' COMMENT '关联账单 id',
  `action_type` tinyint(1) NOT NULL DEFAULT '0' COMMENT '动帐类型',
  `amount` bigint NOT NULL COMMENT '金额',
  `payment_type` tinyint NOT NULL DEFAULT '0' COMMENT '支付方式',
  `payment_platform` varchar(50) NOT NULL DEFAULT '' COMMENT '支付平台',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 账单建表
DROP TABLE IF EXISTS `t_bill`;
CREATE TABLE `t_bill` (
  `id` bigint PRIMARY KEY NOT NULL COMMENT 'id',
  `amount` bigint NOT NULL COMMENT '金额',
  `title` varchar(50) NOT NULL DEFAULT '' COMMENT '标题',
  `content` varchar(255) NOT NULL DEFAULT '' COMMENT '内容',
  `remark` varchar(255) NOT NULL DEFAULT '' COMMENT '备注',
  `payment_status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '支付状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '删除标记位'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
