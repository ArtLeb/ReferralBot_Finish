-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: 62.217.182.228    Database: coupon_system
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.24.04.1

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
-- Table structure for table `ACTION_LOGS`
--

DROP TABLE IF EXISTS `ACTION_LOGS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ACTION_LOGS` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action_type` varchar(50) DEFAULT NULL COMMENT 'Тип действия',
  `entity_id` int DEFAULT NULL COMMENT 'ID сущности',
  `timestamp` datetime DEFAULT NULL COMMENT 'Время действия',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `ACTION_LOGS_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `USERS` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ACTION_LOGS`
--

LOCK TABLES `ACTION_LOGS` WRITE;
/*!40000 ALTER TABLE `ACTION_LOGS` DISABLE KEYS */;
/*!40000 ALTER TABLE `ACTION_LOGS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMPANIES`
--

DROP TABLE IF EXISTS `COMPANIES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPANIES` (
  `id_comp` int NOT NULL AUTO_INCREMENT,
  `Name_comp` varchar(255) NOT NULL,
  PRIMARY KEY (`id_comp`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMPANIES`
--

LOCK TABLES `COMPANIES` WRITE;
/*!40000 ALTER TABLE `COMPANIES` DISABLE KEYS */;
INSERT INTO `COMPANIES` VALUES (1,'system company'),(2,'моя компания'),(4,'AbramianIT'),(5,'AbramianIT2'),(6,'Моя 123'),(7,'Моя 123'),(8,'MyKompany'),(9,'Моя компания 123'),(10,'ArtEdIT'),(11,'qwedqwe'),(13,'1234'),(14,'123'),(15,'34df'),(16,'weryfg'),(17,'12341234');
/*!40000 ALTER TABLE `COMPANIES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMPANY_CATEGORY`
--

DROP TABLE IF EXISTS `COMPANY_CATEGORY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPANY_CATEGORY` (
  `name` varchar(256) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='ТАБЛИЦА С КАТЕГОРИЯМИ КОМПАНИЙ. ПОДОБИЕ СПРАВОЧНИКА';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMPANY_CATEGORY`
--

LOCK TABLES `COMPANY_CATEGORY` WRITE;
/*!40000 ALTER TABLE `COMPANY_CATEGORY` DISABLE KEYS */;
INSERT INTO `COMPANY_CATEGORY` VALUES ('категория 1',1),('категория 2',2),('категория 3',3),('категория 4',4),('категория 5',5),('категория 6',6),('категория 7',7),('категория 8',8),('категория 9',9),('категория 10',10),('категория 11',11),('категория 12',12),('категория 13',13);
/*!40000 ALTER TABLE `COMPANY_CATEGORY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMP_LOCATIONS`
--

DROP TABLE IF EXISTS `COMP_LOCATIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMP_LOCATIONS` (
  `id_location` int NOT NULL AUTO_INCREMENT,
  `id_comp` int NOT NULL,
  `name_loc` varchar(255) NOT NULL,
  `city` varchar(512) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `map_url` text,
  PRIMARY KEY (`id_location`),
  KEY `id_comp` (`id_comp`),
  CONSTRAINT `COMP_LOCATIONS_ibfk_1` FOREIGN KEY (`id_comp`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMP_LOCATIONS`
--

LOCK TABLES `COMP_LOCATIONS` WRITE;
/*!40000 ALTER TABLE `COMP_LOCATIONS` DISABLE KEYS */;
INSERT INTO `COMP_LOCATIONS` VALUES (2,5,'AbramianIT2','qwefqwef','qwefqwef','qwefqwef'),(3,9,'Моя компания 123','Ростов','Ленина д 1',NULL),(5,4,'фывафывафыв','фывафывафывафывафыва','фывафыва','фывафывафыва'),(6,4,'134к','134к134к','134к134к34','134к134к13'),(7,10,'ArtEdIT','Сургут','пр. Мира 32 кв. 1','https://yandex.ru/maps/-/CHHPvV~p'),(8,10,'Заячий остров','Сургут','Комсомолький 13','185022675'),(9,11,'qwedqwe','qweedqwe','qwdwqedqw','qwedqwed'),(11,13,'1234','1234','1234','1234'),(12,14,'123','234','4567','erty'),(13,15,'34df','234r','tg24','tg'),(14,17,'12341234','12341234','1234412341234','1234134');
/*!40000 ALTER TABLE `COMP_LOCATIONS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COUPONS`
--

DROP TABLE IF EXISTS `COUPONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COUPONS` (
  `id_coupon` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `coupon_type_id` int NOT NULL,
  `client_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `issued_by` int NOT NULL,
  `used_by` int DEFAULT NULL,
  `status_id` tinyint NOT NULL DEFAULT '1',
  `order_amount` decimal(10,2) DEFAULT NULL,
  `location_used` int DEFAULT NULL,
  `used_at` timestamp NULL DEFAULT NULL,
  `company_used` int DEFAULT NULL,
  PRIMARY KEY (`id_coupon`),
  UNIQUE KEY `code` (`code`),
  KEY `coupon_type_id` (`coupon_type_id`),
  KEY `issued_by` (`issued_by`),
  KEY `used_by` (`used_by`),
  KEY `location_used` (`location_used`),
  KEY `company_used` (`company_used`),
  KEY `status_id` (`status_id`),
  KEY `idx_coupons_code` (`code`),
  KEY `idx_coupons_client` (`client_id`),
  CONSTRAINT `COUPONS_ibfk_1` FOREIGN KEY (`coupon_type_id`) REFERENCES `COUPON_TYPES` (`id_coupon_type`) ON DELETE CASCADE,
  CONSTRAINT `COUPONS_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `USERS` (`id`) ON DELETE CASCADE,
  CONSTRAINT `COUPONS_ibfk_3` FOREIGN KEY (`issued_by`) REFERENCES `USERS` (`id`) ON DELETE CASCADE,
  CONSTRAINT `COUPONS_ibfk_4` FOREIGN KEY (`used_by`) REFERENCES `USERS` (`id`) ON DELETE SET NULL,
  CONSTRAINT `COUPONS_ibfk_5` FOREIGN KEY (`location_used`) REFERENCES `COMP_LOCATIONS` (`id_location`) ON DELETE SET NULL,
  CONSTRAINT `COUPONS_ibfk_6` FOREIGN KEY (`company_used`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE SET NULL,
  CONSTRAINT `COUPONS_ibfk_7` FOREIGN KEY (`status_id`) REFERENCES `COUPON_STATUSES` (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COUPONS`
--

LOCK TABLES `COUPONS` WRITE;
/*!40000 ALTER TABLE `COUPONS` DISABLE KEYS */;
/*!40000 ALTER TABLE `COUPONS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COUPON_STATUSES`
--

DROP TABLE IF EXISTS `COUPON_STATUSES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COUPON_STATUSES` (
  `id_status` tinyint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COUPON_STATUSES`
--

LOCK TABLES `COUPON_STATUSES` WRITE;
/*!40000 ALTER TABLE `COUPON_STATUSES` DISABLE KEYS */;
INSERT INTO `COUPON_STATUSES` VALUES (1,'active'),(2,'used'),(3,'expired'),(4,'cancelled');
/*!40000 ALTER TABLE `COUPON_STATUSES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COUPON_TYPES`
--

DROP TABLE IF EXISTS `COUPON_TYPES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COUPON_TYPES` (
  `id_coupon_type` int NOT NULL AUTO_INCREMENT,
  `code_prefix` varchar(10) NOT NULL,
  `company_id` int NOT NULL,
  `location_id` int NOT NULL,
  `discount_percent` decimal(5,2) NOT NULL,
  `commission_percent` decimal(5,2) NOT NULL,
  `require_all_groups` tinyint(1) DEFAULT '0',
  `usage_limit` int DEFAULT '0',
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `company_agent_id` bigint NOT NULL,
  `location_agent_id` bigint NOT NULL,
  `days_for_used` bigint NOT NULL,
  `agent_agree` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_coupon_type`),
  KEY `company_id` (`company_id`),
  KEY `location_id` (`location_id`),
  CONSTRAINT `COUPON_TYPES_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE CASCADE,
  CONSTRAINT `COUPON_TYPES_ibfk_2` FOREIGN KEY (`location_id`) REFERENCES `COMP_LOCATIONS` (`id_location`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COUPON_TYPES`
--

LOCK TABLES `COUPON_TYPES` WRITE;
/*!40000 ALTER TABLE `COUPON_TYPES` DISABLE KEYS */;
/*!40000 ALTER TABLE `COUPON_TYPES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GROUP_COUPONS`
--

DROP TABLE IF EXISTS `GROUP_COUPONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `GROUP_COUPONS` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coupon_type_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `coupon_type_id` (`coupon_type_id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `GROUP_COUPONS_ibfk_1` FOREIGN KEY (`coupon_type_id`) REFERENCES `COUPON_TYPES` (`id_coupon_type`) ON DELETE CASCADE,
  CONSTRAINT `GROUP_COUPONS_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `TG_GROUPS` (`id_tg_group`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GROUP_COUPONS`
--

LOCK TABLES `GROUP_COUPONS` WRITE;
/*!40000 ALTER TABLE `GROUP_COUPONS` DISABLE KEYS */;
/*!40000 ALTER TABLE `GROUP_COUPONS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LOC_CATS`
--

DROP TABLE IF EXISTS `LOC_CATS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LOC_CATS` (
  `comp_id` int DEFAULT NULL,
  `id_location` int DEFAULT NULL,
  `id_category` bigint DEFAULT NULL,
  KEY `LOC_CATS_COMPANIES_id_comp_fk` (`comp_id`),
  KEY `LOC_CATS_COMP_LOCATIONS_id_location_fk` (`id_location`),
  KEY `LOC_CATS_COMPANY_CATEGORY_id_fk` (`id_category`),
  CONSTRAINT `LOC_CATS_COMP_LOCATIONS_id_location_fk` FOREIGN KEY (`id_location`) REFERENCES `COMP_LOCATIONS` (`id_location`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `LOC_CATS_COMPANIES_id_comp_fk` FOREIGN KEY (`comp_id`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `LOC_CATS_COMPANY_CATEGORY_id_fk` FOREIGN KEY (`id_category`) REFERENCES `COMPANY_CATEGORY` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LOC_CATS`
--

LOCK TABLES `LOC_CATS` WRITE;
/*!40000 ALTER TABLE `LOC_CATS` DISABLE KEYS */;
INSERT INTO `LOC_CATS` VALUES (5,2,1),(9,3,2),(4,5,4),(4,6,8),(10,7,4),(10,8,2),(10,8,3),(10,8,6),(13,11,9),(13,11,7),(14,12,2),(14,12,5),(15,13,8),(17,14,5);
/*!40000 ALTER TABLE `LOC_CATS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TAGS`
--

DROP TABLE IF EXISTS `TAGS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `TAGS` (
  `id_tag` int NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(255) NOT NULL,
  `entity_type` enum('coupon','user','company') NOT NULL,
  `entity_id` int NOT NULL,
  PRIMARY KEY (`id_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TAGS`
--

LOCK TABLES `TAGS` WRITE;
/*!40000 ALTER TABLE `TAGS` DISABLE KEYS */;
/*!40000 ALTER TABLE `TAGS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TG_GROUPS`
--

DROP TABLE IF EXISTS `TG_GROUPS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `TG_GROUPS` (
  `id_tg_group` int NOT NULL AUTO_INCREMENT,
  `group_id` bigint NOT NULL,
  `company_id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_tg_group`),
  KEY `company_id` (`company_id`),
  CONSTRAINT `TG_GROUPS_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TG_GROUPS`
--

LOCK TABLES `TG_GROUPS` WRITE;
/*!40000 ALTER TABLE `TG_GROUPS` DISABLE KEYS */;
/*!40000 ALTER TABLE `TG_GROUPS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USERS`
--

DROP TABLE IF EXISTS `USERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USERS` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_tg` bigint NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `tel_num` char(11) NOT NULL,
  `reg_date` date NOT NULL,
  `role` varchar(50) DEFAULT 'client',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_tg` (`id_tg`),
  KEY `idx_users_id_tg` (`id_tg`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USERS`
--

LOCK TABLES `USERS` WRITE;
/*!40000 ALTER TABLE `USERS` DISABLE KEYS */;
INSERT INTO `USERS` VALUES (1,1659829486,NULL,'Edgar','Abramian','','2025-07-11','client'),(2,185022675,NULL,'Artem','Shtennikov','','2025-07-11','client'),(9,6685789921,NULL,'Apostol','','','2025-07-20','client'),(11,6175393932,NULL,'.','.','','2025-07-22','client');
/*!40000 ALTER TABLE `USERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USERS_ROLES`
--

DROP TABLE IF EXISTS `USERS_ROLES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USERS_ROLES` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `company_id` int NOT NULL,
  `location_id` int DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `changed_by` bigint NOT NULL,
  `changed_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `is_locked` tinyint(1) DEFAULT '0',
  `role` enum('admin','partner','client','tech_admin') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `location_id` (`location_id`),
  KEY `idx_user_roles_user` (`user_id`),
  KEY `idx_user_roles_company` (`company_id`),
  CONSTRAINT `USERS_ROLES_ibfk_3` FOREIGN KEY (`company_id`) REFERENCES `COMPANIES` (`id_comp`) ON DELETE CASCADE,
  CONSTRAINT `USERS_ROLES_ibfk_4` FOREIGN KEY (`location_id`) REFERENCES `COMP_LOCATIONS` (`id_location`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USERS_ROLES`
--

LOCK TABLES `USERS_ROLES` WRITE;
/*!40000 ALTER TABLE `USERS_ROLES` DISABLE KEYS */;
INSERT INTO `USERS_ROLES` VALUES (3,1659829486,4,NULL,'2025-07-19','2026-07-19',1,'2025-07-19 14:50:33',0,'partner'),(4,1659829486,5,2,'2025-07-20','2026-07-20',1,'2025-07-20 11:14:12',0,'partner'),(6,185022675,10,7,'2025-07-22','2026-07-22',2,'2025-07-21 20:44:02',0,'partner'),(9,6175393932,15,13,'2025-07-22','2026-07-22',6175393932,'2025-07-21 23:11:45',0,'partner'),(10,1659829486,17,14,'2025-07-22','2026-07-22',1659829486,'2025-07-21 23:59:33',0,'partner'),(11,9,1,NULL,'2025-07-22','2026-07-22',9,'2025-07-22 20:13:27',0,'client');
/*!40000 ALTER TABLE `USERS_ROLES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'coupon_system'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-23 13:00:14
