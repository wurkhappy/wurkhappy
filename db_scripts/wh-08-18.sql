-- MySQL dump 10.13  Distrib 5.5.10, for osx10.6 (i386)
--
-- Host: localhost    Database: wurkhappy
-- ------------------------------------------------------
-- Server version	5.5.10

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agreement`
--

DROP TABLE IF EXISTS `agreement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreement` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `vendorID` bigint(20) unsigned NOT NULL,
  `clientID` bigint(20) unsigned NOT NULL,
  `name` varchar(150) DEFAULT NULL,
  `amount` int(10) unsigned DEFAULT NULL,
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dateSent` datetime DEFAULT NULL,
  `dateAccepted` datetime DEFAULT NULL,
  `dateModified` datetime DEFAULT NULL,
  `dateDeclined` datetime DEFAULT NULL,
  `dateVerified` datetime DEFAULT NULL,
  `dateContested` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreement`
--

LOCK TABLES `agreement` WRITE;
/*!40000 ALTER TABLE `agreement` DISABLE KEYS */;
INSERT INTO `agreement` VALUES (1,4,2,'Funky Bananapants',5700,'2011-06-29 16:29:54',NULL,'2011-06-28 12:00:00','2011-07-18 19:15:26','2011-06-29 10:00:00',NULL,NULL),(2,2,4,'Analysis of Main Site',340000,'2011-06-29 22:39:58',NULL,NULL,NULL,NULL,NULL,NULL),(3,4,7,'Marketing Prospectus',120057,'2011-06-30 00:02:30',NULL,'2011-08-15 12:34:33','2011-07-06 17:51:01',NULL,NULL,NULL),(4,4,5,'Waffle Dingus',4200000,'2011-06-30 00:02:30','2011-08-18 14:54:51',NULL,'2011-07-06 14:40:54',NULL,NULL,NULL),(5,4,2,'Humback Quackdinger',1000000,'2011-07-06 21:45:25','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(6,4,2,'New Agreement',1200000,'2011-07-06 21:51:49','2011-08-18 14:54:51','2011-08-15 12:35:16',NULL,NULL,'2011-08-15 12:35:16',NULL),(7,4,2,'Garden Work',2000,'2011-07-07 15:03:21','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(8,4,2,'Waistcoat Swimback',0,'2011-07-19 17:58:17','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(10,4,2,'Gemology Ruddersqueak',0,'2011-07-19 18:09:12','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(11,4,2,'Greenback Citydesk',0,'2011-07-19 18:09:42','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(12,4,2,'Stovepipe Hubcap',NULL,'2011-08-10 20:38:33','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(13,4,2,'Daredevil Alchemy',NULL,'2011-08-12 00:30:59','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(14,4,2,'Snailpace Flipjack',NULL,'2011-08-12 00:31:23','2011-08-18 14:54:51',NULL,NULL,'2011-08-12 14:01:11',NULL,NULL),(15,4,2,'Nickeldime Subwoofer',NULL,'2011-08-12 00:31:52','2011-08-18 14:54:51',NULL,'2011-08-12 14:03:08','2011-08-12 14:03:08',NULL,NULL),(16,4,2,'Fistknife Armandhammer',NULL,'2011-08-12 00:39:57','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(17,4,2,'Starstripe Rebelsnap',NULL,'2011-08-12 00:42:07','2011-08-18 14:54:51','2011-08-12 14:04:06',NULL,NULL,NULL,NULL),(18,4,2,'Kneejerk Jumpingcow',NULL,'2011-08-12 00:49:30','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL),(19,4,2,'Bazooka Artichoke',NULL,'2011-08-15 20:30:43','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `agreement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agreementPhase`
--

DROP TABLE IF EXISTS `agreementPhase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreementPhase` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `agreementID` bigint(20) unsigned NOT NULL,
  `phaseNumber` tinyint(3) unsigned DEFAULT NULL,
  `amount` int(10) unsigned DEFAULT NULL,
  `estDateCompleted` datetime DEFAULT NULL,
  `dateCompleted` datetime DEFAULT NULL,
  `description` text,
  `comments` text,
  PRIMARY KEY (`id`),
  KEY `agreementID` (`agreementID`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementPhase`
--

LOCK TABLES `agreementPhase` WRITE;
/*!40000 ALTER TABLE `agreementPhase` DISABLE KEYS */;
INSERT INTO `agreementPhase` VALUES (1,15,0,1,NULL,NULL,'A',NULL),(2,15,1,2,NULL,NULL,'B',NULL),(3,15,2,3,'2011-08-15 16:19:52',NULL,'C',NULL),(4,15,3,4,NULL,NULL,'D',NULL),(5,16,0,1000,NULL,NULL,'Aardvark artichoke',NULL),(6,16,1,2000,'2011-08-15 16:19:52','2011-08-15 16:20:14','Badger bok-choy',NULL),(7,16,2,3000,NULL,NULL,'Cicada cauliflower',NULL),(8,16,3,4000,NULL,NULL,'Dachshund dandelion',NULL),(9,17,0,1000,'2011-08-15 16:19:52',NULL,'Aardvark artichoke',NULL),(10,17,1,2000,NULL,NULL,'Badger bok-choy',NULL),(11,17,2,3000,NULL,NULL,'Cicada cauliflower',NULL),(12,17,3,4000,'2011-08-15 16:19:52','2011-08-15 16:20:14','Dachshund dandelion',NULL),(13,18,0,2000,NULL,NULL,'Initial project requirements, wireframe proposals, derpity derp.',NULL),(14,18,1,2000,'2011-08-15 16:20:39','2011-08-15 16:20:45','Revise and complete wireframes for client approval. Begin functional spec.',NULL),(15,18,2,2000,'2011-08-15 16:19:52',NULL,'Client review of functional spec and final wireframes. Begin rough coding and user testing.',NULL),(16,18,3,1500,'2011-08-15 16:20:33',NULL,'User testing complete; Add design and polish. Fit and finish for final review.',NULL),(17,19,0,40000,NULL,NULL,'Testing one, two, three.',NULL),(18,19,1,50000,NULL,NULL,'Mic check, ahhh- ahh- ahhh- mic check.',NULL),(19,19,2,100000,NULL,NULL,'Another test',NULL);
/*!40000 ALTER TABLE `agreementPhase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agreementTxn`
--

DROP TABLE IF EXISTS `agreementTxn`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreementTxn` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `agreementID` bigint(20) unsigned NOT NULL,
  `userID` bigint(20) unsigned NOT NULL,
  `status` tinyint(4) DEFAULT NULL,
  `dateModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementTxn`
--

LOCK TABLES `agreementTxn` WRITE;
/*!40000 ALTER TABLE `agreementTxn` DISABLE KEYS */;
INSERT INTO `agreementTxn` VALUES (1,1,4,1,'2011-06-29 16:39:45'),(2,1,2,4,'2011-06-29 23:38:19'),(3,1,4,2,'2011-06-30 19:32:58'),(4,1,2,3,'2011-06-30 19:32:58');
/*!40000 ALTER TABLE `agreementTxn` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agreementTxt`
--

DROP TABLE IF EXISTS `agreementTxt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreementTxt` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `agreementID` bigint(20) unsigned NOT NULL,
  `agreement` text,
  `refund` text,
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agreementID` (`agreementID`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementTxt`
--

LOCK TABLES `agreementTxt` WRITE;
/*!40000 ALTER TABLE `agreementTxt` DISABLE KEYS */;
INSERT INTO `agreementTxt` VALUES (1,1,'Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.','The quick brown foo jumps over the lazy frob.','2011-06-29 16:40:31'),(2,2,'Integer pellentesque sapien. Maecenas urna tortor, ornare id, fringilla porttitor, vestibulum eget, est. Donec in purus sed elit mollis adipiscing. Phasellus mi purus, convallis a, congue sit amet, ultricies nec, ante. Suspendisse potenti. Donec laoreet dui quis arcu. Vestibulum aliquam.','Nunc pretium quam eu ligula pellentesque gravida. Phasellus sem sem, ultricies ac dapibus vel, semper sed metus. Vivamus et cursus odio. Cras vehicula dui eu sapien volutpat sed viverra nisl dictum.','2011-06-29 22:41:19'),(3,4,'Bacon ipsum dolor sit amet ut spare ribs tail boudin sed beef, sausage sirloin pastrami commodo. Reprehenderit bresaola in, labore drumstick esse eu beef bacon ribeye brisket velit. Aliqua veniam eu bresaola cillum occaecat. Magna ut short loin cow t-bone. Proident ad t-bone brisket bresaola ea. Incididunt tri-tip t-bone, qui sirloin mollit in ribeye commodo pork sausage bresaola. Officia enim cillum, nisi sunt shoulder magna in.','Duis sirloin pancetta, ham pork consequat et fatback eu. Pork chop bacon anim enim. Fugiat eiusmod do, labore pork bresaola cow incididunt nostrud ham hock hamburger corned beef commodo cillum consectetur.','2011-07-06 18:30:40'),(4,3,'Sausage ham reprehenderit, tempor pastrami in meatloaf beef ut tenderloin sirloin culpa tri-tip. Ground round chuck do pork chop, pork loin flank venison duis qui tri-tip andouille non reprehenderit aliquip. Laboris jowl in, pork hamburger bresaola occaecat sed rump. Eiusmod t-bone corned beef, tongue labore swine meatball ullamco culpa reprehenderit short loin dolore. Commodo ut short ribs, reprehenderit officia brisket elit veniam jowl cow anim laborum turkey. Pork sausage pork belly sirloin brisket chicken jerky, pariatur excepteur voluptate. Deserunt swine meatball strip steak, id chicken nulla flank ut jerky in ribeye ham hock boudin.','Mollit adipisicing officia tail turkey laborum sirloin, swine non aute short ribs dolor dolore bresaola excepteur. Jerky aliquip dolor pariatur enim jowl fatback.','2011-07-06 18:32:26'),(5,5,'Flapjack','Canada','2011-07-06 21:45:26'),(6,6,'I will make a web site. You will pay me $12,000','None','2011-07-06 21:51:49'),(7,7,'I\'ll mow your lawn once a week, and water monthly.','Grass dies','2011-07-07 15:03:21'),(8,8,'The quick brown foo jumps over the lazy quux',NULL,'2011-07-19 17:58:17'),(9,10,'The quick brown foo jumps over the lazy quux',NULL,'2011-07-19 18:09:12'),(10,11,'The quick brown foo jumps over the lazy quux',NULL,'2011-07-19 18:09:42');
/*!40000 ALTER TABLE `agreementTxt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agreementcomment`
--

DROP TABLE IF EXISTS `agreementcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreementcomment` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `agreementID` bigint(20) unsigned NOT NULL,
  `agreement` text,
  `refund` text,
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agreementID` (`agreementID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementcomment`
--

LOCK TABLES `agreementcomment` WRITE;
/*!40000 ALTER TABLE `agreementcomment` DISABLE KEYS */;
INSERT INTO `agreementcomment` VALUES (1,1,'Maecenas urna tortor, ornare id, fringilla porttitor, vestibulum eget, est. Donec in purus sed elit mollis adipiscing. Phasellus mi purus, convallis a, congue sit amet, ultricies nec, ante. Suspendisse potenti.','Fringilla porttitor, vestibulum eget, est. Donec in purus sed elit mollis adipiscing. Phasellus mi purus, convallis a, congue sit amet, ultricies nec, ante. Suspendisse potenti. Donec laoreet dui quis arcu.','2011-06-30 19:30:43');
/*!40000 ALTER TABLE `agreementcomment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forgot_password`
--

DROP TABLE IF EXISTS `forgot_password`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forgot_password` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `code` varchar(255) NOT NULL,
  `validUntil` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forgot_password`
--

LOCK TABLES `forgot_password` WRITE;
/*!40000 ALTER TABLE `forgot_password` DISABLE KEYS */;
/*!40000 ALTER TABLE `forgot_password` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice`
--

DROP TABLE IF EXISTS `invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `invoice` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `clientID` bigint(20) unsigned DEFAULT NULL,
  `projectID` bigint(20) unsigned NOT NULL,
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `datePaid` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `dateSent` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`id`),
  KEY `userID` (`userID`),
  KEY `clientID` (`clientID`),
  KEY `projectID` (`projectID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice`
--

LOCK TABLES `invoice` WRITE;
/*!40000 ALTER TABLE `invoice` DISABLE KEYS */;
/*!40000 ALTER TABLE `invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lineItem`
--

DROP TABLE IF EXISTS `lineItem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lineItem` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `invoiceID` bigint(20) unsigned NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `description` varchar(200) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `invoiceID` (`invoiceID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lineItem`
--

LOCK TABLES `lineItem` WRITE;
/*!40000 ALTER TABLE `lineItem` DISABLE KEYS */;
/*!40000 ALTER TABLE `lineItem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `profile`
--

DROP TABLE IF EXISTS `profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `profile` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `bio` varchar(141) DEFAULT NULL,
  `blogURL` varchar(200) DEFAULT NULL,
  `portfolioURL` varchar(200) DEFAULT NULL,
  `bioURL` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `urlStub` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userID` (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `profile`
--

LOCK TABLES `profile` WRITE;
/*!40000 ALTER TABLE `profile` DISABLE KEYS */;
INSERT INTO `profile` VALUES (1,3,'I\'m a coder. I write code. \'\" SELECT * FROM user;',NULL,NULL,NULL,NULL,NULL),(2,4,'I\'m a coder. I write code.',NULL,NULL,NULL,'brendn','brendn'),(3,13,'I don\'t exist',NULL,NULL,NULL,'Test','test');
/*!40000 ALTER TABLE `profile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `clientID` bigint(20) unsigned DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `userID` (`userID`),
  KEY `clientUserID` (`clientID`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
INSERT INTO `project` VALUES (1,4,1,'Null Project'),(10,4,1,'Foo Project'),(11,4,2,'Awesome Sauce'),(12,4,2,'Project'),(13,4,2,'Gloop');
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `confirmationCode` varchar(10) DEFAULT NULL,
  `confirmationHash` varchar(30) DEFAULT NULL,
  `confirmed` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `firstName` varchar(60) DEFAULT NULL,
  `lastName` varchar(60) DEFAULT NULL,
  `password` varchar(60) DEFAULT NULL,
  `accessToken` varchar(90) DEFAULT NULL,
  `accessTokenSecret` varchar(90) DEFAULT NULL,
  `accessTokenExpiration` datetime DEFAULT NULL,
  `profileOrigURL` varchar(100) DEFAULT NULL,
  `profileSmallURL` varchar(100) DEFAULT NULL,
  `profileLargeURL` varchar(100) DEFAULT NULL,
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'brendan@plusminusfive.com',NULL,NULL,0,'Brendan','Berg',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2011-02-17 03:14:50'),(2,'marcus.ellison@gmail.com',NULL,NULL,0,'Marcus','Ellison','JDJhJDEyJFRmN1g2dVJhY1ZOdHM2YnJzZng4QS4=,JDJhJDEyJFRmN1g2dVJ',NULL,NULL,NULL,NULL,NULL,NULL,'2011-02-17 03:14:50'),(4,'berg@superstable.net','XOEDBJ','pPb_t1beRxahjmQOWJyfop7voCg=',0,'Brendan','Berg','JDJhJDEyJFRmN1g2dVJhY1ZOdHM2YnJzZng4QS4=,JDJhJDEyJFRmN1g2dVJ',NULL,NULL,NULL,NULL,NULL,NULL,'2011-04-07 04:03:21'),(5,'foo@boo.goo','YWLATQ','eQbSODnODK8a2sQ_bzLSwN80YZM=',0,'John','Appleseed',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2011-06-20 22:51:44');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userprefs`
--

DROP TABLE IF EXISTS `userprefs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userprefs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userID` bigint(20) unsigned NOT NULL,
  `name` varchar(200) NOT NULL,
  `value` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `userID` (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userprefs`
--

LOCK TABLES `userprefs` WRITE;
/*!40000 ALTER TABLE `userprefs` DISABLE KEYS */;
INSERT INTO `userprefs` VALUES (2,4,'vendor_template','Vendor agreement template'),(3,4,'msg_request_template','What hath God wrought?'),(4,4,'client_template','test one');
/*!40000 ALTER TABLE `userprefs` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-08-18 14:58:58
