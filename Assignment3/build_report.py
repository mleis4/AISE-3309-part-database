# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         build_report.py   (Assignment 3)
# Description:     Builds AISE3309-Assignment03_Group6.html and .pdf.
#                  - Every SQL statement is read from SQL/ and SRC/ at build
#                    time, so the report always matches the .zip archive.
#                  - Next to each statement it shows the group's Workbench
#                    screenshot from screenshots/<name>.png. Until that file
#                    exists it shows the server response recorded by
#                    capture_responses.py, marked as a placeholder.
#                  - Styling, headings, tables and the contents list are
#                    imported from ../Assignment2/build_report.py. That script
#                    is only imported, never run (running it overwrites the
#                    submitted A2 PDF and .docx).
#
# Run:             python capture_responses.py   (refresh the responses)
#                  python build_report.py
# ------------------------------------------------------------------------------
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "Assignment2"))
import build_report as a2  # noqa: E402  (A2 helpers: CSS, h2, h3, table, toc)

BASE = "AISE3309-Assignment03_Group6"
OUT_HTML = os.path.join(HERE, BASE + ".html")
OUT_PDF = os.path.join(HERE, BASE + ".pdf")
SHOTS = os.path.join(HERE, "screenshots")
RESP = os.path.join(HERE, "responses")
esc = html.escape
h2, h3, table = a2.h2, a2.h3, a2.table

# Team contributions: each member edits their own entry.
CONTRIB = {name: ["[to be completed by the group]"] for name, _ in a2.MEMBERS}

EXTRA_CSS = """
pre.sql, pre.out { font-family: Consolas, 'Courier New', monospace; font-size: 7.6pt; line-height: 1.3;
  white-space: pre-wrap; word-break: break-word; margin: 4px 0; padding: 6px 8px; border-radius: 3px; }
pre.sql { background: #f4f7fb; border-left: 3px solid #1e88e5; }
pre.out { background: #fbfbf7; border: 1px dashed #b0a060; }
pre.err { color: #a00000; }
.stmt { break-inside: avoid; margin: 8px 0 12px; }
.shotlabel { font-size: 7.5pt; color: #806000; margin: 2px 0 0; }
.shotlabel.ok { color: #2e7d32; }
.shot { break-inside: avoid; margin: 6px 0 14px; }
.shot img { max-width: 100%; border: 1px solid #999; display: block; margin: 4px 0; }
.shot.missing { border: 2px dashed #c62828; background: #fdecea; color: #8e1b1b; padding: 10px 12px; font-size: 9pt; }
.note { background: #fff8e1; border-left: 3px solid #f9a825; padding: 5px 9px; margin: 8px 0; font-size: 9pt; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 8.5pt; }
td code { font-size: 8pt; }
"""

MISSING = []    # screenshots not yet supplied


# ------------------------------------------------------------------------------
# Inputs
# ------------------------------------------------------------------------------
def read(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as f:
        return f.read()


def responses(name):
    path = os.path.join(RESP, name + ".json")
    if not os.path.exists(path):
        raise SystemExit("responses/%s.json missing: run python capture_responses.py first" % name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def inline_md(text):
    """Bold, inline code and the <sub> tags used in explanation.md."""
    text = esc(text).replace("&lt;sub&gt;", "<sub>").replace("&lt;/sub&gt;", "</sub>")
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", text)
    return text


def md_to_html(md, heading_shift=1):
    """A small Markdown subset: headings, paragraphs, lists, tables, code fences."""
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append('<pre class="sql">%s</pre>' % esc("\n".join(lines[i + 1:j])))
            i = j + 1
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            out.append("<h%d>%s</h%d>" % (min(6, level + heading_shift), inline_md(line.lstrip("# ")),
                                          min(6, level + heading_shift)))
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|:]+\|$", lines[i]):
                    rows.append([inline_md(c.strip()) for c in lines[i].strip("|").split(" | ")])
                i += 1
            out.append(table(rows[0], rows[1:]))
        elif re.match(r"^\s*(-|\d+\.|\d+a\.)\s", line):
            items = []
            while i < len(lines) and (re.match(r"^\s*(-|\d+\.|\d+a\.)\s", lines[i]) or lines[i].startswith("   ")):
                if re.match(r"^\s*(-|\d+\.|\d+a\.)\s", lines[i]):
                    depth = len(lines[i]) - len(lines[i].lstrip())
                    items.append([depth, re.sub(r"^\s*(-|\d+\.|\d+a\.)\s", "", lines[i])])
                else:
                    items[-1][1] += " " + lines[i].strip()
                i += 1
            html_items = []
            for depth, text in items:
                style = ' style="margin-left:%dpx"' % (depth * 6) if depth else ""
                html_items.append("<li%s>%s</li>" % (style, inline_md(text)))
            out.append('<ul class="tight">%s</ul>' % "".join(html_items))
        elif line.startswith(">"):
            out.append('<div class="note">%s</div>' % inline_md(line.lstrip("> ")))
            i += 1
        elif line.strip() in ("", "---"):
            i += 1
        else:
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|\s*-\s|>)", lines[i]):
                para.append(lines[i])
                i += 1
            out.append("<p>%s</p>" % inline_md(" ".join(para)))
    return "\n".join(out)


def md_section(md, start, stop=None):
    """The text from heading `start` up to heading `stop` (exclusive)."""
    begin = md.index(start)
    end = md.index(stop, begin) if stop else len(md)
    return md[begin:end]


# ------------------------------------------------------------------------------
# Statement blocks
# ------------------------------------------------------------------------------
# The Workbench screenshots the report needs: about one per handout requirement.
# Every statement also shows its response as text (recorded by
# capture_responses.py), so these screenshots are the evidence that the
# statements were run in MySQL Workbench, not one picture per statement.
# Workbench's Action Output panel lists the response of every statement in a
# script, so one screenshot covers a whole file. If the panel needs scrolling,
# add <name>_2.png, <name>_3.png ...; they are embedded after the first one.
SHOT_PLAN = [
    ("t1_create", "Task 1",
     "Run task3.sql on an empty database. Action Output panel showing every CREATE TABLE and CREATE INDEX "
     "with its response (0 row(s) affected)."),
    ("t2_select1", "Task 2", "task4.sql: result grid of the 1st SELECT * FROM BOMLine (after INSERT 1)."),
    ("t2_select2", "Task 2", "task4.sql: result grid of the 2nd SELECT * FROM BOMLine (after INSERT 2)."),
    ("t2_select3", "Task 2", "task4.sql: result grid of the 3rd SELECT * FROM BOMLine (after INSERT 3)."),
    ("t2_output", "Task 2", "task4.sql: Action Output panel with the response of each INSERT."),
    ("t3_counts", "Task 3", "check_data.sql: result grid of the final row-count query (tuples per relation)."),
    ("t4_q1", "Task 4", "task6.sql: Q1 with its result grid."),
    ("t4_q2", "Task 4", "task6.sql: Q2 with its result grid."),
    ("t4_q3", "Task 4", "task6.sql: Q3 with its result grid."),
    ("t4_q4", "Task 4", "task6.sql: Q4 with its result grid."),
    ("t4_q5", "Task 4", "task6.sql: Q5 with its result grid."),
    ("t4_q6", "Task 4", "task6.sql: Q6 with its result grid."),
    ("t4_q7", "Task 4", "task6.sql: Q7 with its result grid."),
    ("t5_m1", "Task 5", "task7.sql: result grid of the SELECT after M1 (Jordan's 5 copied lines)."),
    ("t5_m2", "Task 5", "task7.sql: result grid of the SELECT after M2 (129 listings, higher average price)."),
    ("t5_m3", "Task 5", "task7.sql: result grid of the SELECT after M3 (182 carts, 1110 cart lines)."),
    ("t5_output", "Task 5",
     "task7.sql: Action Output panel for the whole file, showing the M1-M3 responses (rows affected) and the "
     "M2b/M3b errors 3819 and 1451."),
    ("t6_create", "Task 6", "task8.sql: Action Output panel with the two CREATE VIEW responses."),
    ("t6_v1_query", "Task 6", "task8.sql: result grid of the query on BOMTotals."),
    ("t6_v2_query", "Task 6", "task8.sql: result grid of the query on InStockListing."),
    ("t6_modify", "Task 6",
     "task8.sql: Action Output panel for the modification attempts (errors 1471, 1288, 1369, 1369 and the "
     "successful INSERT and UPDATE)."),
]
SHOT_INFO = {name: (task, what) for name, task, what in SHOT_PLAN}


def text_response(text):
    text = text or "(no output)"
    err = " err" if text.startswith("ERROR") else ""
    return '<pre class="out%s">%s</pre>' % (err, esc(text))


def shot_slot(name):
    """The Workbench screenshot `name` (plus _2, _3 ... parts), or a placeholder box."""
    task, what = SHOT_INFO[name]
    parts = [name] + ["%s_%d" % (name, n) for n in range(2, 10)]
    found = [p for p in parts if os.path.exists(os.path.join(SHOTS, p + ".png"))]
    if not found:
        MISSING.append(name + ".png")
        return ('<div class="shot missing"><b>Screenshot needed: screenshots/%s.png</b><br>%s</div>'
                % (name, esc(what)))
    imgs = "".join('<img src="file:///%s">' % os.path.join(SHOTS, p + ".png").replace("\\", "/") for p in found)
    return '<div class="shot">%s<p class="shotlabel ok">Figure: MySQL Workbench, %s</p></div>' % (imgs, esc(what))


def stmt_block(record, show_comments=True):
    sql = record["sql"]
    if show_comments and record["comments"]:
        sql = record["comments"] + "\n" + sql
    return '<div class="stmt"><pre class="sql">%s</pre>%s</div>' % (esc(sql), text_response(record["response"]))


def file_blocks(name, slots=(), show_comments=True):
    """Every statement of a file with its recorded response.

    slots: (sql prefix, occurrence, screenshot name). The screenshot slot is
    placed right after the n-th statement that starts with that prefix.
    """
    out, seen = [], {}
    for record in responses(name):
        out.append(stmt_block(record, show_comments))
        for prefix, occurrence, shot in slots:
            if record["sql"].startswith(prefix):
                seen[prefix, shot] = seen.get((prefix, shot), 0) + 1
                if seen[prefix, shot] == occurrence:
                    out.append(shot_slot(shot))
    return "\n".join(out)


def header_comment(path):
    lines = []
    for line in read(path).splitlines():
        if not line.startswith("--"):
            break
        lines.append(line)
    return '<pre class="sql">%s</pre>' % esc("\n".join(lines))


# ------------------------------------------------------------------------------
# Report
# ------------------------------------------------------------------------------
def build_html():
    del a2.TOC[:]
    del MISSING[:]
    H = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
         '<title>AISE 3309 Assignment 03 - Group 6</title><style>%s%s</style></head><body>' % (a2.CSS, EXTRA_CSS)]
    rows = "".join("<tr><td>%d.&nbsp; %s</td><td>%s</td></tr>" % (i + 1, n, sid) for i, (n, sid) in enumerate(a2.MEMBERS))
    H.append('<div class="cover"><div class="banner">Western Engineering<br>Electrical and Computer Engineering</div>'
             '<p class="ctitle">AISE 3309: Database Management Systems</p><p class="csub1">Assignment 03</p>'
             '<p class="csub2">Database Implementation</p>'
             '<table><tr><td><b>Group #:</b></td><td>6 (Lab 2, AISE 3309A 002)</td></tr>'
             '<tr><td><b>Project Name:</b></td><td>Engineering Part Sourcer</td></tr>'
             '<tr><th style="width:50%">Team Member Name</th><th>Team Member ID</th></tr>' + rows + '</table></div>')
    H.append('<p class="toctitle" style="page-break-before:always">Table of Contents</p>')
    toc_at = len(H)
    H.append("")

    # ---- 0. Schema evaluation
    H.append(h2("0.", "Final Schema Evaluation and Refinement"))
    H.append("<p>Assignment 3 starts with a final, critical evaluation of the Assignment 2 schema. The peer review "
             "of Assignment 2 raised four points; the table records what changed and why. Every relation is still "
             "in BCNF: the only new determinants are the changed alternate keys, and both are candidate keys.</p>")
    sc = read("SCHEMA_CHANGES.md")
    H.append(md_to_html(md_section(sc, "| # |", "## Implementation decision"), 2))
    H.append(h3("0.1", "Implementation decision: no triggers"))
    H.append(md_to_html(md_section(sc, "## Implementation decision", "## Still to do").split("\n", 1)[1], 2))

    # ---- 1. Task 1
    H.append(h2("1.", "Task 1: SQL Database Schema Creation"))
    H.append("<p>The schema is in <code>SQL/task3.sql</code>. It is generated by <code>SRC/build_ddl.py</code> from the "
             "same definition of the relations (<code>RELS</code>) that produced the Assignment 2 diagrams, so the table "
             "names, keys and foreign keys cannot drift from the design. The script adds what Assignment 2 left "
             "open: data types, NOT NULL, CHECK constraints and indexes.</p>")
    H.append(h3("1.1", "Design decisions"))
    H.append(table(["Decision", "Choice and reason"], [
        ["Data types", "VARCHAR for names, emails and part numbers (Email VARCHAR(254), the longest legal address); "
                       "DECIMAL(10,2) for money; INTEGER for quantities, stock and ratings; DATE for creation dates; "
                       "TIMESTAMP for Listing.LastUpdated. ISO CREATE DOMAIN would define each shared domain once; "
                       "MySQL lacks it, so the type is repeated."],
        ["Keys", "Named constraints: <code>pk_</code>, <code>ak_</code> (UNIQUE), <code>fk_</code>, <code>ck_</code>. "
                 "Every FK column is NOT NULL with ON UPDATE CASCADE; ON DELETE (CASCADE or RESTRICT) is taken from "
                 "the A2 referential integrity table."],
        ["CHECK (C1 and domains)", "StarRating BETWEEN 1 AND 5; Quantity &gt; 0; UnitPrice, StockQuantity, EstShipTime "
                                   "and ShippingFee &gt;= 0; positive dimensions; Packaging IN a fixed list (instead of "
                                   "MySQL's ENUM). Enforced by MySQL 8.0.16 and later."],
        ["C2 and C6", "C2 is the alternate key ak_Listing_1 (DistributorName, ManufacturerName, Manufacturer_PartNum, "
                      "Packaging). C6 is the primary key of Review."],
        ["Optional attributes", "Left nullable: Customer.UnitNum, Part.Description, the three dimensions, "
                                "Part.Datasheet_link, SharedProject.Description, Review.ReviewText."],
        ["Indexes", "InnoDB already indexes every PK, UNIQUE and FK. Two are added: Part(Category) for the category "
                    "filter, and Listing(ManufacturerName, Manufacturer_PartNum, UnitPrice) for Price Match."],
        ["Derived attributes", "Not stored (A2 decision). They are computed in queries and the BOMTotals view."],
        ["Triggers", "None (group decision). C3, C4, C5 and C7 are documented at the end of task3.sql in their ISO "
                     "form (CREATE ASSERTION or CHECK) and verified by SRC/check_data.sql (section 3.3)."],
    ], ["22%", "78%"]))
    H.append(h3("1.2", "CREATE TABLE statements and responses"))
    H.append(header_comment("SQL/task3.sql"))
    recs = responses("task3")
    drops = [r for r in recs if r["sql"].startswith("DROP")]
    H.append('<div class="stmt"><pre class="sql">%s</pre>%s</div>' % (
        esc(drops[0]["comments"] + "\n" + "\n".join(r["sql"] for r in drops)),
        text_response("\n\n".join(r["response"] for r in drops))))
    for r in recs:
        if r["sql"].startswith("CREATE TABLE"):
            H.append(stmt_block(r, show_comments=False))
        elif r["sql"].startswith("CREATE INDEX"):
            H.append(stmt_block(r))
    H.append(shot_slot("t1_create"))
    H.append(h3("1.3", "DESCRIBE output for each relation", pb=True))
    H.append("<p>The handout accepts the CREATE TABLE responses above <i>or</i> DESCRIBE output. Both are given; "
             "the DESCRIBE output below was recorded with the mysql client.</p>")
    for r in responses("describe"):
        H.append(stmt_block(r))
    H.append(h3("1.4", "Constraints not enforced by the DBMS"))
    footer = read("SQL/task3.sql")
    block = footer[footer.index("-- Constraints not enforced by the DBMS"):footer.index("-- DESCRIBE output")]
    H.append('<pre class="sql">%s</pre>' % esc(block.rstrip()))

    # ---- 2. Task 2
    H.append(h2("2.", "Task 2: Basic Data Insertion"))
    H.append("<p>All three INSERTs target <b>BOMLine</b>. They differ in structure, not just values: (1) one tuple "
             "with no column list, in table order; (2) three tuples in one statement with an explicit column list in a "
             "different order; (3) <code>INSERT ... SELECT</code>, where the new tuples are the result of a query. "
             "The file runs on the empty schema, before the bulk load, so each <code>SELECT *</code> is short. Its "
             "keys never occur in the generated data, so the load still succeeds afterwards.</p>")
    H.append(header_comment("SQL/task4.sql"))
    H.append(file_blocks("task4", [("SELECT * FROM BOMLine", n, "t2_select%d" % n) for n in (1, 2, 3)]))
    H.append(shot_slot("t2_output"))

    # ---- 3. Task 3
    H.append(h2("3.", "Task 3: Substantial Data Loading"))
    H.append("<p><code>SRC/generate_data.py</code> (Python 3, standard library only, fixed seed 3309) fabricates the "
             "data and writes <code>SRC/load_data.sql</code>: multi-row <code>INSERT INTO ... VALUES</code> batches of "
             "500 tuples inside one <code>START TRANSACTION ... COMMIT</code>, in dependency order (parents first). "
             "The data is mock data: manufacturer and distributor names look real, but every part, price, address and "
             "review is invented. Before writing anything, the script asserts every key, every foreign key and "
             "constraints C1 to C6, because the DBMS does not enforce C3, C4 and C5.</p>")
    H.append(h3("3.1", "How to rebuild the database"))
    H.append(table(["Step", "File", "What it does"], [
        ["1", "SQL/task3.sql", "Drops and creates the 12 tables and 2 indexes"],
        ["2", "SQL/task4.sql", "Task 2 inserts (5 BOMLine tuples and their parents)"],
        ["3", "SRC/load_data.sql", "Loads the generated data (about 24,000 tuples)"],
        ["4", "SRC/check_data.sql", "Integrity checks: every count must be 0"],
        ["5", "SQL/task6.sql, task7.sql, task8.sql", "Tasks 4 to 6 (task7 and task8 end with ROLLBACK)"],
        ["or", "DUMP/ep_sourcer_dump.sql", "Restores the whole database, views included, in one step"],
    ], ["8%", "32%", "60%"]))
    H.append(h3("3.2", "Coverage of edge cases"))
    H.append('<ul class="tight">'
             "<li>12% of parts have no listing; 12% of listings have stock 0, so stock filters change results.</li>"
             "<li>20% of (distributor, part) pairs come in 2 or 3 packagings, so C2 and the price comparison have real choices.</li>"
             "<li>Generic parts (1N4148, 2N3904, LM358, NE555, L7805) are made by several manufacturers: the reason for the composite part key.</li>"
             "<li>About 29% of BOM lines have no selected listing (non-zero /UnpricedParts); 41 BOMs have no lines at all; 69 customers have no BOM; 17 carts are empty.</li>"
             "<li>Shared-project titles repeat across customers (the AK is per customer).</li></ul>")
    H.append(h3("3.3", "Integrity checks and relation sizes"))
    H.append("<p>Two relations hold thousands of tuples (Part, Listing, BOMLine, BOMSelection) and several hold hundreds "
             "(Customer, BOM, Review, CartLine, PartAlternative). Part and BOM include the Task 2 rows.</p>")
    H.append(file_blocks("check_data", [("SELECT 'Customer'", 1, "t3_counts")], show_comments=False))
    H.append(h3("3.4", "Sample records", pb=True))
    samples = read("SRC/samples.md")
    H.append(md_to_html(samples[samples.index("## Customer"):], 2))
    H.append(h3("3.5", "Database dump"))
    H.append('<p><code>DUMP/ep_sourcer_dump.sql</code> holds the loaded database, including both views. '
             '<span class="note">Placeholder: this copy was made with mysqldump by capture_responses.py. Replace it '
             'with the Workbench export (Server &gt; Data Export, "Dump Structure and Data", self-contained file).</span></p>')

    # ---- 4. Task 4
    H.append(h2("4.", "Task 4: SQL Queries (SELECT)"))
    H.append("<p>Seven queries, each answering a question an Assignment 1 function asks. Q1 is the one plain query; "
             "each of the other six uses a different main feature. No row-limit syntax is used: the conditions keep "
             "every result short. <code>explanation.md</code> explains each query's logic, execution order and "
             "relational algebra.</p>")
    H.append(table(["#", "Question", "Main SQL feature", "Rows"], [
        ["Q1", "Distributors shipping for under $7", "simple SELECT-FROM-WHERE, ORDER BY", "7"],
        ["Q2", "Offers for 100 units of 1N4148, with cost", "3-relation inner join on a composite key, computed column", "2"],
        ["Q3", "BOM totals and unpriced lines for one customer", "LEFT OUTER JOIN + GROUP BY + COUNT/SUM/COALESCE", "9"],
        ["Q4", "Best-rated parts", "GROUP BY + HAVING on two aggregates", "16"],
        ["Q5", "Op-amps listed but out of stock everywhere", "correlated EXISTS and NOT EXISTS", "8"],
        ["Q6", "Cheapest in-stock offer for each line of a BOM", "correlated scalar subquery with MIN", "7"],
        ["Q7", "Alternatives to a part, both directions", "UNION", "2"],
    ], ["6%", "40%", "44%", "10%"]))
    for n, r in enumerate(responses("task6"), start=1):
        H.append("<h4>Q%d</h4>" % n)
        H.append(stmt_block(r))
        H.append(shot_slot("t4_q%d" % n))

    # ---- 5. Task 5
    H.append(h2("5.", "Task 5: Data Modification Commands"))
    H.append("<p>M1 is an <code>INSERT ... SELECT</code>, M2 an <code>UPDATE</code> of 129 tuples chosen by a subquery, "
             "and M3 a <code>DELETE</code> chosen by a correlated <code>NOT EXISTS</code> that cascades to CartLine. "
             "M2b and M3b fail on purpose to show a CHECK constraint and an ON DELETE RESTRICT foreign key rejecting "
             "a change. Each command sits between SELECTs that show its effect. The file runs in one transaction that "
             "ends with ROLLBACK, so it can be rerun and the database stays equal to the dump.</p>")
    H.append(header_comment("SQL/task7.sql"))
    H.append(file_blocks("task7", [("SELECT bl.BOM_name", 1, "t5_m1"),
                                   ("SELECT COUNT(*) AS LCSCCapacitorListings", 2, "t5_m2"),
                                   ("SELECT COUNT(*) AS Carts", 2, "t5_m3")]))
    H.append(shot_slot("t5_output"))

    # ---- 6. Task 6
    H.append(h2("6.", "Task 6: View Creation and Evaluation"))
    H.append("<p><b>BOMTotals</b> (not updatable) gives each BOM's /NumberOfParts, /UnpricedParts and /TotalCost. "
             "<b>InStockListing</b> (updatable, WITH CHECK OPTION) holds the listings that can be bought now. "
             "The script shows each CREATE VIEW, a query on each view, and modification attempts on both.</p>")
    H.append(header_comment("SQL/task8.sql"))
    H.append(file_blocks("task8", [("CREATE VIEW InStockListing", 1, "t6_create"),
                                   ("SELECT sp.Title", 1, "t6_v1_query"),
                                   ("SELECT v.ManufacturerName", 1, "t6_v2_query")]))
    H.append(shot_slot("t6_modify"))
    H.append(h3("6.1", "Are the views updatable?", pb=True))
    ex = read("explanation.md")
    H.append(md_to_html(md_section(ex, "### The ISO rules", "## Likely TA questions"), 1))

    # ---- 7. ISO notes
    H.append(h2("7.", "Notes on ISO SQL"))
    H.append("<p>All statements use ISO SQL as covered in lectures: unquoted identifiers, ISO types, named constraints, "
             "<code>DATE '...'</code> and <code>TIMESTAMP '...'</code> literals, <code>CURRENT_DATE</code>/"
             "<code>CURRENT_TIMESTAMP</code>, <code>COALESCE</code> and <code>CAST</code>. The MySQL-specific features "
             "below were unavoidable; each is marked <code>-- MySQL-specific:</code> in the files.</p>")
    H.append(table(["Feature", "Where", "Why it is needed / ISO form"], [
        ["DROP TABLE IF EXISTS, DROP VIEW IF EXISTS", "task3.sql, task8.sql", "Lets the scripts be rerun. ISO has DROP TABLE/VIEW without IF EXISTS."],
        ["CREATE INDEX", "task3.sql", "Indexes are not part of ISO SQL (physical design), but CREATE INDEX is the form taught in the course."],
        ["CREATE DOMAIN, CREATE ASSERTION", "task3.sql (comments)", "ISO features MySQL lacks. Written as comments next to the MySQL substitute."],
        ["C4 CHECK (row comparison)", "task3.sql (comment)", "MySQL error 3823: a CHECK may not use columns with FK referential actions."],
        ["Workbench / --force", "task7.sql, task8.sql", "The scripts contain statements that fail on purpose; the client must continue after an error."],
    ], ["30%", "22%", "48%"]))

    # ---- 8. AI use
    H.append(h2("8.", "AI Use"))
    H.append("<p>As the handout allows, an AI assistant (Claude) drafted the data generator and helped draft the SQL. "
             "Following the AI policy, <code>explanation.md</code> explains the logic, syntax, execution order and "
             "relational algebra of every statement in Tasks 4 to 6, and <code>ai_log.md</code> records what the AI "
             "did, how each output was checked against the loaded data, and what it got wrong. Every statement in this "
             "report was run on MySQL 26.10, and the group has read and verified each one.</p>")

    # ---- 9. Contributions
    H.append(h2("9.", "Team Contribution Efforts"))
    H.append(table(["Team member", "Contribution"],
                   [[n, '<ul class="tight">%s</ul>' % "".join("<li>%s</li>" % esc(i) for i in CONTRIB[n])]
                    for n, _ in a2.MEMBERS], ["22%", "78%"]))
    H.append("</body></html>")
    H[toc_at] = a2.toc_html()
    return "\n".join(H)


def find_browser():
    return a2.find_browser()


def print_pdf(browser):
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html())
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--print-to-pdf=" + OUT_PDF,
                    "file:///" + OUT_HTML.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_pages():
    """Page of every heading, read back from the PDF (pages 1-2: cover and contents)."""
    try:
        raw = subprocess.run(["pdftotext", "-enc", "UTF-8", OUT_PDF, "-"], check=True,
                             stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    except Exception as ex:
        print("page numbers skipped:", ex)
        return
    pages = [re.sub(r"\s+", " ", p) for p in raw.split("\f")]
    for _, title in a2.TOC:
        for i, page in enumerate(pages):
            if i >= 2 and title in page:
                a2.PAGES[title] = i + 1
                break


def write_screenshot_readme():
    missing = set(MISSING)
    lines = ["# Screenshots for the Assignment 3 report", "",
             "_Generated by `build_report.py`. Do not edit by hand._", "",
             "The report already shows every statement's response as text (recorded by `capture_responses.py`). "
             "These %d Workbench screenshots are the evidence that the statements were run in MySQL Workbench: "
             "about one per handout requirement, not one per statement." % len(SHOT_PLAN), "",
             "## How to take them", "",
             "1. In Workbench, open each SQL file and run the whole script (lightning-bolt button). For task7.sql "
             "and task8.sql, first turn on *Edit > Preferences > SQL Editor > Continue SQL script execution on "
             "errors*, because some statements fail on purpose.",
             "2. Run the files in this order on an empty `ep_sourcer` schema: task3.sql, task4.sql, "
             "SRC/load_data.sql, SRC/check_data.sql, task6.sql, task7.sql, task8.sql.",
             "3. **Action Output** (bottom panel) lists the response of every statement in the script. One "
             "screenshot of it covers a whole file. If it needs scrolling, save the extra parts as "
             "`<name>_2.png`, `<name>_3.png`, and the report embeds them in order.",
             "4. **Result grids**: each SELECT opens a result tab. Click the tab you need and capture the query "
             "together with its grid.",
             "5. Save each PNG here with exactly the name below, then run `python build_report.py`.", "",
             "## Checklist", "",
             "| | File | Task | What to capture |", "|---|---|---|---|"]
    for name, task, what in SHOT_PLAN:
        lines.append("| %s | `%s.png` | %s | %s |" % ("[ ]" if name + ".png" in missing else "[x]", name, task, what))
    lines += ["", "Still missing: %d of %d." % (len(missing), len(SHOT_PLAN))]
    with open(os.path.join(SHOTS, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    os.makedirs(SHOTS, exist_ok=True)
    browser = find_browser()
    if not browser:
        with open(OUT_HTML, "w", encoding="utf-8") as f:
            f.write(build_html())
        print("No Chrome/Edge found: open the HTML and print to PDF manually.")
    else:
        print_pdf(browser)      # pass 1: lay out
        find_pages()
        print_pdf(browser)      # pass 2: contents list with page numbers
        print("wrote", OUT_PDF)
    write_screenshot_readme()
    print("wrote", OUT_HTML)
    print("%d of %d screenshots still missing (placeholders shown); checklist in screenshots/README.md"
          % (len(set(MISSING)), len(SHOT_PLAN)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
