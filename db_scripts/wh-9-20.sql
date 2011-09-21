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
  `dateCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dateSent` datetime DEFAULT NULL,
  `dateAccepted` datetime DEFAULT NULL,
  `dateModified` datetime DEFAULT NULL,
  `dateDeclined` datetime DEFAULT NULL,
  `dateCompleted` datetime DEFAULT NULL,
  `dateVerified` datetime DEFAULT NULL,
  `dateContested` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreement`
--

LOCK TABLES `agreement` WRITE;
/*!40000 ALTER TABLE `agreement` DISABLE KEYS */;
INSERT INTO `agreement` VALUES (2,16,4,'Analysis of Main Site','2011-06-29 22:39:58',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(4,4,5,'Waffle Dingus','2011-06-30 00:02:30','2011-08-18 14:54:51',NULL,'2011-07-06 14:40:54',NULL,NULL,NULL,NULL),(7,4,18,'Garden Work','2011-07-07 15:03:21','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(8,23,4,'Waistcoat Swimback','2011-07-19 17:58:17','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(10,4,20,'Gemology Ruddersqueak','2011-07-19 18:09:12','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(12,4,19,'Stovepipe Hubcap','2011-08-10 20:38:33','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(13,4,23,'Daredevil Alchemy','2011-08-12 00:30:59','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(14,4,14,'Snailpace Flipjack','2011-08-12 00:31:23','2011-08-18 14:54:51',NULL,NULL,'2011-08-12 14:01:11',NULL,NULL,NULL),(15,4,15,'Nickeldime Subwoofer','2011-08-12 00:31:52','2011-08-18 14:54:51',NULL,'2011-08-12 14:03:08','2011-08-12 14:03:08',NULL,NULL,NULL),(16,4,16,'Fistknife Armandhammer','2011-08-12 00:39:57','2011-08-18 14:54:51',NULL,NULL,NULL,NULL,NULL,NULL),(17,4,18,'Starstripe Rebelsnap','2011-08-12 00:42:07','2011-08-18 14:54:51','2011-09-19 17:25:21',NULL,NULL,NULL,NULL,NULL),(18,4,5,'Kneejerk Jumpingcow','2011-08-12 00:49:30','2011-08-18 16:12:07','2011-08-19 15:37:45',NULL,NULL,'2011-08-19 16:51:33','2011-08-19 17:05:27',NULL),(19,2,4,'Bazooka Artichoke','2011-08-15 20:30:43','2011-08-18 14:54:51','2011-09-20 14:57:03',NULL,NULL,NULL,NULL,NULL),(29,4,2,'Estimate (not sent)','2011-09-15 16:25:15',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(30,15,4,'Website Copywriting','2011-09-15 21:02:33',NULL,NULL,NULL,NULL,NULL,NULL,NULL);
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
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementPhase`
--

LOCK TABLES `agreementPhase` WRITE;
/*!40000 ALTER TABLE `agreementPhase` DISABLE KEYS */;
INSERT INTO `agreementPhase` VALUES (1,15,0,NULL,NULL,NULL,'A',NULL),(2,15,1,2,NULL,NULL,'B',NULL),(3,15,2,3,'2011-08-15 16:19:52',NULL,'C',NULL),(4,15,3,4,NULL,NULL,'D',NULL),(5,16,0,1000,NULL,NULL,'Aardvark artichoke',NULL),(6,16,1,2000,'2011-08-15 16:19:52','2011-08-15 16:20:14','Badger bok-choy',NULL),(7,16,2,3000,NULL,NULL,'Cicada cauliflower',NULL),(8,16,3,4000,NULL,NULL,'Dachshund dandelion',NULL),(9,17,0,1000,'2011-08-15 16:19:52',NULL,'Aardvark artichoke',NULL),(10,17,1,2000,NULL,NULL,'Badger bok-choy',NULL),(11,17,2,3000,NULL,NULL,'Cicada cauliflower',NULL),(12,17,3,4000,'2011-08-15 16:19:52','2011-08-15 16:20:14','Dachshund dandelion',NULL),(13,18,0,2000,NULL,NULL,'Initial project requirements, wireframe proposals, derpity derp.',NULL),(14,18,1,2000,'2011-08-15 16:20:39','2011-08-15 16:20:45','Revise and complete wireframes for client approval. Begin functional spec.',NULL),(15,18,2,2000,'2011-08-15 16:19:52',NULL,'Client review of functional spec and final wireframes. Begin rough coding and user testing.',NULL),(16,18,3,1500,'2011-08-15 16:20:33',NULL,'User testing complete; Add design and polish. Fit and finish for final review.',NULL),(17,19,0,40000,NULL,NULL,'Testing one, two, three.','Sounds good to me.'),(18,19,1,50000,NULL,NULL,'Mic check, ahhh- ahh- ahhh- mic check.','Got it.'),(19,19,2,100000,NULL,NULL,'Another test','You\'re awesome!'),(20,20,0,130000,NULL,NULL,'One, een, ein, uno, un, ichi.',NULL),(21,20,1,100000,NULL,NULL,'Two, twee, zwei, dos, deux, ni.',NULL),(22,20,2,100000,NULL,NULL,'Three, drie, drei, tres, trois, san.',NULL),(23,21,0,500,NULL,NULL,'A',NULL),(24,21,1,100,NULL,NULL,'I',NULL),(25,21,2,100,NULL,NULL,'R',NULL),(26,21,3,100,NULL,NULL,'D',NULL),(27,22,0,500,NULL,NULL,'A',NULL),(28,22,1,100,NULL,NULL,'I',NULL),(29,22,2,100,NULL,NULL,'R',NULL),(30,22,3,100,NULL,NULL,'D',NULL),(31,23,0,100,NULL,NULL,'s',NULL),(32,23,1,NULL,NULL,NULL,'k',NULL),(33,23,2,300,NULL,NULL,'a',NULL),(34,23,3,400,NULL,NULL,'k',NULL),(35,24,0,100,NULL,NULL,'a',NULL),(36,24,1,NULL,NULL,NULL,'a',NULL),(37,24,2,300,NULL,NULL,'a',NULL),(38,24,3,NULL,NULL,NULL,'l',NULL),(39,26,0,100,NULL,NULL,'a',NULL),(40,26,1,NULL,NULL,NULL,'a',NULL),(41,26,2,300,NULL,NULL,'a',NULL),(42,26,3,NULL,NULL,NULL,'l',NULL),(43,27,0,100,NULL,NULL,'a',NULL),(44,27,1,NULL,NULL,NULL,'a',NULL),(45,27,2,300,NULL,NULL,'a',NULL),(46,27,3,NULL,NULL,NULL,'l',NULL),(47,28,0,100000,NULL,NULL,'asdlfkj',NULL),(48,28,1,200000,NULL,NULL,'aslkdfhlk lasdkj alkj we',NULL),(49,28,2,320000,NULL,NULL,'alhg iwgoh wiioh egw',NULL),(50,28,3,420102,NULL,NULL,'lawgh gowae hi; hog h wgah',NULL),(51,29,0,100000,NULL,NULL,'Nunc pretium quam eu ligula pellentesque gravida.',NULL),(52,29,1,120000,NULL,NULL,'Donec laoreet dui quis arcu. Vestibulum aliquam.',NULL),(53,29,2,120000,NULL,NULL,'Etiam eu quam a quam mattis placerat. In adipiscing tristique ornare.',NULL),(54,30,0,50000,NULL,NULL,'Establishment of project scope; weekly brainstorming meetings.',NULL),(55,30,1,50000,NULL,NULL,'Finalized project scope and rough drafts for each section.',NULL),(56,30,2,50000,NULL,NULL,'Editing. Final drafts submitted for approval and final proofing.',NULL),(57,30,3,50000,NULL,NULL,'Final proof and delivery of final product.',NULL),(58,8,0,50000,NULL,NULL,'Project outline and negotiated scope of work',NULL),(59,8,1,100000,NULL,NULL,'Detailed feasibility study and response steps',NULL),(60,8,2,100000,NULL,NULL,'Implement response to project guidelines',NULL),(61,8,3,100000,NULL,NULL,'Post-mortem review of changes, analysis and response to oversights and shortcomings',NULL);
/*!40000 ALTER TABLE `agreementPhase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agreementSummary`
--

DROP TABLE IF EXISTS `agreementSummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agreementSummary` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `agreementID` bigint(20) unsigned NOT NULL,
  `summary` text,
  `comments` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agreementID` (`agreementID`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agreementSummary`
--

LOCK TABLES `agreementSummary` WRITE;
/*!40000 ALTER TABLE `agreementSummary` DISABLE KEYS */;
INSERT INTO `agreementSummary` VALUES (1,1,'Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.',NULL),(2,2,'Integer pellentesque sapien. Maecenas urna tortor, ornare id, fringilla porttitor, vestibulum eget, est. Donec in purus sed elit mollis adipiscing. Phasellus mi purus, convallis a, congue sit amet, ultricies nec, ante. Suspendisse potenti. Donec laoreet dui quis arcu. Vestibulum aliquam.',NULL),(3,4,'Bacon ipsum dolor sit amet ut spare ribs tail boudin sed beef, sausage sirloin pastrami commodo. Reprehenderit bresaola in, labore drumstick esse eu beef bacon ribeye brisket velit. Aliqua veniam eu bresaola cillum occaecat. Magna ut short loin cow t-bone. Proident ad t-bone brisket bresaola ea. Incididunt tri-tip t-bone, qui sirloin mollit in ribeye commodo pork sausage bresaola. Officia enim cillum, nisi sunt shoulder magna in.',NULL),(4,3,'Sausage ham reprehenderit, tempor pastrami in meatloaf beef ut tenderloin sirloin culpa tri-tip. Ground round chuck do pork chop, pork loin flank venison duis qui tri-tip andouille non reprehenderit aliquip. Laboris jowl in, pork hamburger bresaola occaecat sed rump. Eiusmod t-bone corned beef, tongue labore swine meatball ullamco culpa reprehenderit short loin dolore. Commodo ut short ribs, reprehenderit officia brisket elit veniam jowl cow anim laborum turkey. Pork sausage pork belly sirloin brisket chicken jerky, pariatur excepteur voluptate. Deserunt swine meatball strip steak, id chicken nulla flank ut jerky in ribeye ham hock boudin.',NULL),(5,5,'Flapjack',NULL),(6,6,'I will make a web site. You will pay me $12,000',NULL),(7,7,'I\'ll mow your lawn once a week, and water monthly.',NULL),(8,8,'The quick brown foo jumps over the lazy quux',NULL),(9,10,'The quick brown foo jumps over the lazy quux',NULL),(10,11,'The quick brown foo jumps over the lazy quux',NULL),(11,20,'Zip zoople zap, zip zarble zonker. Zazzle. Zimmer zom zoomen zam zanden.',NULL),(12,21,'The quick brown fox jumps over the lazy dog.',NULL),(13,22,'The quick brown fox jumps over the lazy dog.',NULL),(14,23,'sasdf',NULL),(15,24,'fop',NULL),(16,25,'fop',NULL),(17,26,'fop',NULL),(18,27,'fop',NULL),(19,28,'fop',NULL),(20,29,'Integer pellentesque sapien. Maecenas urna tortor, ornare id, fringilla porttitor, vestibulum eget, est. Donec in purus sed elit mollis adipiscing. Phasellus mi purus, convallis a, congue sit amet, ultricies nec, ante. Suspendisse potenti.','Maecenas urna tortor, ornare id, fringilla porttitor, vestibulum eget, est.'),(21,30,'Three short pages of copy for a promotional web site. Deliverables include professionally edited text and whatnot. Don\'t forget the whatnot.',NULL),(22,19,NULL,NULL);
/*!40000 ALTER TABLE `agreementSummary` ENABLE KEYS */;
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
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `payment` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `fromClientID` bigint(20) unsigned NOT NULL,
  `toVendorID` bigint(20) unsigned NOT NULL,
  `agreementPhaseID` bigint(20) unsigned NOT NULL,
  `amount` int(10) unsigned NOT NULL,
  `dateInitiated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dateDeclined` datetime DEFAULT NULL,
  `dateApproved` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `profile`
--

LOCK TABLES `profile` WRITE;
/*!40000 ALTER TABLE `profile` DISABLE KEYS */;
INSERT INTO `profile` VALUES (1,3,'I\'m a coder. I write code. \'\" SELECT * FROM user;',NULL,NULL,NULL,NULL,NULL),(2,4,'I\'m a coder. I write code.',NULL,NULL,NULL,'brendn','brendn'),(3,13,'I don\'t exist',NULL,NULL,NULL,'Test','test'),(4,14,NULL,NULL,NULL,NULL,'FU','fu'),(5,2,'The big kahuna',NULL,NULL,NULL,'me','me');
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
  `confirmationCode` varchar(60) DEFAULT NULL,
  `confirmationHash` varchar(60) DEFAULT NULL,
  `confirmed` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `subscriberStatus` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `firstName` varchar(60) DEFAULT NULL,
  `lastName` varchar(60) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'brendan@plusminusfive.com',NULL,NULL,0,1,'Brendan','Berg',NULL,'$2a$12$sYBm0rARxK6lJ2olxIg9E.z4GVEKST80r9K3GcfnCGlg1BhR/Rzc.',NULL,NULL,NULL,'http://media.wurkhappy.com/6pcXrtMw3LiMxoHEVHhRijkm2yN.jpg',NULL,NULL,'2011-02-17 03:14:50'),(2,'marcus@wurkhappy.com',NULL,NULL,0,1,'Marcus','Ellison',NULL,'$2a$12$sYBm0rARxK6lJ2olxIg9E.z4GVEKST80r9K3GcfnCGlg1BhR/Rzc.',NULL,NULL,NULL,'http://media.wurkhappy.com/3BcWTHXew8n7VeSmEUoaeqsamTnz_o.jpg','http://media.wurkhappy.com/3BcWTHXew8n7VeSmEUoaeqsamTnz_s.jpg','http://media.wurkhappy.com/3BcWTHXew8n7VeSmEUoaeqsamTnz_l.jpg','2011-02-17 03:14:50'),(4,'brendan@wurkhappy.com','XOEDBJ','pPb_t1beRxahjmQOWJyfop7voCg=',0,1,'Brendan H.','Berg','(646) 478-6927','$2a$12$4OkzF.RnlVoouxtsinXfY./oynwfmfWhAYGwdQsaS/0/DTRLHWrka',NULL,NULL,NULL,'http://media.wurkhappy.com/htCoUWFX3PRriKQVzj7ZX8RcED3_o.jpg','http://media.wurkhappy.com/htCoUWFX3PRriKQVzj7ZX8RcED3_s.jpg','http://media.wurkhappy.com/htCoUWFX3PRriKQVzj7ZX8RcED3_l.jpg','2011-04-07 04:03:21'),(5,'jon@appleseed.com','YWLATQ','eQbSODnODK8a2sQ_bzLSwN80YZM=',0,1,'Jon','Appleseed',NULL,'$2a$12$sYBm0rARxK6lJ2olxIg9E.z4GVEKST80r9K3GcfnCGlg1BhR/Rzc.',NULL,NULL,NULL,'http://media.wurkhappy.com/3D4NSn3jd1hRt8ByQLK2HNDzNUrm_o.jpg','http://media.wurkhappy.com/3D4NSn3jd1hRt8ByQLK2HNDzNUrm_s.jpg','http://media.wurkhappy.com/3D4NSn3jd1hRt8ByQLK2HNDzNUrm_l.jpg','2011-06-20 22:51:44'),(14,'john@example.com','MVWTEI','8wfK8mwJR3rXTM5aA2Tiypyd9rs=',0,1,'John','Example',NULL,'$2a$12$sYBm0rARxK6lJ2olxIg9E.z4GVEKST80r9K3GcfnCGlg1BhR/Rzc.',NULL,NULL,NULL,'http://media.wurkhappy.com/JhnkYCvCmPBtK2eocXRkSQNPBay_o.jpg','http://media.wurkhappy.com/JhnkYCvCmPBtK2eocXRkSQNPBay_s.jpg','http://media.wurkhappy.com/JhnkYCvCmPBtK2eocXRkSQNPBay_l.jpg','2011-08-18 19:11:08'),(15,'julie@chu.com','XQRNMH','DVFXCyNXdYd587JL7JeBrlR7Ldk=',0,1,'Julie','Chu',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/2rTff9KRSeU7GnVnuWE56MWyLh3p_o.jpg','http://media.wurkhappy.com/2rTff9KRSeU7GnVnuWE56MWyLh3p_s.jpg','http://media.wurkhappy.com/2rTff9KRSeU7GnVnuWE56MWyLh3p_l.jpg','2011-09-05 23:58:55'),(16,'sarah@forrest.com','FNQHYG','vh3z68IudMg2jFbUPK6CIcV3yxc=',0,1,'Sarah','Forrest',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/sAKUGZg8VJ4jEmGfzBrQ9FoxCSD_o.jpg','http://media.wurkhappy.com/sAKUGZg8VJ4jEmGfzBrQ9FoxCSD_s.jpg','http://media.wurkhappy.com/sAKUGZg8VJ4jEmGfzBrQ9FoxCSD_l.jpg','2011-09-06 00:00:55'),(17,'jen@baker.com','BQHJCN','X_geE7yueBZZ4C_0VPW9pRvwC68=',0,1,'Jen','Baker',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/3JkoHJqxmzxZrrvRaVf36Xt3CxG7_o.jpg','http://media.wurkhappy.com/3JkoHJqxmzxZrrvRaVf36Xt3CxG7_s.jpg','http://media.wurkhappy.com/3JkoHJqxmzxZrrvRaVf36Xt3CxG7_l.jpg','2011-09-06 00:02:04'),(18,'alissa@hess.com','JCHWJO','w6hIjhz9KHTmV1KgWaCJixkpiKc=',0,1,'Alissa','Hess',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/2fRYg31221JLke6cZciu1JkLosqN_o.jpg','http://media.wurkhappy.com/2fRYg31221JLke6cZciu1JkLosqN_s.jpg','http://media.wurkhappy.com/2fRYg31221JLke6cZciu1JkLosqN_l.jpg','2011-09-06 00:03:49'),(19,'maggie@hudson.com','JGMSIM','9TXVI3k-ZwnPzOc3u1gt2BOOxDQ=',0,1,'Maggie','Hudson','(212) 555-1212','$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/GFBDCEMaQP8w3gxyUcyF5xaqQKB_o.jpg','http://media.wurkhappy.com/GFBDCEMaQP8w3gxyUcyF5xaqQKB_s.jpg','http://media.wurkhappy.com/GFBDCEMaQP8w3gxyUcyF5xaqQKB_l.jpg','2011-09-06 00:06:26'),(20,'beth@norton.com','EUTQII','x8XSnlymM9a7kvGfTDl1zgYumuc=',0,1,'Beth','Norton',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/33uiuuMuYp2XxspryKoK5dZeF8mS_o.jpg','http://media.wurkhappy.com/33uiuuMuYp2XxspryKoK5dZeF8mS_s.jpg','http://media.wurkhappy.com/33uiuuMuYp2XxspryKoK5dZeF8mS_l.jpg','2011-09-06 00:11:08'),(23,'joe@smith.com','VWEPRN','KGRIwZEf7a4-JZX8p-Ptf7z4pf8=',0,0,'Joe','Smith',NULL,'$2a$12$lAMtw8Vdpw2WbXucLsssMecSKPoGThKfDNRD7psz605GCAXJQ7w7e',NULL,NULL,NULL,'http://media.wurkhappy.com/2DD5CFVNzq9ZUdcqoSNqTFDp2pyo_o.jpg','http://media.wurkhappy.com/2DD5CFVNzq9ZUdcqoSNqTFDp2pyo_s.jpg','http://media.wurkhappy.com/2DD5CFVNzq9ZUdcqoSNqTFDp2pyo_l.jpg','2011-09-15 19:43:23');
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

-- Dump completed on 2011-09-20 23:14:17
