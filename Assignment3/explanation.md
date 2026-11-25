# Assignment 3: explanation of every query, modification and view

> **Draft by an AI assistant (Claude), to be read, checked and rewritten in the group's own words.** The handout's AI policy asks for this file. Every statement below was run against the loaded mock data on MySQL 26.10 (`capture_responses.py`), and the results quoted here come from that run. Before the TA meeting, every member should be able to explain each section without notes.

Statement numbers match the SQL files: **Q1 to Q7** are in `SQL/task6.sql` (Task 4), **M1 to M3** in `SQL/task7.sql` (Task 5) and **V1 and V2** in `SQL/task8.sql` (Task 6).

## How to read a SELECT: the logical execution order

SQL is written as SELECT, FROM, WHERE, ..., but the DBMS evaluates it (logically) in this order. Every section below follows it:

1. **FROM / JOIN**: build the working table from the relations and join conditions.
2. **WHERE**: keep only the tuples that satisfy the condition (a NULL result counts as false).
3. **GROUP BY**: put the remaining tuples into groups with equal grouping values.
4. **HAVING**: keep only the groups that satisfy the condition (it may use aggregates).
5. **SELECT**: compute the output columns (aliases are created here).
6. **ORDER BY**: sort the result. This is the only clause that can use a SELECT alias.

Relational algebra notation (outline topic 5): σ selection, π projection, ⋈ join, ⟕ left outer join, ∪ union, − difference, ρ rename, and γ for grouping with aggregates (γ<sub>grouping attrs; aggregates</sub>). Join conditions are written under ⋈.

A note for every query: **almost every key in this schema is composite**. A part is identified by (ManufacturerName, Manufacturer_PartNum), a BOM by (CustomerEmail, BOM_name) and a listing by (DistributorName, Distributor_PartNum). Joining on only half of a key is the most likely bug: joining Listing to Part on Manufacturer_PartNum alone would match onsemi's 1N4148 with Vishay's 1N4148.

---

## Task 4: SELECT queries

### Q1: Distributors that ship for under $7.00 (simple query)

```sql
SELECT Name, Website, ShippingFee
FROM Distributor
WHERE ShippingFee < 7.00
ORDER BY ShippingFee, Name;
```

1. **What it answers:** which distributors are cheap to order from. Serves the A1 *Filter* function (filter by distributor) and the cart's shipping estimate. This is the one "plain" query the handout allows.
2. **Execution:** FROM reads all 15 Distributor tuples; WHERE keeps the 7 with a fee under 7.00; SELECT projects three attributes; ORDER BY sorts by fee, then by name to break ties (Arrow and Avnet both charge 0.00).
3. **Clauses:** `ShippingFee < 7.00` compares a DECIMAL(10,2) with a numeric literal. No join, no grouping.
3a. **Relational algebra:** π<sub>Name, Website, ShippingFee</sub>(σ<sub>ShippingFee < 7.00</sub>(Distributor))
4. **Constraints:** ck_Distributor_fee (ShippingFee >= 0) guarantees no negative fee appears.
5. **TA questions**
   - *Why is this the "uninteresting" one?* One relation, no subquery, join or grouping.
   - *Why the second sort key?* Without it, the order of tied rows is not defined and could change between runs.

### Q2: Price Match for 100 units of 1N4148 (multi-table join)

```sql
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
```

1. **What it answers:** every offer that can supply 100 units of the generic diode 1N4148 right now, from any of its three manufacturers, with the cost including shipping. Serves A1 *Price Match*. Result: 2 offers (onsemi through Sager at $17.25, Vishay through Avnet at $25.00).
2. **Execution:** FROM joins Part to its Listings (on the full part key), then each listing to its Distributor (on the distributor name). WHERE keeps tuples for part number 1N4148 with stock of at least 100. SELECT computes `CostFor100`. ORDER BY sorts by that alias, cheapest first.
3. **Clauses:** both joins are **inner** joins, because an offer without a listing or a distributor has nothing to show. `100 * UnitPrice + ShippingFee` is a computed column (it is not stored: derived values are never columns in this schema). The filter is on part number only, on purpose: 1N4148 is made by Vishay, onsemi and Nexperia, and comparing all of them is what an engineer wants.
3a. **Relational algebra:** π<sub>ManufacturerName, Name, Distributor_PartNum, Packaging, UnitPrice, StockQuantity, EstShipTime, CostFor100</sub>(σ<sub>Manufacturer_PartNum='1N4148' ∧ StockQuantity≥100</sub>(Part ⋈<sub>part key</sub> Listing ⋈<sub>Distributor.Name = Listing.DistributorName</sub> Distributor)). The computed column is an extended projection.
4. **Constraints:** fk_Listing_Part and fk_Listing_Distributor guarantee every listing has a part and a distributor, so the inner joins lose nothing. ck_Listing_stock keeps stock non-negative.
5. **TA questions**
   - *Why join on both part columns?* The part key is composite. Joining on the number alone would pair each Vishay listing with the onsemi part too.
   - *Why can ORDER BY use CostFor100 but WHERE could not?* WHERE runs before SELECT creates the alias; ORDER BY runs after.
   - *Why only 2 rows?* Most 1N4148 listings have less than 100 in stock (see the V2 query: 6 in-stock offers in total).

### Q3: BOM summary with unpriced lines (outer join + GROUP BY)

```sql
SELECT b.BOM_name,
       COUNT(bl.Manufacturer_PartNum)                      AS NumberOfParts,
       COUNT(bl.Manufacturer_PartNum) - COUNT(l.UnitPrice) AS UnpricedParts,
       COALESCE(SUM(bl.Quantity * l.UnitPrice), 0)         AS TotalCost
FROM BOM b
     LEFT JOIN BOMLine bl
            ON bl.CustomerEmail = b.CustomerEmail AND bl.BOM_name = b.BOM_name
     LEFT JOIN (BOMSelection s
                JOIN Listing l
                  ON l.DistributorName = s.DistributorName
                 AND l.Distributor_PartNum = s.Distributor_PartNum)
            ON s.CustomerEmail = bl.CustomerEmail AND s.BOM_name = bl.BOM_name
           AND l.ManufacturerName = bl.ManufacturerName
           AND l.Manufacturer_PartNum = bl.Manufacturer_PartNum
WHERE b.CustomerEmail = 'alex.chen0@example.com'
GROUP BY b.CustomerEmail, b.BOM_name
ORDER BY TotalCost DESC;
```

1. **What it answers:** for each of one customer's BOMs, the three derived attributes from Assignment 2: /NumberOfParts, /UnpricedParts and /TotalCost. Serves A1 *BOM maker* (totals and the "no supplier chosen" warning). Result: 9 BOMs, including "Empty Draft" with 0 parts.
2. **Execution:**
   - FROM: BOM ⟕ BOMLine keeps every BOM, even one with no lines (its BOMLine columns are NULL). The parenthesised inner join `BOMSelection JOIN Listing` is computed first: each selection with its listing's price and part. That result is then left-joined to each line on **same BOM and same part**, so a line with no selected listing keeps NULL in l.UnitPrice.
   - WHERE keeps one customer's tuples.
   - GROUP BY makes one group per BOM (both key attributes are listed, as ONLY_FULL_GROUP_BY requires).
   - SELECT computes the aggregates per group; ORDER BY sorts by total.
3. **Clauses**
   - `COUNT(column)` counts non-NULL values only, while `COUNT(*)` counts rows. For the empty BOM there is one row (the BOM padded with NULLs), so COUNT(*) would wrongly say 1 part; `COUNT(bl.Manufacturer_PartNum)` says 0.
   - Lines minus priced lines = unpriced lines.
   - `SUM` ignores NULL products (unpriced lines), and returns NULL for a group with no non-NULL value. `COALESCE(..., 0)` turns that NULL into 0 for the empty BOM. COALESCE is the ISO function; MySQL's IFNULL is not used.
   - The match condition on the part (`l.ManufacturerName = bl.ManufacturerName ...`) is what ties a selection to a line: BOMSelection stores the listing, not the part (see the A2 BCNF decision).
3a. **Relational algebra:** γ<sub>CustomerEmail, BOM_name; COUNT(Manufacturer_PartNum)→NumberOfParts, COUNT(UnitPrice)→Priced, SUM(Quantity·UnitPrice)→TotalCost</sub>(σ<sub>CustomerEmail='alex.chen0@example.com'</sub>(BOM ⟕<sub>BOM key</sub> BOMLine ⟕<sub>BOM key ∧ part key</sub> (BOMSelection ⋈<sub>listing key</sub> Listing))), followed by a projection computing UnpricedParts = NumberOfParts − Priced.
4. **Constraints:** C3 (at most one selected listing per part per BOM) is what makes this correct. If a BOM had two selections for one part, that line would be joined twice and counted twice. C3 is not enforced by the DBMS (no triggers), so `check_data.sql` checks it, and it returns 0 violations.
5. **TA questions**
   - *Why LEFT JOIN and not JOIN?* An inner join would drop "Empty Draft" and every unpriced line, so NumberOfParts would be too small and the warning could never fire.
   - *Why the parentheses around BOMSelection JOIN Listing?* If Listing were left-joined separately, a selection whose listing join failed would still appear. The inner join pairs each selection with its price before the outer join.
   - *What does the total mean when UnpricedParts > 0?* It is a partial total (A2 says the app shows it as such).

### Q4: Best-rated parts (GROUP BY + HAVING)

```sql
SELECT p.ManufacturerName, p.Manufacturer_PartNum, p.Name, p.Category,
       COUNT(*) AS Reviews, AVG(r.StarRating) AS AvgStarRating
FROM Part p
     JOIN Review r ON r.ManufacturerName = p.ManufacturerName
                  AND r.Manufacturer_PartNum = p.Manufacturer_PartNum
GROUP BY p.ManufacturerName, p.Manufacturer_PartNum, p.Name, p.Category
HAVING AVG(r.StarRating) >= 4.5 AND COUNT(*) >= 5
ORDER BY AvgStarRating DESC, Reviews DESC, p.ManufacturerName, p.Manufacturer_PartNum;
```

1. **What it answers:** the parts with an average rating (the derived attribute /AvgStarRating) of at least 4.5 from at least 5 reviews. Serves A1 *Part rating*. Result: 16 parts.
2. **Execution:** FROM joins each review to its part (1,500 tuples). There is no WHERE. GROUP BY forms one group per part. HAVING keeps the groups with a high average **and** enough reviews. SELECT outputs the count and average; ORDER BY sorts.
3. **Clauses:** HAVING filters **groups** and may use aggregates; WHERE filters **tuples** and may not. `COUNT(*) >= 5` stops a part with a single 5-star review from topping the list. Name and Category are in GROUP BY so they may appear in SELECT under ONLY_FULL_GROUP_BY; they are functionally dependent on the part key anyway, so adding them does not change the groups.
3a. **Relational algebra:** σ<sub>Avg≥4.5 ∧ Reviews≥5</sub>(γ<sub>ManufacturerName, Manufacturer_PartNum, Name, Category; COUNT(*)→Reviews, AVG(StarRating)→Avg</sub>(Part ⋈<sub>part key</sub> Review))
4. **Constraints:** ck_Review_stars (1 to 5) bounds the average; C6 (the Review PK) means one customer cannot inflate a part with several reviews.
5. **TA questions**
   - *Could the HAVING condition go in WHERE?* No: AVG and COUNT do not exist until the groups are formed.
   - *Why an inner join?* A part with no reviews has no rating, so it cannot qualify anyway.

### Q5: Op-amps sold but out of stock everywhere (EXISTS / NOT EXISTS)

```sql
SELECT p.ManufacturerName, p.Manufacturer_PartNum, p.Name
FROM Part p
WHERE p.Category = 'Op-Amp'
  AND EXISTS (SELECT * FROM Listing l
              WHERE l.ManufacturerName = p.ManufacturerName
                AND l.Manufacturer_PartNum = p.Manufacturer_PartNum)
  AND NOT EXISTS (SELECT * FROM Listing l
                  WHERE l.ManufacturerName = p.ManufacturerName
                    AND l.Manufacturer_PartNum = p.Manufacturer_PartNum
                    AND l.StockQuantity > 0)
ORDER BY p.ManufacturerName, p.Manufacturer_PartNum;
```

1. **What it answers:** op-amps that distributors list, but that none has in stock (so a BOM using them is blocked). Serves A1 *Filter* (minimum stock) and the BOM stock warning. Result: 8 parts.
2. **Execution:** for each Part tuple with category Op-Amp, the two subqueries are evaluated **with that tuple's key** (they are correlated: they refer to `p` from the outer query). The part is kept when the first subquery returns at least one row and the second returns none.
3. **Clauses:** EXISTS is true when its subquery returns any row; `SELECT *` inside it is conventional, since the columns are never used. The EXISTS clause rules out parts nobody sells at all (a different problem: "no supplier"). NOT EXISTS expresses "for all listings of this part, stock = 0", a universal condition SQL has no direct keyword for.
3a. **Relational algebra:** let OP = σ<sub>Category='Op-Amp'</sub>(Part) and K = (ManufacturerName, Manufacturer_PartNum). Then π<sub>K, Name</sub>(OP ⋈ (π<sub>K</sub>(Listing) − π<sub>K</sub>(σ<sub>StockQuantity>0</sub>(Listing)))). The EXISTS becomes the join with listed parts, and the NOT EXISTS becomes the set difference.
4. **Constraints:** ck_Listing_stock (stock >= 0) means "not > 0" is exactly "= 0".
5. **TA questions**
   - *Why not `LEFT JOIN ... WHERE StockQuantity IS NULL`?* That finds parts with no listing. Here the part has listings, all with stock 0, which needs a universal condition, hence NOT EXISTS.
   - *What would NOT IN do differently?* With a row-value NOT IN it works here because the key columns are NOT NULL; with nullable columns NOT IN returns no rows when the subquery contains a NULL, which is why NOT EXISTS is the safer habit.

### Q6: Cheapest in-stock offer for every line of a BOM (scalar subquery)

```sql
SELECT bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity,
       l.DistributorName, l.Distributor_PartNum, l.UnitPrice,
       bl.Quantity * l.UnitPrice AS LineCost
FROM BOMLine bl
     JOIN Listing l ON l.ManufacturerName = bl.ManufacturerName
                   AND l.Manufacturer_PartNum = bl.Manufacturer_PartNum
WHERE bl.CustomerEmail = 'alex.chen0@example.com'
  AND bl.BOM_name = 'Weather Station v2'
  AND l.StockQuantity > 0
  AND l.UnitPrice = (SELECT MIN(l2.UnitPrice) FROM Listing l2
                     WHERE l2.ManufacturerName = bl.ManufacturerName
                       AND l2.Manufacturer_PartNum = bl.Manufacturer_PartNum
                       AND l2.StockQuantity > 0)
ORDER BY LineCost DESC, l.DistributorName;
```

1. **What it answers:** "pick the cheapest supplier for every line" of one BOM. Serves A1 *BOM maker*. Result: 7 lines (one per line of Weather Station v2, since no part had a tie for the cheapest price).
2. **Execution:** FROM pairs each line of every BOM with every listing of the same part; WHERE keeps the chosen BOM's lines and in-stock listings, and for each candidate tuple evaluates the subquery, which returns **one value**: the lowest in-stock price for that line's part. Only the listing whose price equals it survives. SELECT computes the line cost; ORDER BY sorts.
3. **Clauses:** a **scalar subquery** returns a single value (one row, one column), so it can be compared with `=`. It is correlated through `bl`. The alias l2 is needed because the subquery reads Listing a second time, independently of the outer l. The `StockQuantity > 0` must be in **both** places: in the subquery so the minimum is taken over in-stock offers, and outside so an out-of-stock listing with the same price does not sneak in.
3a. **Relational algebra:** let M = γ<sub>ManufacturerName, Manufacturer_PartNum; MIN(UnitPrice)→MinPrice</sub>(σ<sub>StockQuantity>0</sub>(Listing)). Then π<sub>...</sub>(σ<sub>CustomerEmail='alex...' ∧ BOM_name='Weather Station v2' ∧ StockQuantity>0 ∧ UnitPrice=MinPrice</sub>(BOMLine ⋈<sub>part key</sub> Listing ⋈<sub>part key</sub> M)).
4. **Constraints:** a line whose part has no in-stock listing is dropped (inner join); in the app it would appear as unpriced. If two distributors tie on the cheapest price, both rows appear; the ORDER BY makes the order stable.
5. **TA questions**
   - *Is this the same as Q5's feature?* No. Q5 tests existence (true/false); Q6 computes a value (MIN) and compares with it.
   - *Why not ORDER BY UnitPrice with a row limit?* Top-N syntax is not part of the course, and it would give one row in total, not one per line.

### Q7: Alternatives to onsemi 1N4148 (UNION)

```sql
SELECT a.Part2_ManufacturerName AS AltManufacturer, a.Part2_PartNum AS AltPartNum, p.Name,
       'stored as Part2' AS StoredAs
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
```

1. **What it answers:** every part listed as an alternative to onsemi's 1N4148. Serves A1 *Alternative parts*. Result: Nexperia 1N4148 (found in the second SELECT, because "nexperia" sorts before "onsemi") and Vishay 1N4148 (found in the first).
2. **Execution:** each SELECT is evaluated on its own (FROM, WHERE, SELECT), then UNION combines the two results and removes duplicate rows, then ORDER BY sorts the combined result.
3. **Clauses:** constraint C4 stores each symmetric pair **once**, with the smaller part key as Part1. So the part we ask about can be on either side, and each SELECT reads one side. The two SELECTs must be **union-compatible**: same number of columns with compatible types. The output column names come from the first SELECT, which is why ORDER BY uses `AltManufacturer`. The constant column `StoredAs` only shows which side matched, for the report.
3a. **Relational algebra:** ρ<sub>Alt(Man, Num, Name, StoredAs)</sub>(π<sub>Part2_ManufacturerName, Part2_PartNum, Name, 'Part2'</sub>(σ<sub>Part1=('onsemi','1N4148')</sub>(PartAlternative) ⋈<sub>Part2 = part key</sub> Part)) ∪ π<sub>Part1_ManufacturerName, Part1_PartNum, Name, 'Part1'</sub>(σ<sub>Part2=('onsemi','1N4148')</sub>(PartAlternative) ⋈<sub>Part1 = part key</sub> Part)
4. **Constraints:** C4 is not enforced by MySQL (error 3823, see task3.sql), so `check_data.sql` checks the order with the row comparison `(Part1_ManufacturerName, Part1_PartNum) < (Part2_ManufacturerName, Part2_PartNum)`. If a pair were stored twice in both directions, UNION would still return it once.
5. **TA questions**
   - *Why not store both directions and avoid the UNION?* Each fact would be stored twice and could become inconsistent (one direction deleted, the other kept). Storing once is the A2 design.
   - *UNION vs UNION ALL?* UNION removes duplicates (a sort or hash step); UNION ALL keeps them. Duplicates are not possible here, but UNION states the intent.

---

## Task 5: data modification commands

All three run inside `START TRANSACTION ... ROLLBACK` (outline topic 8.1), so the file can be rerun and the database stays equal to the dump. The SELECTs inside the transaction already see the changes. MySQL makes each failed statement undo itself (statement-level atomicity) while the transaction carries on.

There are no triggers, so the DBMS will not stop a change that breaks **C3, C5 or C7**. Each modification was chosen so it cannot: none of them deletes a BOMLine, changes a listing's part or adds a selection.

### M1: Copy a shared project into another customer's account (INSERT ... SELECT)

```sql
INSERT INTO BOM (CustomerEmail, BOM_name, Date_created)
VALUES ('jordan.li1@example.com', 'Battery Charger (copied)', CURRENT_DATE);

INSERT INTO BOMLine (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum, Quantity)
SELECT 'jordan.li1@example.com', 'Battery Charger (copied)',
       bl.ManufacturerName, bl.Manufacturer_PartNum, bl.Quantity
FROM SharedProject sp
     JOIN BOMLine bl ON bl.CustomerEmail = sp.CustomerEmail AND bl.BOM_name = sp.BOM_name
WHERE sp.CustomerEmail = 'leila.patel143@example.com'
  AND sp.Title = 'Open Battery Charger';
```

- **What it does:** A1 *Project Sharing*, "replicate someone else's build". Jordan copies Leila's shared project. Response: `Query OK, 5 rows affected`; the SELECT after it lists the 5 copied lines.
- **How it works:** the first INSERT creates the parent BOM (fk_BOMLine_BOM needs it to exist first). The INSERT ... SELECT evaluates the query and inserts its result: constants for the new owner and BOM name, and the part and quantity from each source line. The shared project is found by its **alternate key** (CustomerEmail, Title), which is how a user picks a project. Title alone is not unique (five customers share a project called "Open Battery Charger").
- **Constraints:** the BOMLine PK prevents a part from being copied twice into the same BOM. C3 is safe: no selections are copied, so all copied lines start unpriced. C5 is unaffected because the copy is not shared.
- **TA questions:** *Why not copy the BOMSelections too?* The copier may want different suppliers, and copying them would have to respect C3. *What if the BOM name already existed?* The first INSERT would fail with a duplicate-key error on pk_BOM.

### M2: LCSC raises its capacitor prices by 10% (UPDATE many tuples with a subquery)

```sql
UPDATE Listing
SET UnitPrice = CAST(UnitPrice * 1.10 AS DECIMAL(10,2)),
    LastUpdated = CURRENT_TIMESTAMP
WHERE DistributorName = 'LCSC'
  AND (ManufacturerName, Manufacturer_PartNum) IN
      (SELECT ManufacturerName, Manufacturer_PartNum FROM Part WHERE Category = 'Capacitor');
```

- **What it does:** a distributor price change, which is how listing data changes over time. Response: `Rows matched: 129  Changed: 129`. The average price of those 129 listings goes from 0.4794 to 0.5281 (+10.2%; the extra 0.2% comes from rounding each new price to the cent).
- **How it works:** Category is an attribute of Part, not Listing, so the listings to change are chosen with a **row-value IN subquery** over the composite part key: the subquery returns the keys of all capacitors, and a listing qualifies when its (ManufacturerName, Manufacturer_PartNum) pair is in that set. SET computes each new value from the tuple's old one. `CAST(... AS DECIMAL(10,2))` rounds to cents explicitly; without it MySQL silently rounds and reports a "data truncated" warning per row. LastUpdated records when the price changed, since A2 shows the age of each price.
- **M2b, the CHECK constraint (fails on purpose):** `UPDATE Listing SET UnitPrice = UnitPrice - 1.00 WHERE DistributorName = 'LCSC'` would make cheap listings negative. Response: `ERROR 3819: Check constraint 'ck_Listing_price' is violated.` The **whole** statement is rejected, not only the bad rows: the SELECT after it still shows 489 LCSC listings with a minimum price of 0.01.
- **Constraints:** C7 is safe because the part columns are not updated. ON UPDATE CASCADE does not fire, because no key attribute changes.
- **TA questions:** *Why not join Listing and Part in the UPDATE?* A multi-table UPDATE is MySQL syntax, not ISO; the subquery is the standard form. *Why did M2b change nothing at all?* SQL statements are atomic.

### M3: Delete abandoned carts (DELETE with a correlated NOT EXISTS, cascading)

```sql
DELETE FROM ShoppingCart
WHERE Date_created < DATE '2026-08-01'
  AND NOT EXISTS (SELECT * FROM BOM b
                  WHERE b.CustomerEmail = ShoppingCart.CustomerEmail);
```

- **What it does:** removes carts created before 1 August 2026 whose owner has never made a BOM (an inactive account). Response: `Query OK, 18 rows affected`. Carts go from 200 to 182 and cart lines from 1,200 to 1,110.
- **How it works:** for each cart, the correlated subquery looks for any BOM of the same customer (`ShoppingCart.CustomerEmail` refers to the tuple being tested). The cart is deleted when the date test is true and no BOM exists. `DATE '2026-08-01'` is an ISO date literal.
- **Cascade:** fk_CartLine_ShoppingCart is `ON DELETE CASCADE`, so the DBMS also deletes the 90 CartLine tuples of those carts. The response counts only the 18 carts; the follow-up SELECT shows 0 orphaned cart lines.
- **M3b, ON DELETE RESTRICT (fails on purpose):** `DELETE FROM Part WHERE ManufacturerName = 'Eaton' AND Category = 'Fuse'` is rejected with `ERROR 1451: Cannot delete or update a parent row: a foreign key constraint fails (... fk_Listing_Part ...)`, because distributors still list those fuses and fk_Listing_Part is RESTRICT. All 23 fuses remain, and so do their reviews, which would otherwise have been removed by fk_Review_Part's CASCADE.
- **Constraints:** no BOM, BOMLine, BOMSelection or SharedProject is touched, so C3 and C5 cannot break.
- **TA questions:** *What would happen to a customer's BOMs if the customer were deleted?* fk_BOM_Customer cascades to BOM, and from BOM to BOMLine, BOMSelection and SharedProject. *Why does the response say 18 and not 108 rows?* Rows deleted by a cascade are not counted.

---

## Task 6: views and updatability

### The ISO rules (Connolly & Begg, ch. 7) used below

A view is updatable only if:
1. DISTINCT is not specified;
2. every element in the SELECT list is a column name (no expressions, constants or aggregates), and no column appears more than once;
3. the FROM clause names exactly one table (no joins, UNION, INTERSECT or EXCEPT); if that table is a view, it must be updatable too;
4. the WHERE clause has no nested SELECT that refers to the table in FROM;
5. there is no GROUP BY or HAVING.

In addition, an INSERT through a view fails if the view leaves out a NOT NULL column with no default, and **WITH CHECK OPTION** rejects an INSERT or UPDATE through the view that would produce a row the view's WHERE clause does not select.

### V1: BOMTotals (not updatable)

```sql
CREATE VIEW BOMTotals (CustomerEmail, BOM_name, NumberOfParts, UnpricedParts, TotalCost) AS
SELECT b.CustomerEmail, b.BOM_name,
       COUNT(bl.Manufacturer_PartNum),
       COUNT(bl.Manufacturer_PartNum) - COUNT(l.UnitPrice),
       COALESCE(SUM(bl.Quantity * l.UnitPrice), 0)
FROM BOM b LEFT JOIN BOMLine bl ON ... LEFT JOIN (BOMSelection s JOIN Listing l ON ...) ON ...
GROUP BY b.CustomerEmail, b.BOM_name;
```

- **Purpose:** the derived attributes of BOM from Assignment 2, computed once for all 802 BOMs, so the app's BOM page does not repeat the Q3 join. The derived values are never stored (A2 decision), so the view stays correct after any change to lines, selections or prices. The column list after the view name names the computed columns.
- **Logic:** the same as Q3 without the customer filter (see Q3 for the outer-join and COUNT reasoning).
- **Relational algebra:** BOMTotals = π<sub>CustomerEmail, BOM_name, NumberOfParts, NumberOfParts−Priced, TotalCost</sub>(γ<sub>CustomerEmail, BOM_name; COUNT(Manufacturer_PartNum)→NumberOfParts, COUNT(UnitPrice)→Priced, SUM(Quantity·UnitPrice)→TotalCost</sub>(BOM ⟕ BOMLine ⟕ (BOMSelection ⋈ Listing)))
- **Query on the view:** shared projects whose BOM is fully priced (UnpricedParts = 0) and has at least 7 parts, joined with SharedProject for the title. Result: 4 projects, from $420.36 down to $15.42. A view is used in FROM like a base relation; the DBMS merges or materialises the view definition when the query runs.
- **Modification attempts and responses:**
  - `INSERT INTO BOMTotals ... VALUES ('alex.chen0@example.com', 'New BOM', 0, 0, 0.00)` → `ERROR 1471: The target table BOMTotals of the INSERT is not insertable-into`
  - `UPDATE BOMTotals SET TotalCost = 0 WHERE ...` → `ERROR 1288: The target table BOMTotals of the UPDATE is not updatable`
- **Why it is not updatable (ISO rules):**
  - **Rule 2 is broken:** NumberOfParts, UnpricedParts and TotalCost are aggregates and expressions, not column names. Setting TotalCost = 0 would mean changing an unknown mix of quantities and prices in two other relations.
  - **Rule 3 is broken:** FROM joins four relations (BOM, BOMLine, BOMSelection, Listing), two of them through outer joins.
  - **Rule 5 is broken:** it has GROUP BY. Each view row stands for a whole group of base tuples, so there is no single base tuple an inserted row could become.
  - Rules 1 and 4 hold (no DISTINCT, no subquery in WHERE), but one broken rule is enough.
  - **MySQL agrees:** MySQL can update some join views (when one base table is changed and the view has no aggregates), but any view with GROUP BY or aggregate functions is neither updatable nor insertable, which is what errors 1288 and 1471 say.

### V2: InStockListing (updatable, WITH CHECK OPTION)

```sql
CREATE VIEW InStockListing AS
SELECT DistributorName, Distributor_PartNum, ManufacturerName, Manufacturer_PartNum,
       Packaging, UnitPrice, StockQuantity, EstShipTime, LastUpdated
FROM Listing
WHERE StockQuantity > 0
WITH CHECK OPTION;
```

- **Purpose:** the listings that can be bought now; the default data source for *Price Match* and the "in stock only" filter. It also lets an "add an in-stock offer" screen insert through the view while being unable to create out-of-stock rows.
- **Relational algebra:** InStockListing = σ<sub>StockQuantity>0</sub>(Listing) (all attributes kept, so the projection is the identity).
- **Query on the view:** every in-stock offer for 1N4148, joined with Distributor for the shipping fee. Result: 6 offers, from $0.09 to $0.25.
- **Modification attempts and responses:**
  1. INSERT of a DigiKey listing for onsemi 1N4148 with StockQuantity 500 → `Query OK, 1 row affected`. The follow-up SELECTs show the tuple both in the view **and in the base relation Listing**: an insert through a view is an insert into its base table.
  2. INSERT of a listing with StockQuantity 0 → `ERROR 1369: CHECK OPTION failed 'ep_sourcer_test.instocklisting'`.
  3. UPDATE setting that listing's StockQuantity to 0 → `ERROR 1369` again.
  4. UPDATE setting its price to 0.08 and stock to 450 → `Rows matched: 1  Changed: 1` (the row stays inside the view).
- **Why it is updatable (ISO rules):**
  - Rule 1: no DISTINCT. Rule 2: every SELECT element is a plain column of Listing, each once. Rule 3: FROM names one base table. Rule 4: the WHERE clause (`StockQuantity > 0`) has no subquery. Rule 5: no GROUP BY or HAVING. All five hold.
  - Every view row therefore corresponds to exactly one Listing tuple, so the DBMS knows which base tuple to update, delete or insert.
  - **INSERT works** because the view keeps every NOT NULL column of Listing; if it left out, say, EstShipTime, an INSERT through it would fail because that column has no default.
  - **WITH CHECK OPTION** is why attempts 2 and 3 fail: the resulting rows would have StockQuantity = 0, which the view's WHERE clause does not select. Without it, attempt 2 would succeed and the new row would immediately "disappear" from the view (a migrating row), and attempt 3 would move an existing row out of the view.
  - The base-table constraints still apply through the view: the INSERT is checked against pk_Listing, ak_Listing_1 (C2), both FKs and the CHECKs, exactly as a direct INSERT into Listing would be.

### Why the pair contrasts well

| | BOMTotals | InStockListing |
|---|---|---|
| Base relations | 4 (with outer joins) | 1 |
| SELECT list | 2 columns + 3 aggregates/expressions | 9 plain columns |
| GROUP BY | yes | no |
| ISO updatable | no (rules 2, 3, 5) | yes (all 5 rules hold) |
| MySQL response to INSERT | ERROR 1471 | success, or ERROR 1369 when the row leaves the view |

---

## Likely TA questions across the whole assignment

- **Why no triggers?** The handout only asks us to consider them. C3, C4, C5 and C7 are written in their ISO form (CREATE ASSERTION or CHECK) at the end of task3.sql, enforced by the generator for the loaded data, checked by `check_data.sql`, and will be enforced by the A4 application.
- **Why is the C4 CHECK only a comment?** MySQL error 3823: a CHECK may not use a column that has an FK referential action, and all four PartAlternative columns have ON DELETE/ON UPDATE CASCADE.
- **Why does task4.sql run before the bulk load?** So each `SELECT * FROM BOMLine` fits on a screenshot; its keys never occur in the generated data, so the load still works afterwards.
- **Why do task7 and task8 end in ROLLBACK?** So the scripts can be rerun and the database stays equal to the submitted dump. The SELECTs inside the transaction show every effect.
