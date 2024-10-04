 CREATE TABLE `admin` (
  `UserID` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(40) DEFAULT 'admin',
  `SNo` int NOT NULL,
  PRIMARY KEY (`UserID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


 CREATE TABLE `allotment` (
  `AllotmentID` int NOT NULL AUTO_INCREMENT,
  `VehicleID` int NOT NULL,
  `SNo` int NOT NULL,
  `username` varchar(100) NOT NULL,
  `date` date NOT NULL,
  `TimeFrom` time NOT NULL,
  `TimeTo` time NOT NULL,
  `duration` varchar(30) NOT NULL,
  `name` varchar(50) NOT NULL,
  `contact` bigint NOT NULL,
  `TotalPrice` int NOT NULL,
  `mode` varchar(40) NOT NULL,
  `VehicleType` varchar(40) NOT NULL,
  `VehicleNumber` varchar(40) NOT NULL,
  PRIMARY KEY (`AllotmentID`),
  KEY `fk_sno` (`SNo`)
) ENGINE=InnoDB AUTO_INCREMENT=107 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


 CREATE TABLE `bookingslot` (
  `BSlotID` int NOT NULL AUTO_INCREMENT,
  `Date` date DEFAULT NULL,
  `TimeFrom` time DEFAULT NULL,
  `TimeTo` time DEFAULT NULL,
  `duration` varchar(30) DEFAULT NULL,
  `SNo` int NOT NULL DEFAULT '1',
  `VehicleID` int NOT NULL,
  PRIMARY KEY (`BSlotID`),
  CONSTRAINT `bookingslot_ibfk_1` FOREIGN KEY (`BSlotID`) REFERENCES `slots` (`SlotID`),
  CONSTRAINT `bookingslot_ibfk_2` FOREIGN KEY (`BSlotID`) REFERENCES `vehicle` (`VehicleID`),
  CONSTRAINT `bookingslot_ibfk_3` FOREIGN KEY (`BSlotID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=95 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


 CREATE TABLE `owner` (
  `OwnerID` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  `contact` bigint DEFAULT NULL,
  `SNo` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`OwnerID`),
  CONSTRAINT `owner_ibfk_1` FOREIGN KEY (`OwnerID`) REFERENCES `user` (`UserID`)
) ENGINE=InnoDB AUTO_INCREMENT=220 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


 CREATE TABLE `payment` (
  `PaymentID` int NOT NULL AUTO_INCREMENT,
  `TotalPrice` int DEFAULT NULL,
  `mode` varchar(30) DEFAULT NULL,
  `SNo` int NOT NULL,
  `VehicleID` int NOT NULL,
  PRIMARY KEY (`PaymentID`),
  CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`PaymentID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `payment_ibfk_2` FOREIGN KEY (`PaymentID`) REFERENCES `bookingslot` (`BSlotID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=91 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 


 CREATE TABLE `sensor` (
  `SensorID` int NOT NULL AUTO_INCREMENT,
  `isParked` tinyint DEFAULT NULL,
  PRIMARY KEY (`SensorID`),
  CONSTRAINT `sensor_ibfk_1` FOREIGN KEY (`SensorID`) REFERENCES `slots` (`SlotID`)
) ENGINE=InnoDB AUTO_INCREMENT=92 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


 CREATE TABLE `slots` (
  `SlotID` int NOT NULL AUTO_INCREMENT,
  `space` varchar(30) DEFAULT NULL,
  `price` int DEFAULT NULL,
  PRIMARY KEY (`SlotID`)
) ENGINE=InnoDB AUTO_INCREMENT=92 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 


 CREATE TABLE `user` (
  `UserID` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(40) DEFAULT 'user',
  `SNo` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`UserID`),
  UNIQUE KEY `SNo` (`SNo`)
) ENGINE=InnoDB AUTO_INCREMENT=245 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 


 CREATE TABLE `vehicle` (
  `VehicleID` int NOT NULL AUTO_INCREMENT,
  `VehicleType` varchar(40) DEFAULT NULL,
  `VehicleNumber` varchar(40) DEFAULT NULL,
  `SNo` int NOT NULL,
  `VehicleName` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`VehicleID`)
) ENGINE=InnoDB AUTO_INCREMENT=147 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci