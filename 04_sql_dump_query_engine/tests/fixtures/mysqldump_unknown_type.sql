CREATE TABLE `devices` (
  `id` INT NOT NULL,
  `meta` GEOGRAPHY,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `devices` (`id`, `meta`) VALUES
(1, 'point-a'),
(2, 'point-b');
