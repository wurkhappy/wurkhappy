CREATE TABLE `forgot_password` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `code` varchar(255) NOT NULL,
  `validUntil` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `active` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;