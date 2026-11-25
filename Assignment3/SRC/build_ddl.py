# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         build_ddl.py
# Description:     Writes SQL/task3.sql (Assignment 3, Task 1: CREATE TABLE
#                  statements) from RELS in ../../Assignment2/build_report.py,
#                  so the table names, keys and foreign keys can never drift
#                  from the Assignment 2 schema. Only the data types, NOT NULL
#                  choices, CHECKs and indexes are added here, because
#                  Assignment 2 did not define them.
#
# Run:             python SRC/build_ddl.py      (from Assignment3/)
#                  (stdlib only; imports build_report.py but never runs it)
# ------------------------------------------------------------------------------
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
A3_DIR = os.path.dirname(SCRIPT_DIR)
A2_DIR = os.path.join(os.path.dirname(A3_DIR), "Assignment2")
sys.path.insert(0, A2_DIR)
import build_report as report  # noqa: E402  (import after the path is set)

OUT_PATH = os.path.join(A3_DIR, "SQL", "task3.sql")

# ------------------------------------------------------------------------------
# Data types. Assignment 2 never defined them.
# GROUP TO CONFIRM: these are proposed defaults, not decisions yet.
# Several columns share one domain (emails, part numbers, money). In ISO SQL
# each domain would be defined once with CREATE DOMAIN (C&B ch. 7); MySQL does
# not support CREATE DOMAIN, so the type is repeated on every column instead.
# ------------------------------------------------------------------------------
EMAIL = "VARCHAR(254)"       # domain EmailAddress (254 = longest legal address)
MANUFACTURER = "VARCHAR(60)"  # domain ManufacturerName
PART_NUM = "VARCHAR(60)"      # domain PartNumber (manufacturer and distributor SKUs)
DISTRIBUTOR = "VARCHAR(60)"   # domain DistributorName
BOM_NAME = "VARCHAR(100)"     # domain BOMName
MONEY = "DECIMAL(10,2)"       # domain Money (dollars and cents)
QUANTITY = "INTEGER"          # domain Quantity (> 0, see CHECKS)
DIMENSION = "DECIMAL(8,2)"    # millimetres

TYPES = {
    # Customer
    "Email": EMAIL, "Username": "VARCHAR(30)", "Password": "VARCHAR(255)",
    "FirstName": "VARCHAR(50)", "LastName": "VARCHAR(50)", "HouseAddress": "VARCHAR(100)",
    "UnitNum": "VARCHAR(10)", "City": "VARCHAR(50)", "Province": "VARCHAR(50)",
    "Country": "VARCHAR(56)", "PostCode": "VARCHAR(10)",
    # Part
    "ManufacturerName": MANUFACTURER, "Manufacturer_PartNum": PART_NUM,
    "Name": "VARCHAR(100)", "Description": "VARCHAR(1000)", "Category": "VARCHAR(50)",
    "Length": DIMENSION, "Width": DIMENSION, "Height": DIMENSION,
    "Datasheet_link": "VARCHAR(2048)",
    # Distributor (Website is an AK, so it is kept short enough for a UNIQUE index)
    "Website": "VARCHAR(255)", "ShippingFee": MONEY,
    # Listing
    "DistributorName": DISTRIBUTOR, "Distributor_PartNum": PART_NUM,
    "Packaging": "VARCHAR(20)", "UnitPrice": MONEY, "StockQuantity": "INTEGER",
    "EstShipTime": "INTEGER", "LastUpdated": "TIMESTAMP",
    # ShoppingCart, BOM, SharedProject
    "CustomerEmail": EMAIL, "Date_created": "DATE", "BOM_name": BOM_NAME,
    "Title": "VARCHAR(100)", "Date_shared": "DATE",
    # PartAlternative
    "Part1_ManufacturerName": MANUFACTURER, "Part1_PartNum": PART_NUM,
    "Part2_ManufacturerName": MANUFACTURER, "Part2_PartNum": PART_NUM,
    # BOMLine, CartLine, Review
    "Quantity": QUANTITY, "ReviewText": "VARCHAR(2000)", "StarRating": "INTEGER",
}
# Per-relation overrides, where one attribute name has a different meaning
TYPE_OVERRIDES = {("Distributor", "Name"): DISTRIBUTOR}

# Optional attributes (left nullable). Everything else is NOT NULL.
NULLABLE = {
    ("Customer", "UnitNum"),          # most addresses have no unit number
    ("Part", "Description"),
    ("Part", "Length"), ("Part", "Width"), ("Part", "Height"),  # not every part has dimensions
    ("Part", "Datasheet_link"),
    ("SharedProject", "Description"),
    ("Review", "ReviewText"),         # a rating without text is allowed
}

# Column meaning, written as a short comment next to the column
COLUMN_NOTES = {
    ("Listing", "EstShipTime"): "estimated shipping time in days",
    ("Part", "Length"): "millimetres",
    ("Customer", "Password"): "a salted hash, never plain text",
}

# C1 and other domain rules. None of these columns has an FK referential action,
# so MySQL accepts them (error 3823 only affects FK columns).
CHECKS = {
    "Part": [("ck_Part_dims", "Length > 0 AND Width > 0 AND Height > 0")],
    "Distributor": [("ck_Distributor_fee", "ShippingFee >= 0")],
    "Listing": [("ck_Listing_price", "UnitPrice >= 0"),
                ("ck_Listing_stock", "StockQuantity >= 0"),
                ("ck_Listing_ship", "EstShipTime >= 0"),
                ("ck_Listing_pack", "Packaging IN ('Cut Tape', 'Tape & Reel', 'Tray', 'Bulk', 'Tube')")],
    "BOMLine": [("ck_BOMLine_qty", "Quantity > 0")],
    "CartLine": [("ck_CartLine_qty", "Quantity > 0")],
    "Review": [("ck_Review_stars", "StarRating BETWEEN 1 AND 5")],
}
CHECK_NOTES = {
    "ck_Part_dims": "a NULL dimension makes the CHECK unknown, which passes (ISO rule)",
    "ck_Listing_pack": "replaces a MySQL ENUM with an ISO CHECK on a fixed list",
    "ck_Review_stars": "C1",
}

# Indexes beyond the ones InnoDB builds for every PK, UNIQUE and FK.
INDEXES = [
    ("ix_Part_Category", "Part", ["Category"],
     "Filter by category (Assignment 1 Filter function, Task 4 Q2/Q6). No key starts with Category."),
    ("ix_Listing_Part_Price", "Listing", ["ManufacturerName", "Manufacturer_PartNum", "UnitPrice"],
     "Price Match: all offers for one part ordered by price. Also serves the FK to Part, so InnoDB "
     "reuses it instead of building a separate FK index."),
]

# ------------------------------------------------------------------------------
# Writing the SQL
# ------------------------------------------------------------------------------
def col_type(rel, attr):
    return TYPE_OVERRIDES.get((rel, attr)) or TYPES[attr]


def fk_columns(rel):
    return {c for cols, *_ in rel["fks"] for c in cols}


def create_table(rel):
    name = rel["name"]
    fk_cols = fk_columns(rel)
    width = max(len(a) for a in rel["attrs"])
    lines = []
    for attr in rel["attrs"]:
        nullable = (name, attr) in NULLABLE
        assert not (nullable and (attr in rel["pk"] or attr in fk_cols)), (name, attr)
        line = "    %-*s %s%s" % (width, attr, col_type(name, attr), "" if nullable else " NOT NULL")
        note = COLUMN_NOTES.get((name, attr))
        lines.append((line, note))

    cons = []
    cons.append(("    CONSTRAINT pk_%s PRIMARY KEY (%s)" % (name, ", ".join(rel["pk"])), None))
    for n, ak in enumerate(rel["aks"], start=1):
        cons.append(("    CONSTRAINT ak_%s_%d UNIQUE (%s)" % (name, n, ", ".join(ak)), None))
    for n, (cols, target, tcols, on_delete, reason) in enumerate(rel["fks"], start=1):
        cons.append(("    CONSTRAINT fk_%s_%s FOREIGN KEY (%s)\n"
                     "        REFERENCES %s (%s)\n"
                     "        ON DELETE %s ON UPDATE CASCADE"
                     % (name, target if [f[1] for f in rel["fks"]].count(target) == 1 else "%s%d" % (target, n),
                        ", ".join(cols), target, ", ".join(tcols), on_delete), reason))
    for cname, expr in CHECKS.get(name, []):
        cons.append(("    CONSTRAINT %s CHECK (%s)" % (cname, expr), CHECK_NOTES.get(cname)))

    body = lines + cons
    out = ["CREATE TABLE %s (" % name]
    for i, (text, note) in enumerate(body):
        comma = "," if i < len(body) - 1 else ""
        if note and "\n" in text:
            out.append("    -- " + note)
            out.append(text + comma)
        elif note:
            out.append("%s%s  -- %s" % (text, comma, note))
        else:
            out.append(text + comma)
    out.append(");")
    return "\n".join(out)


def dependency_order():
    done, order, rels = set(), [], list(report.RELS)
    while rels:
        for r in rels:
            if all(f[1] in done or f[1] == r["name"] for f in r["fks"]):
                order.append(r)
                done.add(r["name"])
                rels.remove(r)
                break
        else:
            raise SystemExit("PROBLEM: circular foreign keys")
    return order


HEADER = """\
-- task3.sql: Task 1, CREATE TABLE statements
-- ============================================================================
-- AISE 3309 Assignment 3, Group 6: Engineering Part Sourcer
-- Generated by SRC/build_ddl.py from RELS in Assignment2/build_report.py.
-- Do not edit by hand: change build_ddl.py (types, CHECKs, indexes) or RELS
-- (keys, FKs) and rerun it.
--
-- Target: MySQL 8.0.16 or later (CHECK constraints are only enforced from
-- 8.0.16; earlier versions parse and silently ignore them). Tested on MySQL
-- 26.10.0 with sql_mode ONLY_FULL_GROUP_BY, STRICT_TRANS_TABLES.
--
-- Conventions
--   * ISO SQL throughout. Identifiers are unquoted (no backticks, no double
--     quotes). Every MySQL-only statement is marked "MySQL-specific".
--   * Keys are named constraints: pk_<Relation>, ak_<Relation>_<n>,
--     fk_<Relation>_<Target>, ck_<Relation>_<rule>.
--   * Every FK column is NOT NULL and uses ON UPDATE CASCADE. ON DELETE is
--     taken from the Assignment 2 referential integrity table.
--   * Derived attributes (/AvgStarRating, /NumberOfParts, /UnpricedParts,
--     /TotalCost, /Subtotal, /ShippingPrice, /TotalPrice) are NOT columns.
--     They are computed in queries and in the BOMTotals view (task8.sql).
--   * No triggers (group decision; the handout makes them optional). See the
--     "Constraints not enforced by the DBMS" block at the end of this file.
-- ============================================================================
"""

FOOTER = """\
-- ============================================================================
-- Constraints not enforced by the DBMS
-- ----------------------------------------------------------------------------
-- C1 (ranges), C2 (Listing AK), C6 (Review PK) and every FK are enforced above.
-- The four rules below cannot be written as a key or a CHECK that MySQL
-- accepts. The group decided not to use triggers, so each rule is written in
-- its ISO form for the record and upheld outside the DBMS:
--   * SRC/generate_data.py asserts it before writing load_data.sql,
--   * the Assignment 4 application checks it on every change, and
--   * SRC/check_data.sql has a query that returns 0 rows when it holds.
--
-- C3: a BOM selects only listings of parts it contains, at most one per part.
--   It spans BOMSelection, Listing and BOMLine, so the ISO form is an
--   assertion (C&B ch. 7). MySQL does not support CREATE ASSERTION.
--
--   CREATE ASSERTION SelectionMatchesLine CHECK (NOT EXISTS (
--       SELECT * FROM BOMSelection s JOIN Listing l
--              ON l.DistributorName = s.DistributorName
--             AND l.Distributor_PartNum = s.Distributor_PartNum
--       WHERE NOT EXISTS (
--           SELECT * FROM BOMLine b
--           WHERE b.CustomerEmail = s.CustomerEmail
--             AND b.BOM_name = s.BOM_name
--             AND b.ManufacturerName = l.ManufacturerName
--             AND b.Manufacturer_PartNum = l.Manufacturer_PartNum)));
--
--   CREATE ASSERTION OneSelectionPerPart CHECK (NOT EXISTS (
--       SELECT s.CustomerEmail, s.BOM_name, l.ManufacturerName, l.Manufacturer_PartNum
--       FROM BOMSelection s JOIN Listing l
--              ON l.DistributorName = s.DistributorName
--             AND l.Distributor_PartNum = s.Distributor_PartNum
--       GROUP BY s.CustomerEmail, s.BOM_name, l.ManufacturerName, l.Manufacturer_PartNum
--       HAVING COUNT(*) > 1));
--
-- C4: AlternativeTo is symmetric and irreflexive. Each pair is stored once,
--   with the smaller part key first. The ISO form is a table CHECK:
--
--   CONSTRAINT ck_PartAlternative_order CHECK (
--       (Part1_ManufacturerName, Part1_PartNum) < (Part2_ManufacturerName, Part2_PartNum))
--
--   MySQL rejects it with error 3823 ("Column cannot be used in a check
--   constraint: needed in a foreign key constraint referential action"),
--   because all four columns have ON UPDATE CASCADE / ON DELETE CASCADE.
--   The Assignment 2 referential actions are kept rather than weakened to make
--   the CHECK fit. Queries read each pair in both directions (Task 4).
--
-- C5: a SharedProject's BOM always has at least one BOMLine.
--
--   CREATE ASSERTION SharedBOMNotEmpty CHECK (NOT EXISTS (
--       SELECT * FROM SharedProject p
--       WHERE NOT EXISTS (
--           SELECT * FROM BOMLine b
--           WHERE b.CustomerEmail = p.CustomerEmail
--             AND b.BOM_name = p.BOM_name)));
--
-- C7: the part offered by a listing never changes.
--   This is a rule about UPDATE (old value vs. new value), which no CHECK or
--   assertion can express: both only see the current state. The application
--   never updates Listing.ManufacturerName or Listing.Manufacturer_PartNum; an
--   offer for a different part is inserted as a new listing. The only change
--   to those columns is the ON UPDATE CASCADE from Part when a part's own key
--   is corrected, and then the listing still refers to the same part.
-- ============================================================================

-- DESCRIBE output for the report (run these in Workbench and screenshot them):
"""


def build():
    order = dependency_order()
    out = [HEADER]
    out.append("-- MySQL-specific: DROP TABLE IF EXISTS. ISO SQL has DROP TABLE <name>\n"
               "-- [RESTRICT | CASCADE] with no IF EXISTS; it lets this script be rerun.\n"
               "-- Children are dropped before their parents.")
    for rel in reversed(order):
        out.append("DROP TABLE IF EXISTS %s;" % rel["name"])
    out.append("")

    for rel in order:
        out.append("-- %s" % rel["name"])
        out.append(create_table(rel))
        out.append("")

    out.append("-- Indexes")
    out.append("-- MySQL-specific: CREATE INDEX is not part of ISO SQL (indexes are a\n"
               "-- physical design choice the standard leaves to the DBMS), but it is the\n"
               "-- form taught in lectures (C&B 7.3.5). InnoDB already indexes every PK,\n"
               "-- UNIQUE and FK, so only the two indexes below are added.")
    for iname, table, columns, why in INDEXES:
        out.append("-- %s" % why)
        out.append("CREATE INDEX %s ON %s (%s);" % (iname, table, ", ".join(columns)))
    out.append("")

    out.append(FOOTER.rstrip("\n"))
    for rel in order:
        out.append("-- DESCRIBE %s;" % rel["name"])
    return "\n".join(out) + "\n"


def main():
    names = {r["name"] for r in report.RELS}
    for r in report.RELS:
        for a in r["attrs"]:
            col_type(r["name"], a)   # KeyError means a type is missing
        for cname, _ in CHECKS.get(r["name"], []):
            pass
        for c, target, tcols, act, _ in r["fks"]:
            assert target in names and act in ("CASCADE", "RESTRICT"), (r["name"], c)
    sql = build()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(sql)
    print("wrote", OUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
