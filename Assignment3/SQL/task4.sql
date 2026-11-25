-- task4.sql: Task 2, three types of INSERT
-- ============================================================================
-- Run order: SQL/task3.sql (empty schema), then THIS FILE, then
-- SRC/load_data.sql. Running it on the empty schema keeps each SELECT * short
-- enough to screenshot. Its keys (the task2 customer, the Espressif/Bosch/
-- Murata parts below) never occur in the generated data, so load_data.sql
-- still loads on top of these rows without a key clash.
--
-- Relation used for all three INSERTs: BOMLine (which parts a BOM needs, and
-- how many). Every BOMLine row needs its BOM and its Part to exist first
-- (two foreign keys), so the setup block creates those parent rows.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Setup: parent rows the three INSERTs refer to
-- ---------------------------------------------------------------------------
INSERT INTO Customer (Email, Username, Password, FirstName, LastName, HouseAddress,
                      City, Province, Country, PostCode)
VALUES ('task2.demo@example.com', 'task2demo',
        '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
        'Robin', 'Demo', '1151 Richmond St', 'London', 'Ontario', 'Canada', 'N6A 3K7');

INSERT INTO Part (ManufacturerName, Manufacturer_PartNum, Name, Category, Length, Width, Height)
VALUES ('Espressif', 'ESP32-C3-MINI-1', 'ESP32-C3 Wi-Fi/BLE Module 4MB Flash', 'MCU', 13.20, 16.60, 2.40),
       ('Bosch', 'BME280', 'Humidity, Pressure and Temperature Sensor', 'Sensor', 2.50, 2.50, 0.93),
       ('Murata', 'GRM188R71C104KA01D', '100nF 0603 X7R Capacitor 16V', 'Capacitor', 1.60, 0.80, 0.80),
       ('Wurth Elektronik', '61300411121', '4-Pin Male Header 2.54mm', 'Connector', 10.16, 2.54, 8.50);

INSERT INTO BOM (CustomerEmail, BOM_name, Date_created)
VALUES ('task2.demo@example.com', 'Rover Rev A', DATE '2026-11-20'),
       ('task2.demo@example.com', 'Rover Rev B', DATE '2026-11-24');

-- ---------------------------------------------------------------------------
-- INSERT 1: single row, VALUES with NO column list.
-- Every column is given, in the order of CREATE TABLE BOMLine
-- (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum, Quantity).
-- Differs from 2 and 3: no column list, one tuple, all values are constants.
-- ---------------------------------------------------------------------------
INSERT INTO BOMLine
VALUES ('task2.demo@example.com', 'Rover Rev A', 'Espressif', 'ESP32-C3-MINI-1', 1);

SELECT * FROM BOMLine;

-- ---------------------------------------------------------------------------
-- INSERT 2: several rows in ONE statement, with an explicit column list in a
-- DIFFERENT order from the table (Quantity first, the BOM key last).
-- Differs from 1: names its columns, so the values are matched by name and
-- not by position, and inserts three tuples at once (atomically: if one row
-- broke a constraint, none of the three would be inserted).
-- ---------------------------------------------------------------------------
INSERT INTO BOMLine (Quantity, ManufacturerName, Manufacturer_PartNum, CustomerEmail, BOM_name)
VALUES (1,  'Bosch',            'BME280',             'task2.demo@example.com', 'Rover Rev A'),
       (12, 'Murata',           'GRM188R71C104KA01D', 'task2.demo@example.com', 'Rover Rev A'),
       (2,  'Wurth Elektronik', '61300411121',        'task2.demo@example.com', 'Rover Rev A');

SELECT * FROM BOMLine;

-- ---------------------------------------------------------------------------
-- INSERT 3: INSERT ... SELECT. The new tuples are the RESULT OF A QUERY, not
-- literals: Rev B of the rover starts as a copy of Rev A, with double the
-- quantity of every part Rev A needs fewer than 10 of (the capacitors are
-- already ordered in bulk, so that line is left out).
-- Differs from 1 and 2: no VALUES clause at all; how many rows are inserted
-- depends on the data (here 3 of Rev A's 4 lines qualify).
-- ---------------------------------------------------------------------------
INSERT INTO BOMLine (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum, Quantity)
SELECT bl.CustomerEmail, 'Rover Rev B', bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity * 2
FROM BOMLine bl
WHERE bl.CustomerEmail = 'task2.demo@example.com'
  AND bl.BOM_name = 'Rover Rev A'
  AND bl.Quantity < 10;

SELECT * FROM BOMLine;
