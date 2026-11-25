-- task6.sql: Task 4, seven SELECT queries
-- ============================================================================
-- Run after SQL/task3.sql, SQL/task4.sql and SRC/load_data.sql.
-- Each query answers a question the Assignment 1 functions ask, and each uses
-- a different main SQL feature. No row-limit syntax is used: the WHERE,
-- GROUP BY and HAVING conditions keep every result short.
-- Q numbers match explanation.md.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Q1 (simple SELECT-FROM-WHERE). Distributors that ship for under $7.00,
-- cheapest first. Serves: Filter by distributor / Cart shipping estimate.
-- ---------------------------------------------------------------------------
SELECT Name, Website, ShippingFee
FROM Distributor
WHERE ShippingFee < 7.00
ORDER BY ShippingFee, Name;

-- ---------------------------------------------------------------------------
-- Q2 (multi-table inner join over a composite key, computed column).
-- Price Match: every offer for 100 units of the generic part 1N4148, from any
-- manufacturer, with enough stock, and the subtotal including shipping.
-- Serves: Price Match.
-- ---------------------------------------------------------------------------
SELECT p.ManufacturerName, d.Name AS Distributor, l.Distributor_PartNum, l.Packaging,
       l.UnitPrice, l.StockQuantity, l.EstShipTime,
       100 * l.UnitPrice + d.ShippingFee AS CostFor100
FROM Part p
     JOIN Listing l ON l.ManufacturerName = p.ManufacturerName
                   AND l.Manufacturer_PartNum = p.Manufacturer_PartNum
     JOIN Distributor d ON d.Name = l.DistributorName
WHERE p.Manufacturer_PartNum = '1N4148'
  AND l.StockQuantity >= 100
ORDER BY CostFor100;

-- ---------------------------------------------------------------------------
-- Q3 (LEFT OUTER JOIN with GROUP BY and aggregates).
-- BOM summary for one customer: the derived attributes /NumberOfParts,
-- /UnpricedParts and /TotalCost of every BOM, including a BOM with no lines.
-- Serves: BOM maker (line costs, totals, unpriced-part warning).
-- ---------------------------------------------------------------------------
SELECT b.BOM_name,
       COUNT(bl.Manufacturer_PartNum)                    AS NumberOfParts,
       COUNT(bl.Manufacturer_PartNum) - COUNT(l.UnitPrice) AS UnpricedParts,
       COALESCE(SUM(bl.Quantity * l.UnitPrice), 0)       AS TotalCost
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
WHERE b.CustomerEmail = 'alex.chen0@example.com'
GROUP BY b.CustomerEmail, b.BOM_name
ORDER BY TotalCost DESC;

-- ---------------------------------------------------------------------------
-- Q4 (GROUP BY with HAVING on two aggregates).
-- Best-rated parts: an average rating (/AvgStarRating) of at least 4.5 from
-- at least 5 reviews. Serves: Part rating.
-- ---------------------------------------------------------------------------
SELECT p.ManufacturerName, p.Manufacturer_PartNum, p.Name, p.Category,
       COUNT(*) AS Reviews,
       AVG(r.StarRating) AS AvgStarRating
FROM Part p
     JOIN Review r ON r.ManufacturerName = p.ManufacturerName
                  AND r.Manufacturer_PartNum = p.Manufacturer_PartNum
GROUP BY p.ManufacturerName, p.Manufacturer_PartNum, p.Name, p.Category
HAVING AVG(r.StarRating) >= 4.5 AND COUNT(*) >= 5
ORDER BY AvgStarRating DESC, Reviews DESC, p.ManufacturerName, p.Manufacturer_PartNum;

-- ---------------------------------------------------------------------------
-- Q5 (correlated EXISTS and NOT EXISTS).
-- Op-amps that ARE sold by at least one distributor, but that NO distributor
-- currently has in stock. Serves: Filter (minimum stock) / BOM stock warning.
-- ---------------------------------------------------------------------------
SELECT p.ManufacturerName, p.Manufacturer_PartNum, p.Name
FROM Part p
WHERE p.Category = 'Op-Amp'
  AND EXISTS (SELECT *
              FROM Listing l
              WHERE l.ManufacturerName = p.ManufacturerName
                AND l.Manufacturer_PartNum = p.Manufacturer_PartNum)
  AND NOT EXISTS (SELECT *
                  FROM Listing l
                  WHERE l.ManufacturerName = p.ManufacturerName
                    AND l.Manufacturer_PartNum = p.Manufacturer_PartNum
                    AND l.StockQuantity > 0)
ORDER BY p.ManufacturerName, p.Manufacturer_PartNum;

-- ---------------------------------------------------------------------------
-- Q6 (scalar subquery with an aggregate, compared in WHERE).
-- For each line of one BOM, the cheapest offer that is in stock: a listing
-- qualifies only if its price equals the minimum in-stock price for that part.
-- Serves: BOM maker ("pick cheapest supplier for every line").
-- ---------------------------------------------------------------------------
SELECT bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity,
       l.DistributorName, l.Distributor_PartNum, l.UnitPrice,
       bl.Quantity * l.UnitPrice AS LineCost
FROM BOMLine bl
     JOIN Listing l ON l.ManufacturerName = bl.ManufacturerName
                   AND l.Manufacturer_PartNum = bl.Manufacturer_PartNum
WHERE bl.CustomerEmail = 'alex.chen0@example.com'
  AND bl.BOM_name = 'Weather Station v2'
  AND l.StockQuantity > 0
  AND l.UnitPrice = (SELECT MIN(l2.UnitPrice)
                     FROM Listing l2
                     WHERE l2.ManufacturerName = bl.ManufacturerName
                       AND l2.Manufacturer_PartNum = bl.Manufacturer_PartNum
                       AND l2.StockQuantity > 0)
ORDER BY LineCost DESC, l.DistributorName;

-- ---------------------------------------------------------------------------
-- Q7 (set operation: UNION).
-- All alternatives to onsemi's 1N4148. Each pair is stored only once, with
-- the smaller part key first (constraint C4), so the part can be on either
-- side of a pair: the first SELECT reads pairs where it is Part1, the second
-- where it is Part2, and UNION merges them and removes duplicates.
-- Serves: Alternative parts.
-- ---------------------------------------------------------------------------
SELECT a.Part2_ManufacturerName AS AltManufacturer, a.Part2_PartNum AS AltPartNum, p.Name, 'stored as Part2' AS StoredAs
FROM PartAlternative a
     JOIN Part p ON p.ManufacturerName = a.Part2_ManufacturerName
                AND p.Manufacturer_PartNum = a.Part2_PartNum
WHERE a.Part1_ManufacturerName = 'onsemi' AND a.Part1_PartNum = '1N4148'
UNION
SELECT a.Part1_ManufacturerName, a.Part1_PartNum, p.Name, 'stored as Part1'
FROM PartAlternative a
     JOIN Part p ON p.ManufacturerName = a.Part1_ManufacturerName
                AND p.Manufacturer_PartNum = a.Part1_PartNum
WHERE a.Part2_ManufacturerName = 'onsemi' AND a.Part2_PartNum = '1N4148'
ORDER BY AltManufacturer;
