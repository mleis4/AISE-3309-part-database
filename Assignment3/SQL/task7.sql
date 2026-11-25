-- task7.sql: Task 5, three data modification commands
-- ============================================================================
-- Run after SQL/task3.sql, SQL/task4.sql and SRC/load_data.sql.
-- M1 is an INSERT ... SELECT, M2 an UPDATE of many tuples chosen by a
-- subquery, M3 a DELETE of a set chosen by a correlated subquery that
-- cascades to a child relation. Each is surrounded by SELECTs that show its
-- effect. M2b and M3b show constraints the DBMS enforces rejecting a change.
--
-- The whole file runs in ONE transaction that ends with ROLLBACK, so it can be
-- rerun and the database stays equal to the dump in DUMP/. Every SELECT inside
-- the transaction already sees the changes. Replace ROLLBACK with COMMIT to
-- keep them.
--
-- M2b and M3b fail on purpose. In the mysql client run this file with
-- --force; in Workbench, turn on "Continue SQL script execution on errors".
-- A failed statement is undone on its own; the transaction carries on.
-- ============================================================================

START TRANSACTION;

-- ---------------------------------------------------------------------------
-- M1: INSERT ... SELECT. Copy a shared project into another customer's
-- account (Assignment 1 "Project Sharing": replicate someone else's build).
-- Jordan copies leila.patel143's shared project "Open Battery Charger".
-- ---------------------------------------------------------------------------
-- Before: Jordan has no BOMs
SELECT COUNT(*) AS JordanBOMs FROM BOM WHERE CustomerEmail = 'jordan.li1@example.com';

-- The new (empty) BOM that will receive the copied lines
INSERT INTO BOM (CustomerEmail, BOM_name, Date_created)
VALUES ('jordan.li1@example.com', 'Battery Charger (copied)', CURRENT_DATE);

-- M1: every line of the shared project's BOM becomes a line of the new BOM.
-- The shared BOM is found through its alternate key (CustomerEmail, Title),
-- the way a user picks a project by its title, not by its BOM_name.
INSERT INTO BOMLine (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum, Quantity)
SELECT 'jordan.li1@example.com', 'Battery Charger (copied)',
       bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity
FROM SharedProject sp
     JOIN BOMLine bl ON bl.CustomerEmail = sp.CustomerEmail
                    AND bl.BOM_name = sp.BOM_name
WHERE sp.CustomerEmail = 'leila.patel143@example.com'
  AND sp.Title = 'Open Battery Charger';

-- After: the copy has the same parts and quantities as the original
SELECT bl.BOM_name, bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity
FROM BOMLine bl
WHERE bl.CustomerEmail = 'jordan.li1@example.com'
ORDER BY bl.ManufacturerName, bl.Manufacturer_PartNum;

-- ---------------------------------------------------------------------------
-- M2: UPDATE many tuples, chosen by a subquery on another relation.
-- LCSC raises the price of all its capacitor listings by 10% and records the
-- change time. Category lives in Part, not Listing, so the listings to change
-- are found with a row-value IN subquery over the composite part key.
-- ---------------------------------------------------------------------------
-- Before: how many listings qualify, and their average price
SELECT COUNT(*) AS LCSCCapacitorListings, AVG(UnitPrice) AS AvgPrice
FROM Listing
WHERE DistributorName = 'LCSC'
  AND (ManufacturerName, Manufacturer_PartNum) IN
      (SELECT ManufacturerName, Manufacturer_PartNum FROM Part WHERE Category = 'Capacitor');

-- M2
UPDATE Listing
SET UnitPrice = CAST(UnitPrice * 1.10 AS DECIMAL(10,2)),
    LastUpdated = CURRENT_TIMESTAMP
WHERE DistributorName = 'LCSC'
  AND (ManufacturerName, Manufacturer_PartNum) IN
      (SELECT ManufacturerName, Manufacturer_PartNum FROM Part WHERE Category = 'Capacitor');

-- After: same count, average about 10% higher. CAST rounds each new price to
-- cents explicitly, so MySQL does not warn about truncating extra decimals.
SELECT COUNT(*) AS LCSCCapacitorListings, AVG(UnitPrice) AS AvgPrice
FROM Listing
WHERE DistributorName = 'LCSC'
  AND (ManufacturerName, Manufacturer_PartNum) IN
      (SELECT ManufacturerName, Manufacturer_PartNum FROM Part WHERE Category = 'Capacitor');

-- M2b (fails on purpose): a $1.00 discount on every LCSC listing would make
-- the cheap ones negative. CHECK ck_Listing_price (C1: UnitPrice >= 0)
-- rejects the WHOLE statement (expected: ERROR 3819), so no row changes.
UPDATE Listing
SET UnitPrice = UnitPrice - 1.00
WHERE DistributorName = 'LCSC';

-- Proof that nothing changed: no LCSC listing is negative, the count is intact
SELECT COUNT(*) AS LCSCListings, MIN(UnitPrice) AS MinPrice
FROM Listing
WHERE DistributorName = 'LCSC';

-- ---------------------------------------------------------------------------
-- M3: DELETE a set chosen by a correlated NOT EXISTS subquery, which
-- cascades. Abandoned carts are removed: carts created before 2026-08-01
-- whose owner has never made a BOM (an inactive account).
-- fk_CartLine_ShoppingCart is ON DELETE CASCADE, so their CartLine rows go
-- too. No BOM, BOMLine, BOMSelection or SharedProject row is touched, so the
-- unenforced constraints C3 and C5 cannot be broken by this delete.
-- ---------------------------------------------------------------------------
-- Before
SELECT COUNT(*) AS Carts, (SELECT COUNT(*) FROM CartLine) AS CartLines
FROM ShoppingCart;

-- M3
DELETE FROM ShoppingCart
WHERE Date_created < DATE '2026-08-01'
  AND NOT EXISTS (SELECT *
                  FROM BOM b
                  WHERE b.CustomerEmail = ShoppingCart.CustomerEmail);

-- After: fewer carts, and their lines removed by ON DELETE CASCADE
SELECT COUNT(*) AS Carts, (SELECT COUNT(*) FROM CartLine) AS CartLines
FROM ShoppingCart;

-- No orphaned cart line is left behind
SELECT COUNT(*) AS OrphanCartLines
FROM CartLine c
WHERE NOT EXISTS (SELECT * FROM ShoppingCart s WHERE s.CustomerEmail = c.CustomerEmail);

-- M3b (fails on purpose): delete Eaton's fuses. Many are still offered by a
-- distributor, and fk_Listing_Part is ON DELETE RESTRICT, so the delete is
-- rejected (expected: ERROR 1451) and none of the parts, nor their reviews
-- (which would otherwise cascade), are removed.
DELETE FROM Part
WHERE ManufacturerName = 'Eaton' AND Category = 'Fuse';

SELECT COUNT(*) AS EatonFuses FROM Part WHERE ManufacturerName = 'Eaton' AND Category = 'Fuse';

ROLLBACK;
