-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: attendance_db
-- ------------------------------------------------------
-- Server version	8.0.46

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
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `time` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_student_attendance_per_day` (`student_id`,`date`),
  KEY `ix_attendance_date` (`date`),
  KEY `ix_attendance_student_id` (`student_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
INSERT INTO `attendance` VALUES (1,2,'2026-04-28','20:25:02'),(2,50,'2026-04-28','20:25:10'),(3,51,'2026-04-28','20:25:28'),(4,54,'2026-04-28','20:33:04'),(5,10,'2026-04-28','20:39:25'),(6,20,'2026-04-28','20:43:10'),(7,12,'2026-04-28','20:46:49'),(8,29,'2026-04-28','20:47:09'),(9,23,'2026-04-28','20:51:10'),(10,26,'2026-04-28','20:51:45'),(11,40,'2026-04-28','20:54:47'),(12,41,'2026-04-28','20:56:31'),(13,43,'2026-04-28','20:56:40'),(14,3,'2026-04-28','20:57:07'),(15,38,'2026-04-28','21:01:03'),(16,39,'2026-04-28','21:05:29'),(17,50,'2026-10-29','19:41:56'),(18,49,'2026-10-29','19:42:08');
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
INSERT INTO `settings` VALUES (1,'realtime','true'),(2,'email','true'),(3,'qr','true');
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `uid` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_pic` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_students_uid` (`uid`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `ix_students_username` (`username`),
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES (1,2,'22a21a5402','22A21A5402','AKULA LEKHANA SAI','parent1@example.com','default_student.png'),(2,3,'22a21a5403','22A21A5403','ALLENA HARIBABU','parent2@example.com','default_student.png'),(3,4,'22a21a5404','22A21A5404','ALLU SATYANARAYANA MURTHY','parent3@example.com','default_student.png'),(4,5,'22a21a5405','22A21A5405','ASAPU HEMANTH','parent4@example.com','default_student.png'),(5,6,'22a21a5406','22A21A5406','BARRI BHAVANI','parent5@example.com','default_student.png'),(6,7,'22a21a5407','22A21A5407','BASWANI MOUNIKA','parent6@example.com','default_student.png'),(7,8,'22a21a5408','22A21A5408','JANAPAMULA THRUN SRI NAGA SUBASH','parent7@example.com','default_student.png'),(8,9,'22a21a5409','22A21A5409','BOLLOJU ANUPAMA','parent8@example.com','default_student.png'),(9,10,'22a21a5410','22A21A5410','CHALAMALASETTI KUNDHANA','knvv321@gmail.com','default_student.png'),(10,11,'22a21a5411','22A21A5411','KETHA J HARSHITH','parent10@example.com','default_student.png'),(11,12,'22a21a5412','22A21A5412','VEERAVASARAPU PUSPHA SAI','parent11@example.com','default_student.png'),(12,13,'22a21a5413','22A21A5413','CHELLUBOINA SOWMYA','parent12@example.com','default_student.png'),(13,14,'22a21a5414','22A21A5414','CHILUKURI SATVIKA','parent13@example.com','default_student.png'),(14,15,'22a21a5415','22A21A5415','CHINTA MUNEESWARI','parent14@example.com','default_student.png'),(15,16,'22a21a5416','22A21A5416','CHINTALAPUDI SRAVANTHI','parent15@example.com','default_student.png'),(16,17,'22a21a5417','22A21A5417','ELI ROHITH SRI GANESH','parent16@example.com','default_student.png'),(17,18,'22a21a5418','22A21A5418','GAJULA SAI KRISHNA','parent17@example.com','default_student.png'),(18,19,'22a21a5419','22A21A5419','GIRIGI SATYA SAI AJAY KUMAR','parent18@example.com','default_student.png'),(19,20,'22a21a5420','22A21A5420','GUBBALA PAVANI DURGA','parent19@example.com','default_student.png'),(20,21,'22a21a5421','22A21A5421','GUTHULA HEMA SRI DEVI','parent20@example.com','default_student.png'),(21,22,'22a21a5422','22A21A5422','JUTHUGA BLESSY','parent21@example.com','default_student.png'),(22,23,'22a21a5425','22A21A5425','KATTA LALITHA KUMARI','parent22@example.com','default_student.png'),(23,24,'22a21a5426','22A21A5426','KAVURU BHAVYA','parent23@example.com','default_student.png'),(24,25,'22a21a5427','22A21A5427','KOLLEPALLI VENKATA NAGA DURGA PRASAD','parent24@example.com','default_student.png'),(25,26,'22a21a5428','22A21A5428','KONA VEERA MANIKANTA','parent25@example.com','default_student.png'),(26,27,'22a21a5429','22A21A5429','KRUPAKAR INJETI','parent26@example.com','default_student.png'),(27,28,'22a21a5430','22A21A5430','KUCHCHERLAPATI PRABHU PRIYA','parent27@example.com','default_student.png'),(28,29,'22a21a5431','22A21A5431','MANIKALA VENU GOPALA SWAMY','parent28@example.com','default_student.png'),(29,30,'22a21a5432','22A21A5432','MAIJI PURNA CHANDRIKA','parent29@example.com','default_student.png'),(30,31,'22a21a5433','22A21A5433','MAMIDISETTI LOUKYA SATYA MANIKANTA','parent30@example.com','default_student.png'),(31,32,'22a21a5434','22A21A5434','PALA SAI SATISH KUMAR','parent31@example.com','default_student.png'),(32,33,'22a21a5435','22A21A5435','MANDELA YAMINI NAGA LAKSHMI DEVI','parent32@example.com','default_student.png'),(33,34,'22a21a5436','22A21A5436','MUDDALA DURGA NAGENDRA KUMAR','parent33@example.com','default_student.png'),(34,35,'22a21a5437','22A21A5437','NOOKALA BALA SUBRAHMANYA SATYA TEJASRI','parent34@example.com','default_student.png'),(35,36,'22a21a5438','22A21A5438','NUKAVARAPU SARIKA','parent35@example.com','default_student.png'),(36,37,'22a21a5439','22A21A5439','PECHETTI MOHITH RAM','parent36@example.com','default_student.png'),(37,38,'22a21a5440','22A21A5440','PILLA LOKESWARI','parent37@example.com','default_student.png'),(38,39,'22a21a5441','22A21A5441','PINABAKALA NAGESWARARAO','parent38@example.com','default_student.png'),(39,40,'22a21a5442','22A21A5442','PUTCHALA PHANI SRI KUMAR','parent39@example.com','default_student.png'),(40,41,'22a21a5444','22A21A5444','RAJA MOHAN KOUSHIK','parent40@example.com','default_student.png'),(41,42,'22a21a5445','22A21A5445','SAKHAMURI KAVYA','parent41@example.com','default_student.png'),(42,43,'22a21a5446','22A21A5446','SANKU PAVANI','parent42@example.com','default_student.png'),(43,44,'22a21a5447','22A21A5447','SHESHAPALLI NAGA JAHNAVI','parent43@example.com','default_student.png'),(44,45,'22a21a5448','22A21A5448','SIRIGINENI GAYATHRI','parent44@example.com','default_student.png'),(45,46,'22a21a5449','22A21A5449','SOLA GOPI CHANDU','parent45@example.com','default_student.png'),(46,47,'22a21a5450','22A21A5450','TIRUMANI TULASI','parent46@example.com','default_student.png'),(47,48,'22a21a5451','22A21A5451','YADLA GOPIVISHAL','parent47@example.com','default_student.png'),(48,49,'23a25a5401','23A25A5401','ENUGU BHANU','parent48@example.com','default_student.png'),(49,50,'23a25a5402','23A25A5402','KOYA SIVA SATYA DURGA SAI VINAY','sivasatyakoya18@gmail.com','default_student.png'),(50,51,'23a25a5403','23A25A5403','KUDIPUDI NAGA VEERA VENKATA SATYANARAYANA','parent50@example.com','default_student.png'),(51,52,'23a25a5406','23A25A5406','NARAM MANI KUMAR','parent51@example.com','default_student.png'),(52,53,'23a25a5407','23A25A5407','POSINASETTI NAGA VEERA VENKATA SWAMY','parent52@example.com','default_student.png'),(53,54,'23a25a5408','23A25A5408','SRINIVASULA RAMA MANOJNA','parent53@example.com','default_student.png'),(54,55,'23a25a5409','23A25A5409','VATTIKUTI MOUNIKA','parent54@example.com','default_student.png');
/*!40000 ALTER TABLE `students` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `support_tickets`
--

DROP TABLE IF EXISTS `support_tickets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `support_tickets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `subject` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `admin_reply` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `support_tickets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `support_tickets`
--

LOCK TABLES `support_tickets` WRITE;
/*!40000 ALTER TABLE `support_tickets` DISABLE KEYS */;
/*!40000 ALTER TABLE `support_tickets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teacher_attendance`
--

DROP TABLE IF EXISTS `teacher_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teacher_attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int NOT NULL,
  `date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `time` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_teacher_attendance_per_day` (`teacher_id`,`date`),
  KEY `ix_teacher_attendance_date` (`date`),
  KEY `ix_teacher_attendance_teacher_id` (`teacher_id`),
  CONSTRAINT `teacher_attendance_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teacher_attendance`
--

LOCK TABLES `teacher_attendance` WRITE;
/*!40000 ALTER TABLE `teacher_attendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `teacher_attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teachers`
--

DROP TABLE IF EXISTS `teachers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teachers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_pic` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `ix_teachers_username` (`username`),
  CONSTRAINT `teachers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teachers`
--

LOCK TABLES `teachers` WRITE;
/*!40000 ALTER TABLE `teachers` DISABLE KEYS */;
INSERT INTO `teachers` VALUES (1,56,'Rao','Durga Rao','AIDS','Durga_Rao@gmail.com','default_teacher.png');
/*!40000 ALTER TABLE `teachers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$K0gl8Y5FFrcz4JV9$fa438fd8e113e4aeaa459aa5efb3be553205ba3842e6d088981f28c810fff02ef8b83b3d9677f25045eb179d30d0ae2696fc305016218995b18d66b5cb19ebe6','admin','2026-04-26 00:40:00'),(2,'22a21a5402','scrypt:32768:8:1$2nMk5oDSpjP5LhxP$e3c3d27dfdece5c91e60208af0c475680af617a4cb74ebc18867c8d2069ad81c7d30dfbf36848f072f1a405cbb09c30ec489e102f7dd4641c3ae8ac860cdb8d9','student','2026-04-26 23:18:28'),(3,'22a21a5403','scrypt:32768:8:1$DVVxLMbl3Ey8GJ0c$cd5898bc38faa3e2066853a65379c1925be71dc8b603c50920c26863738c6a506f31e66f2154f3a44b4b2cedaba4789a9201563f738663cfa1ac40366410a0c2','student','2026-04-26 23:18:28'),(4,'22a21a5404','scrypt:32768:8:1$v32jHVPekiHZTT6O$e033b63cb278b02aa33773f64610afcb95c45eba0a8af2ef5cef8724b04ec0728fd50b6abd609a1c0237232dcac1b7c0c89aa9ac4dbf95a7ec2407a41cef9d2c','student','2026-04-26 23:18:28'),(5,'22a21a5405','scrypt:32768:8:1$jkftPadIEoENfGKZ$ef907dc0035a662d35e868b7da7c920658e70ba99d58a04afbbf2251bc20a1ed195d0e2713307018b0ba1d80eeaf76d4e70f7ab1f470dc27c4c829e6ede4a505','student','2026-04-26 23:18:29'),(6,'22a21a5406','scrypt:32768:8:1$hELImljdULmKWZ6T$7a6e3bfac0890d3064c23a7927d183e40bbdfeb0dd7dcbefe5f989f77d4ce7c76e701abe52d7f1c0ac8fd62321f0c546f686f01305db3edd8ad46f10eaf9e038','student','2026-04-26 23:18:29'),(7,'22a21a5407','scrypt:32768:8:1$BD0EuVliVJafE1KV$d0d699af2070bcf7b69fe89533d32cb82e847dff6a833a2f77538ff50d9f93433eca5b3c7027a9d5a21efa1e0476fca69207e6555583555f0aa0c398dd20e2c5','student','2026-04-26 23:18:29'),(8,'22a21a5408','scrypt:32768:8:1$96q4SC42zCr5R9ei$863cfdbdc2dcb4ae7e445dd48ca8a45dc0801d6b0e75c1eb45a26c36a6e7a5a5214e6da3ef4d601a3b14ca87820ce33d9920ac066cf5d7964d8f953047d21de4','student','2026-04-26 23:18:29'),(9,'22a21a5409','scrypt:32768:8:1$c4r4XSWm4ISPhpQS$961c48386619c6c1a0f24241549b6a3bb331f1c970f0e2b75f6aeda58f2bc03e51b9cfb6fb6c6bbac73d1a3a43996d8cf41b8227648adadc9e0f6d958ce820b1','student','2026-04-26 23:18:29'),(10,'22a21a5410','scrypt:32768:8:1$UIiTYBTVrhoF144B$46f8e4350f6495dfc6503a26cc545dcd4a7c1fae0f7956943fdb656eefb5726589d4cef5a851ea859d5dee02377a9257cab20d6efa6c8f9de5fa291713594467','student','2026-04-26 23:18:29'),(11,'22a21a5411','scrypt:32768:8:1$tUmqSO1lvHGbxZwy$773645c7ff47b0a2fe2ea8d647c4ffd38b909c52ad49835ef4acd53af042fe146dbcd1ab2b1ba00b57a16e013d43815bb5accf188c8fdb438e97d750fc45d635','student','2026-04-26 23:18:30'),(12,'22a21a5412','scrypt:32768:8:1$lQhRrEF6m2Ke4Bn5$2e73b1d2b99a9629ab608922bbc98283e233723954886542c4e827ad3d8e563b38f79620cd31bb760acae6d33e5ac1a70714ac37ea3eafef5c15791ba1a572ca','student','2026-04-26 23:18:30'),(13,'22a21a5413','scrypt:32768:8:1$edPnGRllAMrc9pYM$6a36bf37010fd59ef3e8f819eae0814b5be57ce4f2441323b78b2d307c24184b587e9f87baed00ccae8174d885e4f4fc3a3c52729fbd6db440e759f2b54065bf','student','2026-04-26 23:18:30'),(14,'22a21a5414','scrypt:32768:8:1$La3155LZwCCHVqQJ$d7176d0937c583b9367b5c9b844094faf6b562e51c46597b903d20826ff5f34d795b4d90775b7b7b21fa87fa2b43ac04c7402bc37897532a8ea7c986441fe9ce','student','2026-04-26 23:18:30'),(15,'22a21a5415','scrypt:32768:8:1$DXcMgajWsJAfOWU8$1226951e687506a3928f129027e70972570abe9bf2075554892a994a8f525baaba4cd96c7ccd9b3d6beb8767f7009eb55b376524694dca043581bc43ea21a9bf','student','2026-04-26 23:18:30'),(16,'22a21a5416','scrypt:32768:8:1$5zp3dJdAdXCJHxBQ$904c05419c02b1eb5e0e30e4aa63ec350e042c27ceb155da12360ea4166cb5c2c248cabaff6795362ee751e8fbaf6a20201073efc4fe51dbd9739e0964f9f67c','student','2026-04-26 23:18:31'),(17,'22a21a5417','scrypt:32768:8:1$MRGZLYWXtCKg09p3$8a6f81ffd965e296e3a99c27c5f5391682f301e08781a201b284fbc5693c398b7314870362c988531ee53ec286036c5a9c3e2f41c41e2562ec254233dc56d7f8','student','2026-04-26 23:18:31'),(18,'22a21a5418','scrypt:32768:8:1$O45MnOSwV3IxVNDB$b4447570501997119e997155f6c20027ddbcea652aa05e1471f2ca9a1025a1d5eb950c25f786cfb0a99b38d1da728f98d00709336293924b54fe27422f6ffc79','student','2026-04-26 23:18:31'),(19,'22a21a5419','scrypt:32768:8:1$McDTwcjx5E3Psp0X$aab9191dcab083a7a3a262136d65cbe8f4b6aad964d3bea7de4b060fb55574911fdffb563f4153b842b81a8ed3711eb1ac21f320ac0f4da64dbfab0f4d9d9967','student','2026-04-26 23:18:31'),(20,'22a21a5420','scrypt:32768:8:1$4JEQUEjmYSMdcNrb$4852bdd9cb0f5f3b3f7e121133c3ffa9a155cfc2b825c608f878629f45b8f39c287223bb803a7651cf6c436b485ad984252956865615f683df93266aba522ede','student','2026-04-26 23:18:31'),(21,'22a21a5421','scrypt:32768:8:1$54W32IYWHgLS3T1v$3abfb20e415dd1a198d658b5efa94962942964f377fcfff539f37723ab5e880f5ee967ee2de4e30678431289a158b0a1b46f8694c3582f15760a19a89af5138f','student','2026-04-26 23:18:32'),(22,'22a21a5422','scrypt:32768:8:1$J3QacbADogq3QAjb$cb65dcc1accf44005b00b33873b27894ed74d78aed6dbddd2ceab5b8db98fc8507907dd3273f88dbfccae1169438241bee64b161c0adbcd6189daa29035471a3','student','2026-04-26 23:18:32'),(23,'22a21a5425','scrypt:32768:8:1$6tdzhtsK2o9rjYiL$ae8bdb2a8f3b42c630f7362729e4c6bef195bed38dd59bc75c78f65cf92aae1ae1e06613ae486653381a9923a05d7f5f289ff91d1c08410bc1f939a15f5ff4c1','student','2026-04-26 23:18:32'),(24,'22a21a5426','scrypt:32768:8:1$DqekACK5QyKWQym7$88e10faad9a661f71054444800ef1a38d875f273d22fcb4b0e25c39d8f1f7dd49183c00c3431db7d692ab49f1861fcfe0c346a5794d3bfd9d25f2f9e27f4b6bf','student','2026-04-26 23:18:32'),(25,'22a21a5427','scrypt:32768:8:1$e98ZDcIMUjyv6LKA$98d056f668940a5dffa527fd7b99ffdbd04f8432984670f52b5fdc1b72e0d5bf186489cf41fc0dcb3d089cb23bd04d1c2de06f6e232b81061cbcfa04358061fd','student','2026-04-26 23:18:33'),(26,'22a21a5428','scrypt:32768:8:1$SFDeii9rNduZF32P$80b8f22831898454f9787c586acb0c4535a67003db02cf2a0b1cafceef89ab6ccaf22905abb9a9668825d40f6be3b7cc9eec9f40a08bfc5d65f3e2a8bfee58ab','student','2026-04-26 23:18:33'),(27,'22a21a5429','scrypt:32768:8:1$XmmK4eFwzMbwwF03$acc8e9c7bdab5f9fc0d016d00e52240434cfc16fb4a61a080804033decde34861339f842127829d3165bcbaad2aaaaefc38c88396a6352160cc082a739afb79a','student','2026-04-26 23:18:33'),(28,'22a21a5430','scrypt:32768:8:1$QgFbZ3zToWUoDzjX$a29ff83d733e290a84bdde2e4d16399bde95494f583e5fbcc3a8af45b74e5fcf2b8363eb77c31ee6d9d74211ea3ad3df68be844aa54e24d663e8f0be645b634a','student','2026-04-26 23:18:33'),(29,'22a21a5431','scrypt:32768:8:1$MKVyf4XKcaSIRqsy$235d3ff9ef04a822d8358ddef80ce7ad068d175c467c7a7580b00c5469c9732fd8e5152826aa470930b6725a8f8b0e4ce3893e53323ac5624b90f29be79e9292','student','2026-04-26 23:18:33'),(30,'22a21a5432','scrypt:32768:8:1$ED6mBYVXLLGvVxGn$54d1e1e7233c95ecc27a1ce7f2e06f2134cb6435e0041c9869cec81fbe431a456ff11efc7989375f21528adeb9ed72af23f853c45263c103545f3f0ac91410f7','student','2026-04-26 23:18:33'),(31,'22a21a5433','scrypt:32768:8:1$YbVPrWQMQ2b44JiC$db0b55b8fc642c37f7afad85a7500d2559e2dac7eaa1342bc07f154c829043907e0280e8ade09a97c03d3ff9143521c3b61199932be87771b67e64104d7b0570','student','2026-04-26 23:18:34'),(32,'22a21a5434','scrypt:32768:8:1$yyA3u97yvU5g6yJN$7137f2e5be97492c21a3a7608d8a0872c64d60435ca3aa3454525b5c1876bdb63a4267dc6ea7940bd26d840b9395153f68c485c53b00744684a41809bb31a71c','student','2026-04-26 23:18:34'),(33,'22a21a5435','scrypt:32768:8:1$fI9XGuTGMHq9o9mb$8b0dd73c20b628080f9715c1ba1127cbd98a376facdd9a87621fb645b7955ef3c1cbd835e4b4cef98b1e4b53e21241f507eb3019fabbc1b867ec26d66b685928','student','2026-04-26 23:18:34'),(34,'22a21a5436','scrypt:32768:8:1$pQnYuZWSpBJQhvqk$8984dc87e1f2cc340f226e5819034ae0a23c981b58f0771dde79fe885aac0ee16cdbee30e05f5e412e0874d6fcf6e4858b2d2fe6b4db290d287e73d389f5ae5d','student','2026-04-26 23:18:34'),(35,'22a21a5437','scrypt:32768:8:1$FlargUDADNZgQttd$d61c99ed4857838ee1191f7f4be4561d8393c597e97b7a535d136e10d63e70647a6d498b4e91eacd480461c499332a2aed96aeb833d567a8e9d69cdb1670e063','student','2026-04-26 23:18:35'),(36,'22a21a5438','scrypt:32768:8:1$axhmykNIVFnCfUoL$0652bea04123750a330ad967e04aa0cfd4c6ecb71a9ea73a77860dce6d657277f8b573e0b7b7ce993d5c9e86a6591aae1eba31d1849ed42e00fccc4237562c79','student','2026-04-26 23:18:35'),(37,'22a21a5439','scrypt:32768:8:1$1QtaRwhBfsA80NmN$454849f2f7e4872e2eb6396216bc5e7593edab1ed9828c5a36f96cd782b17d33a74babd570c62937a5efae4c293ebefb9eece4291a402f3149bb5145e89fa145','student','2026-04-26 23:18:35'),(38,'22a21a5440','scrypt:32768:8:1$zL14Hs8r1WtPAsN9$b227ac51fe0c97b7a49e7042e89ffeaf24911b4c1c273cf33a951861f58c751b97cf18a446963ac00bab23ea9215e469aba9a76c37d146a0a5e1e2487791c62c','student','2026-04-26 23:18:35'),(39,'22a21a5441','scrypt:32768:8:1$qvqVtrIM9JjkBVtM$04a3933a63a21354574ae32e9b950a633d29378c2937cd983acdbc452062375742fa8755c8230204a8363da858a482d21cde0c9a52849f5cac8f2d9bc6206f37','student','2026-04-26 23:18:35'),(40,'22a21a5442','scrypt:32768:8:1$aN2gXqoq30kNxTgT$bb576d57f02d72260a86ef485ad2058dc68d214f21ff3b05be961ece6c0e1e3efecce0ba7188d0c22fe53b87172f64d862251d7be5db6d2ff3564778271a48e1','student','2026-04-26 23:18:36'),(41,'22a21a5444','scrypt:32768:8:1$3F3tvcwJITmpL0cC$a0a8342449eed19fcbb4f1a344540e16fa869d816c6696e60bc509aa83a831608cc6fadb7b226989f9d2a155b80a7f45504654402548d7710f3b672da9d3a80e','student','2026-04-26 23:18:36'),(42,'22a21a5445','scrypt:32768:8:1$WFt8rg1DZNocNiHj$ba6ad35b2df76f267d327390cd31f74822dac3adc2c9d7c7af4633fdf099484868f657c8e1c090e55d65eee82e891070c18ce0c28d48c114adefe078d79aa1d7','student','2026-04-26 23:18:36'),(43,'22a21a5446','scrypt:32768:8:1$dr11N97ezNizxbyQ$e4516d8f1595d43e6f72846205dc8578fa6fa31eae6f486681a1348344d2a67ecfaee60d15a2011ca49cdc6812a0c556091f9d56a325d31df6e70153d31f88b0','student','2026-04-26 23:18:36'),(44,'22a21a5447','scrypt:32768:8:1$PGNUtlH4HLTe8Al3$f819115079f6443461fd687259d6cedc24529ede8c498f1fb17d9852c2f9d0d04932e8be78479f04f128a38441028aed0802fd80e1282dcfdcf395d5a2ad1c55','student','2026-04-26 23:18:36'),(45,'22a21a5448','scrypt:32768:8:1$VTAxPXjQHrS4M60R$5878188e272f8f919f25c95cfd0f96544be7ab949cbfc129553fbb48e2967815b0281a0785e03cd914fea8f407abf5a2cd9d07181be9a2ba169e71a6c9d4585c','student','2026-04-26 23:18:37'),(46,'22a21a5449','scrypt:32768:8:1$X9uJn6pnaa3eMF5r$58683a24c5cb50d8c0979935cfe12dbebf398b50cf4a31077061d21e0ff07dac7fcac1ca774039ce8c4af6b9c765d80e5a1df48bad6f688f6c7cbfc1af9bd298','student','2026-04-26 23:18:37'),(47,'22a21a5450','scrypt:32768:8:1$IELXjaTjDw64Wj3w$8a15227ef729ed1f3d415f91f5ed6762d8085742b85353b5e02c9fc9d6a713f11ef294b9350228a5faa45ae92767fa1bc76bd09d52e6a04bd233833bcc0e14c4','student','2026-04-26 23:18:37'),(48,'22a21a5451','scrypt:32768:8:1$s71MEwdwXwEIS7eB$996fccba9dfbf8d9e8c512884af3b0150ba5a601cc9d56495052b1cc9925388bcafdca0d18333345cf6a44d79cff15c90923b444ccd664961cbfcc48b7b97f2d','student','2026-04-26 23:18:37'),(49,'23a25a5401','scrypt:32768:8:1$b5wPSxYlN4KL5dNg$0c606b140fba51fbe2401ffa635ed8639d4d0a1d1d95e3e2408cc51e76e2e6b0f5f49d28514acffaa024e1b4717e83000efc6ec0c02e83f8577baeb7a6a8d770','student','2026-04-26 23:18:37'),(50,'23a25a5402','scrypt:32768:8:1$AH2zsC4dC4W5gkiP$75b8a887d4ce3f22b3852a2cf60f82e22c6036879361b0984f9fa8148cc2ad1676d6089d4b4b3bdf0647a4aaf5d43b57f6ec073d89574f9b6b941db9ed6862d2','student','2026-04-26 23:18:37'),(51,'23a25a5403','scrypt:32768:8:1$jxw0Cwf60Y6ClsY4$c008e3df4fb500c3050d9fe9c84e836a97448b6a922450727f3fb93126bb7286bcd6147ad436bf73c385bef1153633c16eaa0baba63c72107cbeb9beeeb22dc9','student','2026-04-26 23:18:38'),(52,'23a25a5406','scrypt:32768:8:1$9d0XqPLpLCBdlpw2$a7e06ee92f4828111c7cbc7b6d56f4c97758b9399b99aa3e31fb3b5f2f9899f059a0523cc4350589a8fa1cfb3a87e9bad4f8cdb420e8426a1834970430244a51','student','2026-04-26 23:18:38'),(53,'23a25a5407','scrypt:32768:8:1$fsSSoR3LpqlBDeMQ$749894f1ea9314df76a042c26df0e5553eac56e22c35f0af778cb439053cacaf090ae4241d2398c2e2b7cb80f441d671f2bacba7d3f98f3650b3a7a6a52321e2','student','2026-04-26 23:18:38'),(54,'23a25a5408','scrypt:32768:8:1$lUC9FaqdaiQZ7ULq$b0652f5b7c48dcd839fbe416bbdce87d0048348a505fb0cbab377f9b2efb849becfad1d1ff7eb323bceb4e3a7ee5576b056a31ac95f9b82f194c112e6dadb6f7','student','2026-04-26 23:18:38'),(55,'23a25a5409','scrypt:32768:8:1$R35ZLYTgmPQCGwGr$f693d4706edce84e0fd89dc1fd7585e80d5aad3e877153a6b8ab5d90f1e2570c46d6d1b89b311c13f78bc01ac4497946461374838b3858b554557d1737875ccb','student','2026-04-26 23:18:38'),(56,'Rao','scrypt:32768:8:1$OhqOferoGUHxp7Zd$ec486b06bb04f278c88ab30c0bcffe20a0c6ae39a6c9f6507378b77668d3610d9ad4118510b736befb2a7c47b7108aa9dfdb6cf52cb18ece8b867e67a45a00e3','teacher','2026-04-28 21:07:09');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-29 20:27:05
