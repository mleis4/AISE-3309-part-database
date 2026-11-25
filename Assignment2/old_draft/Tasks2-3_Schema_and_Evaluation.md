# Tasks 2 and 3: Relational Schema and Schema Evaluation

Engineering Part Sourcer, Group 6. Draft for group review. Names match the ERD in `diagrams/erd_001_class_engineering_part_sourcer.png`.

Notation: `R(A, B, C)`. **PK** attributes are in bold. FK = foreign key, AK = alternate key, `/x` = derived (not stored).

---

## Task 2: ERD to relational schema

### 2.1 Mapping steps applied

| Step | ERD construct | Result |
|---|---|---|
| 1. Strong entities | Customer, Part, Distributor, SharedProject | One relation each. Composite attributes are flattened (BillingAddress to 6 columns, Dimensions to 3). |
| 2. Weak entities | BOM, ShoppingCart, Listing | PK = owner's PK + partial key. Owner's PK is also an FK. |
| 3. 1:1 | Customer owns ShoppingCart | Identifying relationship, so Cart's PK is the FK `CustomerEmail`. |
| 4. 1:N | Customer shares SharedProject | FK `CustomerEmail` in SharedProject (NOT NULL). |
| 4. 1:N (identifying) | Customer creates BOM, Distributor publishes Listing, Listing offers Part | FK in the N side. |
| 5. M:N | contains, holds, reviews, uses, alternative to | New relation per M:N, with relationship attributes. |
| 6. Multivalued | A1's "Customer reviews", "Parts", "All parts" | Removed from entities. Represented by Review, CartLine/BOMLine, and Listing. |
| 7. Specialization | None in this ERD | n/a |
| Derived | /NumberOfParts, /TotalCost, /Subtotal, /ShippingPrice, /TotalPrice, /AvgStarRating | Not stored. Computed by queries or views. |

### 2.2 Relations

**Customer**(**Email**, Username, Password, FirstName, LastName, HouseAddress, UnitNum, PostCode, City, Province, Country)
- PK: Email. AK: Username. FK: none. Derived: none.

**Part**(**Manufacturer_PartNum**, Name, Description, Category, Length, Width, Height, Datasheet_link)
- PK: Manufacturer_PartNum. AK: none. FK: none. Derived: none.

**Distributor**(**Name**, Website)
- PK: Name. AK: Website. FK: none. Derived: /AvgStarRating = AVG(Review.StarRating).

**SharedProject**(**Title**, Description, Date_shared, CustomerEmail)
- PK: Title. FK: CustomerEmail → Customer(Email), NOT NULL. AK: none.

**BOM**(**CustomerEmail**, **BOM_name**, Date_created)
- PK: (CustomerEmail, BOM_name). FK: CustomerEmail → Customer(Email).
- Derived: /NumberOfParts = COUNT(BOMLine), /TotalCost = SUM(BOMLine.Quantity × Listing.UnitPrice) for the chosen listings.

**ShoppingCart**(**CustomerEmail**, Date_Added)
- PK: CustomerEmail. FK: CustomerEmail → Customer(Email).
- Derived: /Subtotal, /ShippingPrice, /TotalPrice (computed from CartLine and Listing).

**Listing**(**DistributorName**, **Distributor_PartNum**, Manufacturer_PartNum, UnitPrice, StockQuantity, EstShipTime, LastUpdated)
- PK: (DistributorName, Distributor_PartNum).
- AK: (DistributorName, Manufacturer_PartNum). This assumes one listing per distributor per part, as A1 says ("one distributor's offer for one part").
- FK: DistributorName → Distributor(Name). Manufacturer_PartNum → Part(Manufacturer_PartNum), NOT NULL.

**PartAlternative**(**Part1_PartNum**, **Part2_PartNum**)
- PK: both attributes. FK: each → Part(Manufacturer_PartNum). CHECK Part1_PartNum <> Part2_PartNum.
- The relationship is symmetric. Store each pair once (e.g. Part1_PartNum < Part2_PartNum).

**BOMLine**(**CustomerEmail**, **BOM_name**, **Manufacturer_PartNum**, Quantity)
- PK: all three key attributes. FK: (CustomerEmail, BOM_name) → BOM. Manufacturer_PartNum → Part.

**CartLine**(**CustomerEmail**, **DistributorName**, **Distributor_PartNum**, Quantity)
- PK: all three key attributes. FK: CustomerEmail → ShoppingCart(CustomerEmail). (DistributorName, Distributor_PartNum) → Listing.

**Review**(**CustomerEmail**, **DistributorName**, ReviewText, StarRating)
- PK: (CustomerEmail, DistributorName). FK: CustomerEmail → Customer. DistributorName → Distributor. CHECK StarRating BETWEEN 1 AND 5.

**ProjectPart**(**Title**, **Manufacturer_PartNum**, Quantity)
- PK: (Title, Manufacturer_PartNum). FK: Title → SharedProject. Manufacturer_PartNum → Part.

Referential integrity diagram: `diagrams/schema_001_foreign_keys.png`. Every FK points to a PK or full composite PK.

### 2.3 Open points for the group

1. **BOM line to listing.** A1's BOM maker says users "select supplier listings", but the ERD links BOM to Part. If a BOM must remember the chosen distributor, add nullable `DistributorName` and `Distributor_PartNum` to BOMLine as an FK to Listing. Then /TotalCost is computable. Without it, TotalCost has to use the cheapest listing.
2. **Review after purchase.** A1 says reviews follow a purchase, but there is no Order entity. The schema cannot enforce it, so the rule goes in the application (A4).
3. **BOM_name uniqueness.** BOM names are unique only per customer. This is a design choice from replacing the surrogate BOM ID.

---

## Task 3: Schema evaluation

FD diagrams for every relation: `diagrams/fd_001_dependency_diagrams.png`. Determinant boxes are keys.

### 3.3.1 Flaws and 3NF

**Flaws found in the A1 draft and fixed in this schema**

| Flaw | Problem | Fix |
|---|---|---|
| `Part.Distributor` | Redundant with Listing, and wrong for parts with many distributors | Removed |
| `Distributor.All parts`, `ShoppingCart.Parts`, `Customer reviews` | Multivalued, so not 1NF | Separate relations (Listing, CartLine, Review) |
| Stored `5-star rating`, `Subtotal`, `Total price`, `Shipping price` | Update anomalies when the source data changes | Derived, not stored |
| Surrogate IDs (BOM ID, Cart_ID, Listing_ID, DistributorID) | Not real-world identifiers | Natural or composite keys |

**1NF.** Every attribute is atomic, with no repeating groups. Composite attributes (address, dimensions) are split into columns.

**2NF.** A partial dependency needs a composite key with a non-key attribute depending on part of it. Composite-key relations:

| Relation | Key | Check |
|---|---|---|
| BOM | (CustomerEmail, BOM_name) | Date_created is the date of the named BOM, which depends on both. No partial dependency. |
| Listing | (DistributorName, Distributor_PartNum) | All attributes describe one distributor's offer for one part. No partial dependency. |
| BOMLine, CartLine, ProjectPart, Review | all | Only Quantity, or ReviewText and StarRating, which depend on the whole key. |
| PartAlternative | both | No non-key attributes. |

Single-attribute-key relations (Customer, Part, Distributor, SharedProject, ShoppingCart) cannot have partial dependencies.

**3NF.** A transitive dependency needs a non-key attribute determining another non-key attribute.

| Relation | Non-key to non-key FDs | Verdict |
|---|---|---|
| Customer | None assumed (see below) | 3NF |
| Part | None. Category does not determine Name, dimensions or datasheet. | 3NF |
| Distributor | Website is an AK, so it is a candidate key. | 3NF |
| SharedProject | None | 3NF |
| BOM, ShoppingCart | None | 3NF |
| Listing | None. UnitPrice, StockQuantity, EstShipTime and LastUpdated are independent. | 3NF |
| BOMLine, CartLine, Review, ProjectPart, PartAlternative | None | 3NF |

**Customer address caveat.** In the real world `PostCode → City, Province` would be a transitive dependency. We do not treat it as an FD. A postal code format is not unique across countries, and one code can span several municipalities. A1 also models the address as one composite attribute. If the group or TA wants strict normalization, split into `Customer(…, PostCode)` and `PostalArea(PostCode, Country, City, Province)`. The risk is more joins for little benefit.

**Conclusion:** all 11 relations are in at least 3NF.

### 3.3.2 Combining relations

| Candidate | Can merge without redundancy? | Decision |
|---|---|---|
| Customer + ShoppingCart (1:1) | Yes. Date_Added would be a nullable column on Customer. | **Keep separate.** The cart has one stored attribute and is updated on every add or remove, while Customer holds credentials and billing data read at sign-in. Separating them avoids sparse NULLs for customers without a cart and keeps CartLine's FK pointing at a cart. **If the group wants fewer tables, this is the only safe merge.** |
| Customer + SharedProject, Customer + BOM | No. 1:N, so merging repeats customer data per row. | Keep separate. |
| Distributor + Listing, Listing + Part | No. 1:N, so the "one" side's attributes would repeat. | Keep separate. |
| BOM + BOMLine, ShoppingCart + CartLine | No. M:N link tables. | Keep separate. |

This is the only merge opportunity. The remaining relations come from 1:N or M:N relationships, where merging would create redundancy.

### 3.3.3 BCNF

BCNF requires every determinant to be a superkey.

| Relation | Determinants | Superkey? |
|---|---|---|
| Customer | Email, Username | Yes (PK, AK) |
| Part | Manufacturer_PartNum | Yes |
| Distributor | Name, Website | Yes (PK, AK) |
| SharedProject | Title | Yes |
| BOM | (CustomerEmail, BOM_name) | Yes |
| ShoppingCart | CustomerEmail | Yes |
| Listing | (DistributorName, Distributor_PartNum); (DistributorName, Manufacturer_PartNum) | Yes (PK, AK). The AK is the one relevant check, and it holds under the one-listing-per-distributor-per-part rule. |
| BOMLine, CartLine, Review, ProjectPart, PartAlternative | Full PK | Yes |

**All relations are in BCNF. No decomposition is needed.** Overlapping candidate keys appear only in Listing, and both are superkeys.

If the group drops the one-listing-per-part rule, the AK FD disappears and Listing stays in BCNF with its PK as the only determinant.

### Query justification

| Anticipated query | Supporting design |
|---|---|
| Part search by name, number or keyword | Part is indexed on Manufacturer_PartNum, Name and Category. It has no distributor columns, so one Part row serves all searches. |
| Price match for N units | Listing joined to Part on Manufacturer_PartNum, giving UnitPrice × N, StockQuantity and EstShipTime sorted by price. No data repeated per distributor. |
| Filters (category, dimensions, distributor, price range, minimum stock) | Part attributes (Category, Length/Width/Height) plus Listing attributes (DistributorName, UnitPrice, StockQuantity), all via one join. |
| BOM total, line costs, stock warnings | BOMLine joined to Listing. Totals are derived on read, so they cannot go stale. |
| Cart subtotals grouped by distributor | CartLine joined to Listing and grouped by DistributorName. |
| Distributor star rating | AVG over Review, not stored. |
| Find shared projects and order the parts | SharedProject joined to ProjectPart, then to Part and Listing. |
| Alternative parts | PartAlternative, queried in both directions with a UNION. |

Splitting these into separate relations removes update anomalies. Price or stock changes touch one Listing row. The extra joins are on keys, which are indexed, and A4 can add views for the common joins.
