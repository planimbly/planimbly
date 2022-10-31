DELETE
FROM organizations_organization
WHERE id <> 0;
INSERT INTO organizations_organization
VALUES (1, 'SKLEPY sp. z o. o.');

DELETE
FROM organizations_unit
WHERE id <> 0;
INSERT INTO organizations_unit
VALUES (1, 'SKLEP POZNAŃ', TRUE, 1),
       (2, 'SKLEP WARSZAWA', TRUE, 1);

DELETE
FROM organizations_workplace
WHERE id <> 0;
INSERT INTO organizations_workplace
VALUES (1, 'Magazyn', 1),
       (2, 'Kasa', 1),
       (3, 'Ochrona', 1),
       (4, 'Kasa', 2);

DELETE
FROM schedules_shifttype
WHERE id <> 0;
INSERT INTO schedules_shifttype
VALUES (1, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 1, 1, 'FFFFFF'),
       (2, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 1, 1, 'FFFFFF'),
       (3, '22:00:00', '06:00:00', 'N', '1111111', TRUE, FALSE, 1, 1, 'FFFFFF'),
       (4, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 2, 1, 'FFFFFF'),
       (5, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 2, 1, 'FFFFFF'),
       (6, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 3, 1, 'FFFFFF'),
       (7, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 3, 1, 'FFFFFF'),
       (8, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 4, 1, 'FFFFFF'),
       (9, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 4, 1, 'FFFFFF'),
       (10, '22:00:00', '06:00:00', 'N', '1111111', TRUE, FALSE, 4, 1, 'FFFFFF'),
       (11, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 5, 1, 'FFFFFF'),
       (12, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 5, 1, 'FFFFFF'),
       (13, '06:00:00', '14:00:00', 'M', '1111111', TRUE, FALSE, 6, 1, 'FFFFFF'),
       (14, '14:00:00', '22:00:00', 'A', '1111111', TRUE, FALSE, 6, 1, 'FFFFFF');

DELETE
FROM accounts_employee
WHERE id <> 0;
INSERT INTO accounts_employee
VALUES (1, 'pbkdf2_sha256$320000$iszi9G4mmCHdk310qnkPvB$JtkEdMgQCcVU2QaK7+IJc5Ngd85kHMLlK8ffqTzCmPY=', NULL, TRUE, 'admin','', '', TRUE, TRUE, '2022-04-06 10:49:31.677561', 'admin@admin.com', 0, FALSE, 1),
       (2, 'pbkdf2_sha256$320000$ENO4df044f4e8029ddd468640911239741405a996ac32566ff1061ac4214368fff9', NULL, FALSE, 'danwro12','Daniel', 'Wróbel', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'daniel.wrobel@gmail.com', 160, FALSE, 1),
       (3, 'pbkdf2_sha256$320000$ENO4c2ee01d7d1375f7f891b97c974e5264b657eccd947cbb3315b253e6875ceac4', NULL, FALSE, 'arcban13','Archibald', 'Banach', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'archibald.banach@gmail.com', 160, FALSE, 1),
       (4, 'pbkdf2_sha256$320000$ENO0f12f5e647e863baf55d6bb1b85d0dac21830bbcd8b702e09dc266bfbdfc0e25', NULL, FALSE, 'patwnu44','Patryk', 'Wnuk', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'patryk.wnuk@gmail.com', 160, FALSE, 1),
       (5, 'pbkdf2_sha256$320000$ENO76e35d06348033ab26d9387e6cfd0e4b105b875e17ed8adb45e6d7c95916c62e', NULL, FALSE, 'sewkraw3','Seweryn', 'Krawiec', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'seweryn.krawiec@gmail.com', 160, FALSE, 1),
       (6, 'pbkdf2_sha256$320000$ENO3cb4e61d8c9c176beb0fe2c3f80523553824055d9b515fe8c44b4c66240f8d2a', NULL, FALSE, 'sylko188','Sylwester', 'Kozioł', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'sylwester.koziol@gmail.com', 160, FALSE, 1),
       (7, 'pbkdf2_sha256$320000$ENO5e0805ccbfbed258fbd4661f2cf3f1c5423a8ddb9e8ff5031dc65f3d1c22b8bf', NULL, FALSE, 'mirmaj44','Miron', 'Majcher', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'miron.majcher@gmail.com', 80, FALSE, 1),
       (8, 'pbkdf2_sha256$320000$ENO4a41dc7f7cd47ac894c3a4442f1d84e0a9ac8a1908192b9389b16fe9dbbf263e', NULL, FALSE, 'berzar','Bertrand', 'Zaremba', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'bertrand.zaremba@gmail.com', 160, FALSE, 1),
       (9, 'pbkdf2_sha256$320000$ENObae7eb7e4935b44f64579e029c43d2803783513fda0375e7ef51fb401aca73fb', NULL, FALSE, 'wlofra','Włodzimierz', 'Frątczak', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'wlodzirmierz.fratczak@gmail.com', 80, FALSE, 1),
       (10, 'pbkdf2_sha256$320000$ENO3abd5a2f54c69aaa6a8a150eed5d0cdc388ff536c40b98f3b85012419bc3e86e', NULL, FALSE, 'kwimako1','Kwintyn', 'Makowski', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'kwintyn.makowski@gmail.com', 160, FALSE, 1),
       (11, 'pbkdf2_sha256$320000$ENO31baef8e072654c0f18b77922d6b0dbd4e4c2003c68625094a0682b0898d38b8', NULL, FALSE, 'filewi0','Filip', 'Lewicki', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'filip.lewicki@gmail.com', 160, FALSE, 1),
       (12, 'pbkdf2_sha256$320000$ENO2bb7e1ba58355646d1b2422f96417d75d00ccfd1cd1d8b3ef6834286d01640ca', NULL, FALSE, 'makope12','Mateusz', 'Kopeć', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'mateusz.kopeć@gmail.com', 80, FALSE, 1),
       (13, 'pbkdf2_sha256$320000$ENOcfd5af6b28636ad32bbef00e907b7e47272c6954809f1de45e2bf5a52760280b', NULL, FALSE, 'humaj83','Hubert', 'Maj', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'hubert.maj@gmail.com', 120, FALSE, 1),
       (14, 'pbkdf2_sha256$320000$ENOf88ac6a0b4a4ef80fe216b1198e21a03df6d99e2afde799c4db4ed69398dc687', NULL, FALSE, 'gemale89','Gedeon', 'Małek', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'gedeon.malek@gmail.com', 160, FALSE, 1),
       (15, 'pbkdf2_sha256$320000$rV4HmIa83sGYYH3MuKiBcV$IrB0bSF87EIMlu5FDscJz1Ec472NYBRG/wpyJkQPdNs=', NULL, FALSE, 'ksead45','Ksenofont', 'Adamiak', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'ksenofont.adamiak@gmail.com', 120, FALSE, 1),
       (16, 'pbkdf2_sha256$320000$Q1fc1GPBetwY6nnyZNHXnk$Ui0nZK8i4yzFhOAgkpXz1yt2EessKEjoqplcJJ/bW1k=', NULL, FALSE, 'cenie92','Cecyliusz', 'Niedźwiecki', FALSE, TRUE, '2022-04-06 10:49:31.677561', 'cecyliusz.niedzwiecki@gmail.com', 160, FALSE, 1);

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
       (32, 12, 4),
       (33, 13, 4),
       (34, 14, 4),
       (35, 15, 4),
       (36, 16, 4);

DELETE
FROM schedules_schedule
WHERE id <> 0;
DELETE
FROM schedules_shift
WHERE id <> 0;