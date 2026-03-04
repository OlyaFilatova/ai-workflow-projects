-- MySQL dump fixture
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;

CREATE TABLE `users` (
  `id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `users` WRITE;
INSERT INTO `users` (`id`, `name`, `active`) VALUES
(1, 'Alice', 1),
(2, 'Bob', 0),
(3, 'Eve; Mallory', 1);
UNLOCK TABLES;

CREATE VIEW `active_users` AS SELECT * FROM `users` WHERE `active` = 1;
