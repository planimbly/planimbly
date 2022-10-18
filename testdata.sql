DELETE
FROM organizations_organization
WHERE id <> 0;
INSERT INTO organizations_organization
VALUES (1, 'UAM');

DELETE
FROM organizations_unit
WHERE id <> 0;
INSERT INTO organizations_unit
VALUES (1, 'WMI', 1, 1),
       (2, 'WNPiD', 1, 1);

DELETE
FROM organizations_workplace
WHERE id <> 0;
INSERT INTO organizations_workplace
VALUES (1, 'Portiernia A', 1),
       (2, 'Portiernia B', 1),
       (3, 'Szatnia', 1),
       (4, 'Portiernia A', 2),
       (5, 'Portiernia B', 2),
       (6, 'Szatnia', 2);

DELETE
FROM schedules_shifttype
WHERE id <> 0;
INSERT INTO schedules_shifttype
VALUES (1, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 1),
       (2, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 1),
       (3, '22:00:00', '06:00:00', 'N', '1111111', 1, 0, 1),
       (4, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 2),
       (5, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 2),
       (6, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 3),
       (7, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 3),
       (8, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 4),
       (9, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 4),
       (10, '22:00:00', '06:00:00', 'N', '1111111', 1, 0, 4),
       (11, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 5),
       (12, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 5),
       (13, '06:00:00', '14:00:00', 'M', '1111111', 1, 0, 6),
       (14, '14:00:00', '22:00:00', 'A', '1111111', 1, 0, 6);

DELETE
FROM accounts_employee
WHERE id <> 0;
INSERT INTO accounts_employee
VALUES (1, 'pbkdf2_sha256$320000$ENO69ud6qXm5XKqWBkDQXh$/WZVTdrLmVU4SIfDBTGluR0+HUXdLK36/67/NEpcaMc=', NULL, 1, '', '', 1, 1, '2022-04-06 10:49:31.677561', 'admin@admin.com', 0, 0, 1, 'admin'),
       (2, 'pbkdf2_sha256$320000$ENO4df044f4e8029ddd468640911239741405a996ac32566ff1061ac4214368fff9', NULL, 0, 'Janusz', 'Dobronic', 0, 1, '2022-04-06 10:49:31.677561', 'janusz.dobronic@gmail.com', 160, 0, 1, 'jandob12'),
       (3, 'pbkdf2_sha256$320000$ENO4c2ee01d7d1375f7f891b97c974e5264b657eccd947cbb3315b253e6875ceac4', NULL, 0, 'Jozef', 'Topolewski', 0, 1, '2022-04-06 10:49:31.677561', 'jozef.topolewski@gmail.com', 160, 0, 1, 'joztop13'),
       (4, 'pbkdf2_sha256$320000$ENO0f12f5e647e863baf55d6bb1b85d0dac21830bbcd8b702e09dc266bfbdfc0e25', NULL, 0, 'Jan', 'Plank', 0, 1, '2022-04-06 10:49:31.677561', 'jan.plank@gmail.com', 160, 0, 1, 'janpla44'),
       (5, 'pbkdf2_sha256$320000$ENO76e35d06348033ab26d9387e6cfd0e4b105b875e17ed8adb45e6d7c95916c62e', NULL, 0, 'Janusz', 'Glownikowski', 0, 1, '2022-04-06 10:49:31.677561', 'janusz.glownikowski@gmail.com', 160, 0, 1, 'janglow3'),
       (6, 'pbkdf2_sha256$320000$ENO3cb4e61d8c9c176beb0fe2c3f80523553824055d9b515fe8c44b4c66240f8d2a', NULL, 0, 'Arnold', 'Grochowski', 0, 1, '2022-04-06 10:49:31.677561', 'arnold.grochowski@gmail.com', 160, 0, 1, 'arngro188'),
       (7, 'pbkdf2_sha256$320000$ENO5e0805ccbfbed258fbd4661f2cf3f1c5423a8ddb9e8ff5031dc65f3d1c22b8bf', NULL, 0, 'Andrzej', 'Wolanski', 0, 1, '2022-04-06 10:49:31.677561', 'andrzej.wolanski@gmail.com', 80, 0, 1, 'andwol44'),
       (8, 'pbkdf2_sha256$320000$ENO4a41dc7f7cd47ac894c3a4442f1d84e0a9ac8a1908192b9389b16fe9dbbf263e', NULL, 0, 'Violetta', 'Wojciechowska', 0, 1, '2022-04-06 10:49:31.677561', 'violetta.wojciechowska@gmail.com', 160, 0, 1, 'viowoj'),
       (9, 'pbkdf2_sha256$320000$ENObae7eb7e4935b44f64579e029c43d2803783513fda0375e7ef51fb401aca73fb', NULL, 0, 'Renata', 'Kujawa', 0, 1, '2022-04-06 10:49:31.677561', 'renata.kujawa@gmail.com', 80, 0, 1, 'renkuj65'),
       (10, 'pbkdf2_sha256$320000$ENO3abd5a2f54c69aaa6a8a150eed5d0cdc388ff536c40b98f3b85012419bc3e86e', NULL, 0, 'Violetta', 'Stachowiak', 0, 1, '2022-04-06 10:49:31.677561', 'viloletta.stachowiak@gmail.com', 160, 0, 1, 'viosta33'),
       (11, 'pbkdf2_sha256$320000$ENO31baef8e072654c0f18b77922d6b0dbd4e4c2003c68625094a0682b0898d38b8', NULL, 0, 'Beata', 'Kaczmarek', 0, 1, '2022-04-06 10:49:31.677561', 'beata.kaczmarek@gmail.com', 160, 0, 1, 'beakac22'),
       (12, 'pbkdf2_sha256$320000$ENO2bb7e1ba58355646d1b2422f96417d75d00ccfd1cd1d8b3ef6834286d01640ca', NULL, 0, 'Ryszard', 'Andrzejewski', 0, 1, '2022-04-06 10:49:31.677561', 'ryszard.andrzejewski@gmail.com', 80, 0, 1, 'rysand41'),
       (13, 'pbkdf2_sha256$320000$ENOcfd5af6b28636ad32bbef00e907b7e47272c6954809f1de45e2bf5a52760280b', NULL, 0, 'Joanna', 'Pilarska', 0, 1, '2022-04-06 10:49:31.677561', 'joanna.pilarska@gmail.com', 120, 0, 1, 'joapil83'),
       (14, 'pbkdf2_sha256$320000$ENOf88ac6a0b4a4ef80fe216b1198e21a03df6d99e2afde799c4db4ed69398dc687', NULL, 0, 'Waldemar', 'Mazurek', 0, 1, '2022-04-06 10:49:31.677561', 'waldemar.mazurek@gmail.com', 160, 0, 1, 'walmaz89'),
       (15, 'pbkdf2_sha256$320000$rV4HmIa83sGYYH3MuKiBcV$IrB0bSF87EIMlu5FDscJz1Ec472NYBRG/wpyJkQPdNs=', NULL, 0, 'Jan', 'Kujawa', 0, 1, '2022-04-06 10:49:31.677561', 'Jan.Kujawa@gmail.com', 120, 0, 1, 'jankuj45'),
       (16, 'pbkdf2_sha256$320000$Q1fc1GPBetwY6nnyZNHXnk$Ui0nZK8i4yzFhOAgkpXz1yt2EessKEjoqplcJJ/bW1k=', NULL, 0, 'Aleksandra', 'Bartkowiak', 0, 1, '2022-04-06 10:49:31.677561', 'aleksandra.bartkowiak@gmail.com', 160, 0, 1, 'alebar92');

DELETE
FROM accounts_employee_user_unit
WHERE id <> 0;
INSERT INTO accounts_employee_user_unit
VALUES (1, 2, 1),
       (2, 3, 1),
       (3, 4, 1),
       (4, 5, 1),
       (5, 6, 1),
       (6, 7, 1),
       (7, 8, 1),
       (8, 9, 1),
       (9, 10, 1),

       (10, 11, 2),
       (11, 12, 2),
       (12, 13, 2),
       (13, 14, 2),
       (14, 15, 2),
       (15, 16, 2);

DELETE
FROM accounts_employee_user_workplace
WHERE id <> 0;
INSERT INTO accounts_employee_user_workplace
VALUES (4, 2, 1),
       (5, 2, 2),
       (6, 2, 3),
       (7, 3, 1),
       (8, 3, 2),
       (9, 3, 3),
       (10, 4, 1),
       (11, 4, 2),
       (12, 4, 3),
       (13, 5, 1),
       (14, 5, 2),
       (15, 5, 3),
       (16, 6, 1),
       (17, 6, 2),
       (18, 6, 3),
       (19, 7, 1),
       (20, 7, 2),
       (21, 7, 3),
       (22, 8, 1),
       (23, 8, 2),
       (24, 8, 3),
       (25, 9, 1),
       (26, 9, 2),
       (27, 9, 3),
       (28, 10, 1),
       (29, 10, 2),
       (30, 10, 3),
       (31, 11, 4),
       (32, 11, 5),
       (33, 11, 6),
       (34, 12, 4),
       (35, 12, 5),
       (36, 12, 6),
       (38, 13, 5),
       (39, 13, 6),
       (40, 14, 4),
       (41, 14, 5),
       (42, 14, 6),
       (43, 15, 4),
       (44, 15, 5),
       (45, 15, 6),
       (46, 16, 4),
       (47, 16, 5),
       (48, 16, 6);

DELETE
FROM schedules_schedule
WHERE id <> 0;
DELETE
FROM schedules_shift
WHERE id <> 0;