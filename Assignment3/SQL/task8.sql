-- task8.sql: Task 6, two views, a query on each, and modification attempts
-- ============================================================================
-- Run after SQL/task3.sql, SQL/task4.sql and SRC/load_data.sql.
-- V1 BOMTotals is NOT updatable (joins, outer join, GROUP BY, aggregates).
-- V2 InStockListing IS updatable (one base table, plain columns, simple
-- WHERE) and uses WITH CHECK OPTION. The updatability of each is explained
-- in explanation.md (section V) with the ISO rules from C&B.
--
-- Several statements fail on purpose. In the mysql client run this file with
-- --force; in Workbench, turn on "Continue SQL script execution on errors".
-- The modifications run in a transaction that ends with ROLLBACK, so the
-- views stay but the data is left as loaded.
-- ============================================================================

-- MySQL-specific: DROP VIEW IF EXISTS (ISO has DROP VIEW <name> with no
-- IF EXISTS). It lets this script be rerun.
DROP VIEW IF EXISTS BOMTotals;
DROP VIEW IF EXISTS InStockListing;

-- ---------------------------------------------------------------------------
-- V1: BOMTotals. One row per BOM with the three derived attributes of BOM
-- from Assignment 2: /NumberOfParts, /UnpricedParts and /TotalCost.
-- Purpose: the BOM list page shows every BOM's size and cost without the
-- application repeating this join; the derived values are never stored.
-- ---------------------------------------------------------------------------
CREATE VIEW BOMTotals (CustomerEmail, BOM_name, NumberOfParts, UnpricedParts, TotalCost) AS
SELECT b.CustomerEmail, b.BOM_name,
       COUNT(bl.Manufacturer_PartNum),
       COUNT(bl.Manufacturer_PartNum) - COUNT(l.UnitPrice),
       COALESCE(SUM(bl.Quantity * l.UnitPrice), 0)
FROM BOM b
     LEFT JOIN BOMLine bl
            ON bl.CustomerEmail = b.CustomerEmail
           AND bl.BOM_name = b.BOM_name
     LEFT JOIN (BOMSelection s
                JOIN Listing l
                  ON l.DistributorName = s.DistributorName
                 AND l.Distributor_PartNum = s.Distributor_PartNum)
            ON s.CustomerEmail = bl.CustomerEmail
           AND s.BOM_name = bl.BOM_name
           AND l.ManufacturerName = bl.ManufacturerName
           AND l.Manufacturer_PartNum = bl.Manufacturer_PartNum
GROUP BY b.CustomerEmail, b.BOM_name;

-- ---------------------------------------------------------------------------
-- V2: InStockListing. The listings that can be bought right now.
-- Purpose: the default for Price Match and the "in stock only" filter.
-- Every column of Listing is kept (including all NOT NULL ones) so a full
-- tuple can be inserted through the view. WITH CHECK OPTION stops an INSERT
-- or UPDATE through the view from producing a row the view cannot see.
-- ---------------------------------------------------------------------------
CREATE VIEW InStockListing AS
SELECT DistributorName, Distributor_PartNum, ManufacturerName, Manufacturer_PartNum,
       Packaging, UnitPrice, StockQuantity, EstShipTime, LastUpdated
FROM Listing
WHERE StockQuantity > 0
WITH CHECK OPTION;

-- ---------------------------------------------------------------------------
-- Queries on the views
-- ---------------------------------------------------------------------------
-- Query on V1: shared projects whose BOM is fully priced (no unpriced line)
-- and has at least 7 parts, most expensive first. A view can be joined like
-- a base table.
SELECT sp.Title, t.CustomerEmail, t.NumberOfParts, t.TotalCost
FROM BOMTotals t
     JOIN SharedProject sp ON sp.CustomerEmail = t.CustomerEmail
                          AND sp.BOM_name = t.BOM_name
WHERE t.UnpricedParts = 0
  AND t.NumberOfParts >= 7
ORDER BY t.TotalCost DESC;

-- Query on V2: every in-stock offer for the generic 1N4148 diode, with the
-- distributor's shipping fee.
SELECT v.ManufacturerName, v.DistributorName, v.Distributor_PartNum, v.Packaging,
       v.UnitPrice, v.StockQuantity, d.ShippingFee
FROM InStockListing v
     JOIN Distributor d ON d.Name = v.DistributorName
WHERE v.Manufacturer_PartNum = '1N4148'
ORDER BY v.UnitPrice;

-- ---------------------------------------------------------------------------
-- Modification attempts
-- ---------------------------------------------------------------------------
START TRANSACTION;

-- V1, attempt 1 (fails): INSERT into the aggregate view.
-- Expected: ERROR 1471, "The target table BOMTotals of the INSERT is not
-- insertable-into". There is no base tuple a row of totals could become.
INSERT INTO BOMTotals (CustomerEmail, BOM_name, NumberOfParts, UnpricedParts, TotalCost)
VALUES ('alex.chen0@example.com', 'New BOM', 0, 0, 0.00);

-- V1, attempt 2 (fails): UPDATE a computed column.
-- Expected: ERROR 1288, "The target table BOMTotals of the UPDATE is not
-- updatable". TotalCost is a SUM over many tuples of two other relations.
UPDATE BOMTotals
SET TotalCost = 0
WHERE CustomerEmail = 'alex.chen0@example.com' AND BOM_name = 'Weather Station v2';

-- V2, attempt 1 (succeeds): insert an in-stock listing through the view.
-- The row goes into the base relation Listing.
INSERT INTO InStockListing (DistributorName, Distributor_PartNum, ManufacturerName,
                            Manufacturer_PartNum, Packaging, UnitPrice, StockQuantity,
                            EstShipTime, LastUpdated)
VALUES ('DigiKey', 'DK-1N4148-ON', 'onsemi', '1N4148', 'Tube', 0.09, 500, 3, CURRENT_TIMESTAMP);

-- The new tuple is visible both in the view and in the base table
SELECT DistributorName, Distributor_PartNum, Packaging, UnitPrice, StockQuantity
FROM InStockListing WHERE Distributor_PartNum = 'DK-1N4148-ON';
SELECT DistributorName, Distributor_PartNum, Packaging, UnitPrice, StockQuantity
FROM Listing WHERE Distributor_PartNum = 'DK-1N4148-ON';

-- V2, attempt 2 (fails): insert an OUT-of-stock listing through the view.
-- Expected: ERROR 1369, "CHECK OPTION failed 'ep_sourcer_test.InStockListing'".
-- Without WITH CHECK OPTION this row would be inserted into Listing and then
-- vanish from the view (a "migrating" row).
INSERT INTO InStockListing (DistributorName, Distributor_PartNum, ManufacturerName,
                            Manufacturer_PartNum, Packaging, UnitPrice, StockQuantity,
                            EstShipTime, LastUpdated)
VALUES ('DigiKey', 'DK-1N4148-OUT', 'onsemi', '1N4148', 'Bulk', 0.08, 0, 3, CURRENT_TIMESTAMP);

-- V2, attempt 3 (fails): an UPDATE through the view that would move the row
-- out of the view (stock sold out). Expected: ERROR 1369 (CHECK OPTION).
UPDATE InStockListing
SET StockQuantity = 0
WHERE DistributorName = 'DigiKey' AND Distributor_PartNum = 'DK-1N4148-ON';

-- V2, attempt 4 (succeeds): an UPDATE that keeps the row inside the view.
UPDATE InStockListing
SET UnitPrice = 0.08, StockQuantity = 450
WHERE DistributorName = 'DigiKey' AND Distributor_PartNum = 'DK-1N4148-ON';

SELECT DistributorName, Distributor_PartNum, UnitPrice, StockQuantity
FROM Listing WHERE Distributor_PartNum LIKE 'DK-1N4148-%';

ROLLBACK;
