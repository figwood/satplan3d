# ************************************************************
# Sequel Ace SQL dump
# Version 20089
#
# https://sequel-ace.com/
# https://github.com/Sequel-Ace/Sequel-Ace
#
# Host: 127.0.0.1 (MySQL 5.5.5-10.5.28-MariaDB-ubu2004)
# Database: satplan3d
# Generation Time: 2025-04-11 02:54:32 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE='NO_AUTO_VALUE_ON_ZERO', SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table satellite
# ------------------------------------------------------------

DROP TABLE IF EXISTS `satellite`;

CREATE TABLE `satellite` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `noard_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `hex_color` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_noard_id` (`noard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

LOCK TABLES `satellite` WRITE;
/*!40000 ALTER TABLE `satellite` DISABLE KEYS */;

INSERT INTO `satellite` (`id`, `noard_id`, `name`, `hex_color`)
VALUES
	(1,'33321','HJ-1A','#FF0000'),
	(2,'33320','HJ-1B','#00FFFF');

/*!40000 ALTER TABLE `satellite` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table sensor
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sensor`;

CREATE TABLE `sensor` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `sat_noard_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `resolution` double DEFAULT NULL,
  `width` double DEFAULT NULL,
  `right_side_angle` double DEFAULT 0,
  `left_side_angle` double DEFAULT 0,
  `observe_angle` double DEFAULT NULL,
  `hex_color` varchar(255) DEFAULT NULL,
  `init_angle` double DEFAULT 0,
  `cur_side_angle` double DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_sensor_satellite` (`sat_noard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

LOCK TABLES `sensor` WRITE;
/*!40000 ALTER TABLE `sensor` DISABLE KEYS */;

INSERT INTO `sensor` (`id`, `sat_noard_id`, `name`, `resolution`, `width`, `right_side_angle`, `left_side_angle`, `observe_angle`, `hex_color`, `init_angle`, `cur_side_angle`)
VALUES
	(1,'33321','CCD1',30,360,0,0,30,'#9983E9',-14.5,0),
	(2,'33321','CCD2',30,360,0,0,30,'#FF8055',14.5,0),
	(3,'33321','HSI',100,50,30,30,4.5,'#CC6633',0,0),
	(4,'33320','CCD1',30,360,0,0,30,'#99E6FF',-14.5,0),
	(5,'33320','CCD2',30,360,0,0,30,'#8fbc8f',14.5,0),
	(6,'33320','IRS',300,720,0,0,60,'#b87333',0,0);

/*!40000 ALTER TABLE `sensor` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table sensor_path
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sensor_path`;

CREATE TABLE `sensor_path` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `noard_id` varchar(255) DEFAULT NULL,
  `sensor_id` int(11) unsigned DEFAULT NULL,
  `time` int(11) unsigned DEFAULT NULL,
  `lon1` double DEFAULT NULL,
  `lat1` double DEFAULT NULL,
  `lon2` double DEFAULT NULL,
  `lat2` double DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;



# Dump of table sys_user
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sys_user`;

CREATE TABLE `sys_user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_name` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

LOCK TABLES `sys_user` WRITE;
/*!40000 ALTER TABLE `sys_user` DISABLE KEYS */;

INSERT INTO `sys_user` (`id`, `user_name`, `password`, `is_admin`)
VALUES
	(1,'admin','$2b$12$jqWj3fEGNWeVl7u3FPtuQu2jvwx0dRZB8bdG8LLbNIlBWXK5OuP5C',1);

/*!40000 ALTER TABLE `sys_user` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table tle
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tle`;

CREATE TABLE `tle` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `noard_id` varchar(255) DEFAULT NULL,
  `time` int(11) unsigned DEFAULT NULL,
  `line1` text DEFAULT NULL,
  `line2` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

LOCK TABLES `tle` WRITE;
/*!40000 ALTER TABLE `tle` DISABLE KEYS */;

INSERT INTO `tle` (`id`, `noard_id`, `time`, `line1`, `line2`)
VALUES
	(1,'33321',1744180492,'1 33321U 08041B   25099.60755453  .00002475  00000+0  31423-3 0  9998','2 33321  97.6298 102.8588 0037711 163.3680 196.8781 14.82042366894167'),
	(2,'33320',1744179421,'1 33320U 08041A   25099.59515104  .00003763  00000+0  47400-3 0  9995','2 33320  97.6402  98.5985 0021121 119.2869 241.0459 14.82417352894135');

/*!40000 ALTER TABLE `tle` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table track
# ------------------------------------------------------------

DROP TABLE IF EXISTS `track`;

CREATE TABLE `track` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `noard_id` varchar(255) DEFAULT NULL,
  `time` int(11) unsigned DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `alt` double DEFAULT NULL,
  `vx` double DEFAULT NULL,
  `vy` double DEFAULT NULL,
  `vz` double DEFAULT NULL,
  `eci_x` double DEFAULT NULL,
  `eci_y` double DEFAULT NULL,
  `eci_z` double DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
