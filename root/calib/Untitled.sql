CREATE TABLE IF NOT EXISTS `users` (
  `id` integer PRIMARY KEY,
  `username` varchar(255)
);

CREATE TABLE IF NOT EXISTS `calibration` (
  `id` integer PRIMARY KEY,
  `serial_num` varchar(255),
  `production_date` timestamp,
  `CHC` integer,
  `CHV` integer
);