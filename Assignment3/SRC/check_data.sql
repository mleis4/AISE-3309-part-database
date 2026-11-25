-- check_data.sql: Task 3, integrity checks on the loaded data
-- Run after SQL/task3.sql and SRC/load_data.sql. Every check returns a single
-- count, and every count must be 0. The FK checks repeat what the DBMS
-- already enforces (a sanity check on the load); the C3, C4 and C5 checks are
-- the only proof of those rules, because no trigger or assertion enforces them.

-- 1. Orphaned foreign keys (anti-joins), one per FK
SELECT 'Listing -> Distributor' AS CheckName, COUNT(*) AS Violations
FROM Listing l LEFT JOIN Distributor d ON d.Name = l.DistributorName
WHERE d.Name IS NULL
UNION ALL
SELECT 'Listing -> Part', COUNT(*)
FROM Listing l LEFT JOIN Part p
       ON p.ManufacturerName = l.ManufacturerName AND p.Manufacturer_PartNum = l.Manufacturer_PartNum
WHERE p.ManufacturerName IS NULL
UNION ALL
SELECT 'ShoppingCart -> Customer', COUNT(*)
FROM ShoppingCart s LEFT JOIN Customer c ON c.Email = s.CustomerEmail
WHERE c.Email IS NULL
UNION ALL
SELECT 'BOM -> Customer', COUNT(*)
FROM BOM b LEFT JOIN Customer c ON c.Email = b.CustomerEmail
WHERE c.Email IS NULL
UNION ALL
SELECT 'SharedProject -> BOM', COUNT(*)
FROM SharedProject s LEFT JOIN BOM b ON b.CustomerEmail = s.CustomerEmail AND b.BOM_name = s.BOM_name
WHERE b.CustomerEmail IS NULL
UNION ALL
SELECT 'PartAlternative -> Part (1)', COUNT(*)
FROM PartAlternative a LEFT JOIN Part p
       ON p.ManufacturerName = a.Part1_ManufacturerName AND p.Manufacturer_PartNum = a.Part1_PartNum
WHERE p.ManufacturerName IS NULL
UNION ALL
SELECT 'PartAlternative -> Part (2)', COUNT(*)
FROM PartAlternative a LEFT JOIN Part p
       ON p.ManufacturerName = a.Part2_ManufacturerName AND p.Manufacturer_PartNum = a.Part2_PartNum
WHERE p.ManufacturerName IS NULL
UNION ALL
SELECT 'BOMLine -> BOM', COUNT(*)
FROM BOMLine l LEFT JOIN BOM b ON b.CustomerEmail = l.CustomerEmail AND b.BOM_name = l.BOM_name
WHERE b.CustomerEmail IS NULL
UNION ALL
SELECT 'BOMLine -> Part', COUNT(*)
FROM BOMLine l LEFT JOIN Part p
       ON p.ManufacturerName = l.ManufacturerName AND p.Manufacturer_PartNum = l.Manufacturer_PartNum
WHERE p.ManufacturerName IS NULL
UNION ALL
SELECT 'BOMSelection -> BOM', COUNT(*)
FROM BOMSelection s LEFT JOIN BOM b ON b.CustomerEmail = s.CustomerEmail AND b.BOM_name = s.BOM_name
WHERE b.CustomerEmail IS NULL
UNION ALL
SELECT 'BOMSelection -> Listing', COUNT(*)
FROM BOMSelection s LEFT JOIN Listing l
       ON l.DistributorName = s.DistributorName AND l.Distributor_PartNum = s.Distributor_PartNum
WHERE l.DistributorName IS NULL
UNION ALL
SELECT 'CartLine -> ShoppingCart', COUNT(*)
FROM CartLine c LEFT JOIN ShoppingCart s ON s.CustomerEmail = c.CustomerEmail
WHERE s.CustomerEmail IS NULL
UNION ALL
SELECT 'CartLine -> Listing', COUNT(*)
FROM CartLine c LEFT JOIN Listing l
       ON l.DistributorName = c.DistributorName AND l.Distributor_PartNum = c.Distributor_PartNum
WHERE l.DistributorName IS NULL
UNION ALL
SELECT 'Review -> Customer', COUNT(*)
FROM Review r LEFT JOIN Customer c ON c.Email = r.CustomerEmail
WHERE c.Email IS NULL
UNION ALL
SELECT 'Review -> Part', COUNT(*)
FROM Review r LEFT JOIN Part p
       ON p.ManufacturerName = r.ManufacturerName AND p.Manufacturer_PartNum = r.Manufacturer_PartNum
WHERE p.ManufacturerName IS NULL
UNION ALL

-- 2. C3a: a selected listing's part must be a line of the same BOM
SELECT 'C3 selection without a matching line', COUNT(*)
FROM BOMSelection s
     JOIN Listing l ON l.DistributorName = s.DistributorName AND l.Distributor_PartNum = s.Distributor_PartNum
WHERE NOT EXISTS (SELECT * FROM BOMLine b
                  WHERE b.CustomerEmail = s.CustomerEmail AND b.BOM_name = s.BOM_name
                    AND b.ManufacturerName = l.ManufacturerName
                    AND b.Manufacturer_PartNum = l.Manufacturer_PartNum)
UNION ALL
-- 3. C3b: at most one selected listing per part per BOM
SELECT 'C3 two selections for one part', COUNT(*)
FROM (SELECT s.CustomerEmail, s.BOM_name, l.ManufacturerName, l.Manufacturer_PartNum
      FROM BOMSelection s
           JOIN Listing l ON l.DistributorName = s.DistributorName AND l.Distributor_PartNum = s.Distributor_PartNum
      GROUP BY s.CustomerEmail, s.BOM_name, l.ManufacturerName, l.Manufacturer_PartNum
      HAVING COUNT(*) > 1) dup
UNION ALL
-- 4. C4: each pair stored once, smaller key first (the CHECK MySQL rejects)
SELECT 'C4 pair out of order or self-pair', COUNT(*)
FROM PartAlternative
WHERE NOT ((Part1_ManufacturerName, Part1_PartNum) < (Part2_ManufacturerName, Part2_PartNum))
UNION ALL
-- 5. C5: a shared BOM has at least one line
SELECT 'C5 shared BOM with no lines', COUNT(*)
FROM SharedProject p
WHERE NOT EXISTS (SELECT * FROM BOMLine b
                  WHERE b.CustomerEmail = p.CustomerEmail AND b.BOM_name = p.BOM_name)
UNION ALL
-- 6. C2 and the SharedProject AK (the UNIQUE constraints already stop these)
SELECT 'C2 duplicate listing per distributor, part, packaging', COUNT(*)
FROM (SELECT DistributorName, ManufacturerName, Manufacturer_PartNum, Packaging
      FROM Listing
      GROUP BY DistributorName, ManufacturerName, Manufacturer_PartNum, Packaging
      HAVING COUNT(*) > 1) dup
UNION ALL
SELECT 'Duplicate (customer, title) shared project', COUNT(*)
FROM (SELECT CustomerEmail, Title FROM SharedProject
      GROUP BY CustomerEmail, Title HAVING COUNT(*) > 1) dup;

-- 7. Size of every relation, for the report
SELECT 'Customer' AS Relation, COUNT(*) AS Tuples FROM Customer
UNION ALL SELECT 'Part', COUNT(*) FROM Part
UNION ALL SELECT 'Distributor', COUNT(*) FROM Distributor
UNION ALL SELECT 'Listing', COUNT(*) FROM Listing
UNION ALL SELECT 'ShoppingCart', COUNT(*) FROM ShoppingCart
UNION ALL SELECT 'BOM', COUNT(*) FROM BOM
UNION ALL SELECT 'SharedProject', COUNT(*) FROM SharedProject
UNION ALL SELECT 'PartAlternative', COUNT(*) FROM PartAlternative
UNION ALL SELECT 'BOMLine', COUNT(*) FROM BOMLine
UNION ALL SELECT 'BOMSelection', COUNT(*) FROM BOMSelection
UNION ALL SELECT 'CartLine', COUNT(*) FROM CartLine
UNION ALL SELECT 'Review', COUNT(*) FROM Review;
