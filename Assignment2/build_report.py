# -*- coding: utf-8 -*-
"""Builds the Assignment 2 report: SVG diagrams, HTML, PDF (headless Chrome) and an editable .docx (Word).

Run:  python build_report.py
The schema is defined once in RELS; the relation listing, FK tables, FD diagrams
and BCNF table are all generated from it so names stay consistent.
NOTE: every run overwrites the .pdf and .docx.
"""
import html
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIAG = os.path.join(HERE, "diagrams")
BASE = "AISE3309-Assignment02_Group6"
OUT_HTML = os.path.join(HERE, BASE + ".html")
OUT_PDF = os.path.join(HERE, BASE + ".pdf")
OUT_DOCX = os.path.join(HERE, BASE + ".docx")

MEMBERS = [
    ("Shaan Wrench", "251422184"),
    ("Mats Leis", "251409940"),
    ("Ayman Hossain", "251430600"),
    ("Samuel Huang", "251418742"),
    ("Anish Jami", "251419182"),
]

# Team Contribution Efforts: short bullets per member. Edit so each entry matches what the member did.
REVIEW_LINE = ("Took part in the group review of the full draft and helped correct the issues it "
               "found across Tasks 1 to 3.")
CONTRIB = {
    "Shaan Wrench": [
        "Task 3.3.1: assessed the schema for flaws, redundancy and anomalies, listed the functional "
        "dependencies and made the FD diagrams and the 1NF/2NF/3NF argument for each of the 12 relations.",
        REVIEW_LINE,
    ],
    "Mats Leis": [
        "Task 2: did the ER-to-relational transformation, wrote the 12 relations with their primary, "
        "alternate and foreign keys and derived attributes, and made the referential integrity tables and diagram (2.1 to 2.4).",
        "Compiled the report and diagrams into one document.",
        REVIEW_LINE,
    ],
    "Ayman Hossain": [
        "Task 1: defined the relationship types, multiplicities and participation, the Enhanced ER features "
        "(specialization, composition) and the constraints and assumptions (1.2 and 1.3).",
        REVIEW_LINE,
    ],
    "Samuel Huang": [
        "Task 1: defined the 7 entity types of the ER diagram, their attributes and identifiers (1.1), and "
        "documented the changes from the Assignment 1 data requirements (1.4).",
        REVIEW_LINE,
    ],
    "Anish Jami": [
        "Task 3.3.2 and 3.3.3: evaluated the candidates for combining relations, did the BCNF evaluation and "
        "the merged BOMLine analysis, and wrote the anticipated-query justification against the Assignment 1 functions.",
        REVIEW_LINE,
    ],
}

FONT = "Segoe UI, Arial, Helvetica, sans-serif"
esc = html.escape
PARTKEY = ["ManufacturerName", "Manufacturer_PartNum"]
BOMKEY = ["CustomerEmail", "BOM_name"]
LISTKEY = ["DistributorName", "Distributor_PartNum"]

# ----------------------------------------------------------------------------
# Schema (single source of truth)
# fks: (columns, referenced relation, referenced columns, ON DELETE action, reason)
# ----------------------------------------------------------------------------
RELS = [
    dict(
        name="Customer",
        attrs=["Email", "Username", "Password", "FirstName", "LastName", "HouseAddress",
               "UnitNum", "City", "Province", "Country", "PostCode"],
        pk=["Email"], aks=[["Username"]], fks=[], derived=[],
        fds=[(["Email"], "rest"), (["Username"], "rest")],
        nf2="Both candidate keys (Email and Username) are single attributes, so no partial dependency is possible.",
        nf3="The only determinants are Email (PK) and Username (AK), and both are superkeys. No non-key "
            "attribute determines another (see the customer address issue above).",
    ),
    dict(
        name="Part",
        attrs=PARTKEY + ["Name", "Description", "Category", "Length", "Width", "Height", "Datasheet_link"],
        pk=PARTKEY, aks=[], fks=[],
        derived=["/AvgStarRating = AVG(Review.StarRating) over the part's reviews (no value when the part has no review)"],
        fds=[(PARTKEY, "rest")],
        nf2="The non-key attributes describe one specific part. A manufacturer makes many parts, and "
            "another manufacturer can use the same part number, so neither key attribute alone determines them.",
        nf3="Category does not determine Name, the dimensions or the datasheet, and two parts "
            "can share a Name. The only determinant is the key.",
    ),
    dict(
        name="Distributor",
        attrs=["Name", "Website", "ShippingFee"],
        pk=["Name"], aks=[["Website"]], fks=[], derived=[],
        fds=[(["Name"], "rest"), (["Website"], "rest")],
        nf2="Both candidate keys (Name and Website) are single attributes, so no partial dependency is possible.",
        nf3="Website determines Name and ShippingFee, but Website is a candidate key (no two distributors "
            "share a website), so its determinant is a superkey.",
    ),
    dict(
        name="Listing",
        attrs=LISTKEY + PARTKEY + ["Packaging", "UnitPrice", "StockQuantity", "EstShipTime", "LastUpdated"],
        pk=LISTKEY,
        aks=[["DistributorName"] + PARTKEY + ["Packaging"]],
        fks=[(["DistributorName"], "Distributor", ["Name"], "CASCADE",
              "Composition: a distributor's listings are removed with the distributor."),
             (PARTKEY, "Part", PARTKEY, "RESTRICT",
              "A part that is still offered cannot be deleted.")],
        derived=[],
        fds=[(LISTKEY, "rest"), (["DistributorName"] + PARTKEY + ["Packaging"], "rest")],
        nf2="Checked against both candidate keys. A distributor part number (SKU) is unique only within "
            "its distributor, so price, stock, shipping time and the part offered need the whole primary key. "
            "For the alternate key, one distributor sells the same part as cut tape and as a reel at different "
            "prices and stock levels, so the distributor and the part without the packaging do not determine them, "
            "and neither does any other proper subset. No attribute depends on a proper subset of either key.",
        nf3="UnitPrice, StockQuantity, EstShipTime and LastUpdated are independent of each "
            "other. Both determinants are candidate keys, so both are superkeys.",
    ),
    dict(
        name="ShoppingCart",
        attrs=["CustomerEmail", "Date_created"],
        pk=["CustomerEmail"], aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"], "CASCADE",
              "Composition: the cart is removed with its customer.")],
        derived=["/Subtotal = SUM(CartLine.Quantity × Listing.UnitPrice); 0 for an empty cart",
                 "/ShippingPrice = SUM(Distributor.ShippingFee) over the distinct distributors in the cart; 0 for an empty cart",
                 "/TotalPrice = /Subtotal + /ShippingPrice (before tax)"],
        fds=[(["CustomerEmail"], "rest")],
        nf2="Single-attribute key, so no partial dependency is possible.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="BOM",
        attrs=BOMKEY + ["Date_created"],
        pk=BOMKEY, aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"], "CASCADE",
              "Composition: a customer's BOMs are removed with the customer.")],
        derived=["/NumberOfParts = COUNT of the BOM's BOMLine rows",
                 "/UnpricedParts = COUNT of the BOM's BOMLine rows that have no selected listing",
                 "/TotalCost = SUM(BOMLine.Quantity × Listing.UnitPrice) over the lines that have a selected listing. "
                 "Parts only, without shipping or tax. It is the complete cost of the BOM only when /UnpricedParts = 0; "
                 "otherwise it is shown as a partial total"],
        fds=[(BOMKEY, "rest")],
        nf2="Date_created belongs to one named BOM of one customer. A customer has many BOMs and "
            "a name can be reused by other customers, so neither key attribute alone determines it.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="SharedProject",
        attrs=BOMKEY + ["Title", "Description", "Date_shared"],
        pk=BOMKEY, aks=[["CustomerEmail", "Title"]],
        fks=[(BOMKEY, "BOM", BOMKEY, "CASCADE",
              "Specialization: the subclass row is removed with its BOM.")],
        derived=[],
        fds=[(BOMKEY, "rest"), (["CustomerEmail", "Title"], "rest")],
        nf2="Title, Description and Date_shared describe one shared BOM, which is identified "
            "only by the whole primary key. For the alternate key (CustomerEmail, Title), different customers "
            "can use the same title, so Title alone determines nothing, and CustomerEmail alone does not either, "
            "because a customer can share several projects.",
        nf3="(CustomerEmail, Title) determines the other attributes, but it is a candidate key, so it is a superkey. "
            "Description and Date_shared determine nothing.",
    ),
    dict(
        name="PartAlternative",
        attrs=["Part1_ManufacturerName", "Part1_PartNum", "Part2_ManufacturerName", "Part2_PartNum"],
        pk=["Part1_ManufacturerName", "Part1_PartNum", "Part2_ManufacturerName", "Part2_PartNum"], aks=[],
        fks=[(["Part1_ManufacturerName", "Part1_PartNum"], "Part", PARTKEY, "CASCADE",
              "The pair has no meaning once either part is gone."),
             (["Part2_ManufacturerName", "Part2_PartNum"], "Part", PARTKEY, "CASCADE",
              "The pair has no meaning once either part is gone.")],
        derived=[], fds=[],
        nf2="All-key relation: there are no non-key attributes.",
        nf3="All-key relation: there are no non-key attributes.",
    ),
    dict(
        name="BOMLine",
        attrs=BOMKEY + PARTKEY + ["Quantity"],
        pk=BOMKEY + PARTKEY, aks=[],
        fks=[(BOMKEY, "BOM", BOMKEY, "CASCADE", "A BOM's lines are removed with the BOM."),
             (PARTKEY, "Part", PARTKEY, "RESTRICT", "A part that is used in a BOM cannot be deleted.")],
        derived=[],
        fds=[(BOMKEY + PARTKEY, "rest")],
        nf2="Quantity is how many of one part one BOM needs. It changes with the BOM and with "
            "the part, so it depends on the whole key.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="BOMSelection",
        attrs=BOMKEY + LISTKEY,
        pk=BOMKEY + LISTKEY, aks=[],
        fks=[(BOMKEY, "BOM", BOMKEY, "CASCADE", "A BOM's selections are removed with the BOM."),
             (LISTKEY, "Listing", LISTKEY, "CASCADE",
              "When a listing is withdrawn the line returns to \"no supplier selected\".")],
        derived=[], fds=[],
        nf2="All-key relation: there are no non-key attributes.",
        nf3="All-key relation: there are no non-key attributes.",
    ),
    dict(
        name="CartLine",
        attrs=["CustomerEmail"] + LISTKEY + ["Quantity"],
        pk=["CustomerEmail"] + LISTKEY, aks=[],
        fks=[(["CustomerEmail"], "ShoppingCart", ["CustomerEmail"], "CASCADE",
              "A cart's lines are removed with the cart."),
             (LISTKEY, "Listing", LISTKEY, "CASCADE",
              "A withdrawn listing can no longer be bought, so it leaves every cart.")],
        derived=[],
        fds=[(["CustomerEmail"] + LISTKEY, "rest")],
        nf2="Quantity is how many units of one listing one cart holds, so it depends on the "
            "whole key.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="Review",
        attrs=["CustomerEmail"] + PARTKEY + ["ReviewText", "StarRating"],
        pk=["CustomerEmail"] + PARTKEY, aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"], "CASCADE",
              "A customer's reviews are removed with the account."),
             (PARTKEY, "Part", PARTKEY, "CASCADE", "Reviews of a removed part are removed.")],
        derived=[],
        fds=[(["CustomerEmail"] + PARTKEY, "rest")],
        nf2="A customer reviews many parts and a part has many reviewers, so the "
            "text and the rating depend on the whole key.",
        nf3="ReviewText does not determine StarRating, or the reverse.",
    ),
]
REL = {r["name"]: r for r in RELS}


def resolved_fds(r):
    out = []
    for det, dep in r["fds"]:
        if dep == "rest":
            dep = [a for a in r["attrs"] if a not in det]
        out.append((det, dep))
    return out


# ----------------------------------------------------------------------------
# SVG helpers
# ----------------------------------------------------------------------------
def svg_wrap(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
            'font-family="%s">\n'
            '<defs><marker id="ah" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto">'
            '<path d="M0,0 L9,4 L0,8 z" fill="#000"/></marker></defs>\n'
            '<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>\n%s\n</svg>'
            % (w, h, w, FONT, w, h, body))


def text(x, y, s, size=13, anchor="start", weight="normal", style="normal", fill="#000", deco=""):
    d = ' text-decoration="%s"' % deco if deco else ""
    return ('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" font-weight="%s" '
            'font-style="%s" fill="%s"%s>%s</text>' % (x, y, size, anchor, weight, style, fill, d, esc(s)))


def poly(points, dash=False, marker=False):
    pts = " ".join("%.1f,%.1f" % p for p in points)
    extra = ' stroke-dasharray="5,4"' if dash else ""
    if marker:
        extra += ' marker-end="url(#ah)"'
    return '<polyline points="%s" fill="none" stroke="#000" stroke-width="1.3"%s/>' % (pts, extra)


# ----------------------------------------------------------------------------
# Figure 1: ER diagram (UML database notation)
# ----------------------------------------------------------------------------
ROW, HDR, PAD = 19, 32, 8


def ent_h(n):
    return HDR + PAD + ROW * n


def entity(x, y, w, name, rows):
    h = ent_h(len(rows))
    s = ['<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#000" stroke-width="1.4"/>' % (x, y, w, h),
         '<rect x="%d" y="%d" width="%d" height="%d" fill="#dce9f7" stroke="#000" stroke-width="1.4"/>' % (x, y, w, HDR),
         text(x + w / 2, y + 22, name, 16, "middle", "bold")]
    for i, (t, ind) in enumerate(rows):
        s.append(text(x + (26 if ind else 10), y + HDR + 18 + ROW * i, t, 14))
    return "\n".join(s)


def attr_box(x, y, w, rows):
    h = 8 + 18 * len(rows)
    s = ['<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#000" stroke-width="1" stroke-dasharray="5,4"/>' % (x, y, w, h)]
    for i, t in enumerate(rows):
        s.append(text(x + 8, y + 18 + 18 * i, t, 13))
    return "\n".join(s)


def diamond_down(cx, y):
    """Filled composition diamond hanging below (cx, y)."""
    return '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#000"/>' % (
        cx, y, cx + 7, y + 11, cx, y + 22, cx - 7, y + 11)


def diamond_left(x, cy):
    """Filled composition diamond to the left of (x, cy)."""
    return '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#000"/>' % (
        x, cy, x - 11, cy - 7, x - 22, cy, x - 11, cy + 7)


def build_erd():
    b, e = [], []
    M = 13

    cust_rows = [("Email {PK}", 0), ("Username {AK}", 0), ("Password", 0),
                 ("Name", 0), ("FirstName", 1), ("LastName", 1),
                 ("BillingAddress", 0), ("HouseAddress", 1), ("UnitNum", 1), ("City", 1),
                 ("Province", 1), ("Country", 1), ("PostCode", 1)]
    bom_rows = [("BOM_name {PPK}", 0), ("Date_created", 0), ("/NumberOfParts", 0),
                ("/UnpricedParts", 0), ("/TotalCost", 0)]
    sp_rows = [("Title {AK}", 0), ("Description", 0), ("Date_shared", 0)]
    cart_rows = [("Date_created", 0), ("/Subtotal", 0), ("/ShippingPrice", 0), ("/TotalPrice", 0)]
    dist_rows = [("Name {PK}", 0), ("Website {AK}", 0), ("ShippingFee", 0)]
    list_rows = [("Distributor_PartNum {PPK}", 0), ("Packaging", 0), ("UnitPrice", 0), ("StockQuantity", 0),
                 ("EstShipTime", 0), ("LastUpdated", 0)]
    part_rows = [("ManufacturerName {PK}", 0), ("Manufacturer_PartNum {PK}", 0), ("Name", 0),
                 ("Description", 0), ("Category", 0), ("Dimensions", 0), ("Length", 1), ("Width", 1),
                 ("Height", 1), ("Datasheet_link", 0), ("/AvgStarRating", 0)]

    cb = 30 + ent_h(len(cust_rows))            # Customer bottom
    bb = 410 + ent_h(len(bom_rows))            # BOM bottom
    bom_mid = 410 + ent_h(len(bom_rows)) / 2.0
    kb = 410 + ent_h(len(cart_rows))           # cart bottom
    lb = 670 + ent_h(len(list_rows))           # listing bottom
    sp_y = int(bom_mid - ent_h(len(sp_rows)) / 2.0)
    dist_y = 680
    dist_mid = dist_y + ent_h(len(dist_rows)) / 2.0

    e.append(entity(440, 30, 260, "Customer", cust_rows))
    e.append(entity(300, 410, 200, "BOM", bom_rows))
    e.append(entity(20, sp_y, 190, "SharedProject", sp_rows))
    e.append(entity(570, 410, 200, "ShoppingCart", cart_rows))
    e.append(entity(900, dist_y, 170, "Distributor", dist_rows))
    e.append(entity(570, 670, 220, "Listing", list_rows))
    e.append(entity(300, 890, 240, "Part", part_rows))

    # Creates: Customer 1..1 -- 0..* BOM (identifying, composition)
    b.append(poly([(470, cb), (470, 410)]))
    b.append(diamond_down(470, cb))
    b.append(text(482, cb + 20, "1..1", M))
    b.append(text(482, cb + 52, "Creates ▼", M, style="italic"))
    b.append(text(478, 403, "0..*", M))

    # Owns: Customer 1..1 -- 0..1 ShoppingCart (identifying, composition)
    b.append(poly([(670, cb), (670, 410)]))
    b.append(diamond_down(670, cb))
    b.append(text(682, cb + 20, "1..1", M))
    b.append(text(682, cb + 52, "Owns ▼", M, style="italic"))
    b.append(text(678, 403, "0..1", M))

    # Reviews: Customer 0..* -- 0..* Part, attributes ReviewText, StarRating
    b.append(poly([(700, 120), (1095, 120), (1095, 1105), (540, 1105)]))
    b.append(text(706, 112, "0..*", M))
    b.append(text(890, 112, "Reviews ►", M, "middle", style="italic"))
    b.append(text(546, 1099, "0..*", M))
    b.append(attr_box(950, 300, 130, ["ReviewText", "StarRating"]))
    b.append(poly([(1095, 322), (1080, 322)], dash=True))

    # Specialization: BOM (superclass) <|-- SharedProject (subclass), {Optional}
    b.append(poly([(300, bom_mid), (210, bom_mid)]))
    b.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#fff" stroke="#000" stroke-width="1.3"/>'
             % (286, bom_mid, 264, bom_mid - 12, 264, bom_mid + 12))
    b.append(text(255, bom_mid + 34, "{Optional}", M, "middle"))

    # Contains: BOM 0..* -- 0..* Part, attribute Quantity
    b.append(poly([(400, bb), (400, 890)]))
    b.append(text(392, bb + 17, "0..*", M, "end"))
    b.append(text(392, 660, "Contains ▼", M, "end", style="italic"))
    b.append(text(392, 882, "0..*", M, "end"))
    b.append(attr_box(285, 747, 82, ["Quantity"]))
    b.append(poly([(400, 760), (367, 760)], dash=True))

    # Selects: BOM 0..* -- 0..* Listing
    b.append(poly([(500, 495), (535, 495), (535, 715), (570, 715)]))
    b.append(text(505, 489, "0..*", M))
    b.append(text(543, 580, "Selects ▼", M, style="italic"))
    b.append(text(541, 709, "0..*", M))

    # Holds: ShoppingCart 0..* -- 0..* Listing, attribute Quantity
    b.append(poly([(670, kb), (670, 670)]))
    b.append(text(678, kb + 17, "0..*", M))
    b.append(text(662, 640, "Holds ▼", M, "end", style="italic"))
    b.append(text(678, 663, "0..*", M))
    b.append(attr_box(705, 588, 82, ["Quantity"]))
    b.append(poly([(670, 601), (705, 601)], dash=True))

    # Publishes: Distributor 1..1 -- 0..* Listing (identifying, composition)
    b.append(poly([(900, dist_mid), (790, dist_mid)]))
    b.append(diamond_left(900, dist_mid))
    b.append(text(872, dist_mid - 10, "1..1", M, "end"))
    b.append(text(845, dist_mid + 20, "◄ Publishes", M, "middle", style="italic"))
    b.append(text(796, dist_mid - 6, "0..*", M))

    # Offers: Listing 0..* -- 1..1 Part
    b.append(poly([(670, lb), (670, 990), (540, 990)]))
    b.append(text(678, lb + 17, "0..*", M))
    b.append(text(662, 905, "Offers ▼", M, "end", style="italic"))
    b.append(text(546, 984, "1..1", M))

    # AlternativeTo: Part 0..* -- 0..* Part (recursive)
    b.append(poly([(300, 960), (235, 960), (235, 1060), (300, 1060)]))
    b.append(text(267, 954, "0..*", M, "middle"))
    b.append(text(267, 1077, "0..*", M, "middle"))
    b.append(text(227, 1014, "AlternativeTo", M, "end", style="italic"))

    # Legend
    lx, ly = 715, 836
    lines = [
        "{PK} primary key     {AK} alternate key",
        "Two {PK} attributes form one composite key",
        "{PPK} partial key of a weak entity",
        "/Attr   derived attribute",
        "Indented attributes are parts of a composite",
        "0..*   multiplicity (min..max)",
        "Dashed box: attributes of the relationship",
    ]
    leg = ['<rect x="%d" y="%d" width="360" height="%d" fill="#fafafa" stroke="#666" stroke-width="1"/>'
           % (lx, ly, 46 + 20 * len(lines) + 62),
           text(lx + 12, ly + 22, "Notation", 14, weight="bold")]
    for i, t in enumerate(lines):
        leg.append(text(lx + 12, ly + 46 + 20 * i, t, 13))
    yy = ly + 46 + 20 * len(lines) + 2
    leg.append(diamond_down(lx + 22, yy - 14))
    leg.append(text(lx + 40, yy + 2, "Composition (identifying relationship)", 13))
    yy += 26
    leg.append('<polygon points="%d,%d %d,%d %d,%d" fill="#fff" stroke="#000" stroke-width="1.3"/>'
               % (lx + 32, yy - 4, lx + 12, yy - 14, lx + 12, yy + 6))
    leg.append(text(lx + 40, yy + 1, "Specialization, points to the superclass", 13))

    return svg_wrap(1115, 890 + ent_h(len(part_rows)) + 14, "\n".join(e + b + leg))


# ----------------------------------------------------------------------------
# Figure 2: referential integrity (FK -> PK)
# ----------------------------------------------------------------------------
def build_fk():
    BW, BH = 150, 36
    pos = {
        "Customer": (200, 20), "Distributor": (480, 20),
        "ShoppingCart": (100, 190), "BOM": (290, 190), "Listing": (480, 190),
        "Part": (700, 190), "Review": (910, 190),
        "SharedProject": (100, 360), "BOMLine": (290, 360), "BOMSelection": (480, 360),
        "CartLine": (670, 360), "PartAlternative": (880, 360),
    }
    s = []
    seen = {}
    for r in RELS:
        for fk in r["fks"]:
            src, tgt = r["name"], fk[1]
            sx, sy = pos[src]
            tx, ty = pos[tgt]
            k = seen.get((src, tgt), 0)
            seen[(src, tgt)] = k + 1
            if sy == ty:  # same row: horizontal
                if sx < tx:
                    s.append(poly([(sx + BW / 2, sy + BH / 2), (tx - BW / 2, ty + BH / 2)], marker=True))
                else:
                    s.append(poly([(sx - BW / 2, sy + BH / 2), (tx + BW / 2, ty + BH / 2)], marker=True))
                continue
            if src == "PartAlternative":
                off = -10 + 20 * k
                s.append(poly([(sx + off, sy), (tx + 30 + off, ty + BH)], marker=True))
                continue
            off = max(-60, min(60, (sx - tx) * 0.14))
            s.append(poly([(sx - off * 0.5, sy), (tx + off, ty + BH)], marker=True))
    for name, (cx, cy) in pos.items():
        s.append('<rect x="%.1f" y="%d" width="%d" height="%d" rx="3" fill="#dce9f7" stroke="#000" stroke-width="1.3"/>'
                 % (cx - BW / 2, cy, BW, BH))
        s.append(text(cx, cy + 23, name, 14, "middle", "bold"))
    return svg_wrap(1005, 415, "\n".join(s))


# ----------------------------------------------------------------------------
# FD diagrams
# ----------------------------------------------------------------------------
def build_fd(attrs, pk, fds):
    FS, CH, CW, LANE = 12, 26, 6.7, 22
    x = 44
    cells = {}
    s = []
    for a in attrs:
        w = len(a) * CW + 16
        is_pk = a in pk
        s.append('<rect x="%.1f" y="2" width="%.1f" height="%d" fill="%s" stroke="#000" stroke-width="1.1"/>'
                 % (x, w, CH, "#dce9f7" if is_pk else "#fff"))
        s.append(text(x + w / 2, 2 + 18, a, FS, "middle", "bold" if is_pk else "normal",
                      deco="underline" if is_pk else ""))
        cells[a] = (x, w)
        x += w
    width = x + 6
    n = len(fds)
    base = 2 + CH
    for i, (det, dep) in enumerate(fds):
        ly = base + LANE * (i + 1)
        shift = (i - (n - 1) / 2.0) * 12
        xs = []
        col = ["#0b4ea2", "#b03a2e", "#1e7d34"][i % 3]
        ln = '<polyline points="%.1f,%.1f %.1f,%.1f" fill="none" stroke="' + col + '" stroke-width="1.3"/>'
        for a in det:
            cx = cells[a][0] + cells[a][1] / 2 + shift
            xs.append(cx)
            s.append(ln % (cx, base, cx, ly))
            s.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' % (cx, base + 1, col))
        for a in dep:
            cx = cells[a][0] + cells[a][1] / 2 + shift
            xs.append(cx)
            s.append(ln % (cx, ly, cx, base + 6))
            s.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s"/>'
                     % (cx, base + 1, cx - 3.5, base + 9, cx + 3.5, base + 9, col))
        s.append(ln % (min(xs), ly, max(xs), ly))
        s.append(text(4, ly + 4, "FD%d" % (i + 1), FS, weight="bold", fill=col))
    height = base + LANE * n + 12
    if not fds:
        s.append(text(44, base + 20, "All-key relation: the only FDs are trivial.", FS, style="italic"))
        height = base + 30
    return svg_wrap(int(width), int(height), "\n".join(s))


# ----------------------------------------------------------------------------
# HTML pieces
# ----------------------------------------------------------------------------
WORD = False   # True while building the HTML that Word converts to .docx
PAGES = {}     # heading text -> page number (filled after the first PDF pass)
TOC = []       # (level, heading text)
KEEP = ' style="page-break-after:avoid"'


def svg_size(name):
    s = open(os.path.join(DIAG, name + ".svg"), encoding="utf-8").read()
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', s)
    return int(m.group(1)), int(m.group(2))


def fig(name):
    """Inline SVG for the PDF; PNG <img> for the Word version."""
    if not WORD:
        return open(os.path.join(DIAG, name + ".svg"), encoding="utf-8").read()
    w, h = svg_size(name)
    dw = min(640, int(w * 0.85))
    png = os.path.join(DIAG, "png", name + ".png").replace("\\", "/")
    return '<img src="file:///%s" width="%d" height="%d">' % (png, dw, int(h * dw / w))


def h2(num, title, pb=True):
    TOC.append((1, "%s %s" % (num, title)))
    brk = ' style="page-break-before:always"' if (pb and WORD) else ""
    return '<h2 class="sec%s"%s>%s&nbsp; %s</h2>' % (" pb" if (pb and not WORD) else "", brk, num, esc(title))


def h3(num, title, pb=False):
    TOC.append((2, "%s %s" % (num, title)))
    return '<h3%s>%s&nbsp; %s</h3>' % (' class="pb"' if pb else "", num, esc(title))


def table(headers, rows, widths=None):
    out = ['<table width="100%" style="width:100%">']
    if widths:
        out.append("<colgroup>" + "".join('<col style="width:%s">' % w for w in widths) + "</colgroup>")
    out.append("<thead><tr>" + "".join("<th>%s</th>" % h for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def cols(c):
    return ", ".join(c)


def paren(c):
    return "(%s)" % cols(c) if len(c) > 1 else c[0]


def relation_block(r):
    parts = ['<span class="pk">%s</span>' % a if a in r["pk"] else a for a in r["attrs"]]
    keys = ['<b>Primary Key</b> %s' % cols(r["pk"])]
    keys += ['<b>Alternate Key</b> %s' % cols(ak) for ak in r["aks"]] or ['<b>Alternate Key</b> none']
    keys += ['<b>Foreign Key</b> %s <b>references</b> %s(%s)' % (cols(f[0]), f[1], cols(f[2]))
             for f in r["fks"]] or ['<b>Foreign Key</b> none']
    keys += ['<b>Derived</b> %s' % esc(d) for d in r["derived"]] or ['<b>Derived</b> none']
    k = KEEP if WORD else ""
    lines = ['<div class="relhead"%s><b>%s</b> (%s)</div>' % (k, r["name"], ", ".join(parts))]
    for i, t in enumerate(keys):
        lines.append('<div class="relkey"%s>%s</div>' % (k if i < len(keys) - 1 else "", t))
    return '<div class="rel">%s</div>' % "\n".join(lines)


def nf_block(r, idx):
    fds = resolved_fds(r)
    fd_txt = ["FD%d: %s → %s" % (i + 1, paren(det), cols(dep)) for i, (det, dep) in enumerate(fds)]
    if not fd_txt:
        fd_txt = ["No non-trivial FDs."]
    cks = [cols(r["pk"])] + [cols(a) for a in r["aks"]]
    k = KEEP if WORD else ""
    return ('<div class="nf"><h4>%d. %s</h4>'
            '<div class="fig"%s>%s</div>'
            '<p class="fdlist"%s>%s<br><b>Candidate keys:</b> %s</p>'
            '<ul class="tight"><li><b>1NF:</b> every attribute holds a single atomic value.</li>'
            '<li><b>2NF:</b> %s</li><li><b>3NF:</b> %s</li></ul></div>'
            % (idx, r["name"], k, fig("fd_%s" % r["name"]), k, "<br>".join(esc(t) for t in fd_txt),
               "; ".join("{%s}" % c for c in cks), esc(r["nf2"]), esc(r["nf3"])))


def toc_html():
    if WORD:
        return '<p>[[TOC]]</p>'
    out = []
    for lvl, t in TOC:
        out.append('<div class="tr l%d"><span>%s</span><span class="dots"></span><span>%s</span></div>'
                   % (lvl, esc(t), PAGES.get(t, "")))
    return "\n".join(out)


CSS = """
@page { size: Letter; margin: 0.75in 0.8in; @bottom-center { content: counter(page); font-family: 'Segoe UI', Arial, sans-serif; font-size: 9pt; } }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, Helvetica, sans-serif; font-size: 10pt; line-height: 1.4; color: #000; margin: 0; }
.cover { text-align: center; }
.banner { background: #1565c0; color: #fff; padding: 46px 10px 40px; font-size: 15pt; font-weight: 600; border-radius: 0 0 50% 50% / 0 0 26px 26px; }
.ctitle { color: #1565c0; font-size: 22pt; font-weight: 700; margin: 150px 0 40px; }
.csub1 { color: #1565c0; font-size: 18pt; font-weight: 700; margin: 0; }
.csub2 { color: #1565c0; font-size: 12pt; margin: 4px 0 40px; }
.cover table { width: 78%; margin: 0 auto; text-align: left; }
h2.sec { background: #cfe2f6; border-top: 3px solid #1e88e5; color: #1565c0; font-weight: 500; font-size: 14pt; padding: 4px 10px; margin: 22px 0 12px; break-after: avoid; }
h3 { color: #1565c0; font-size: 12pt; margin: 18px 0 6px; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 12px 0 4px; break-after: avoid; }
p { margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9pt; }
th, td { border: 1px solid #000; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #bdd7ee; text-align: center; }
tr { break-inside: avoid; }
.toctitle { color: #1565c0; text-align: center; font-size: 22pt; font-weight: 700; margin: 10px 0 24px; }
.tr { display: flex; align-items: baseline; margin: 5px 0; }
.tr.l1 { font-weight: 600; margin-top: 10px; }
.tr.l2 { margin-left: 26px; }
.dots { flex: 1; border-bottom: 1px dotted #000; margin: 0 6px; }
.fig { text-align: center; margin: 8px 0; break-inside: avoid; }
.fig svg { max-width: 100%; height: auto; }
.cap { text-align: center; font-size: 9pt; font-style: italic; margin: 2px 0 12px; }
.rel { margin: 9px 0; padding: 5px 9px; border-left: 3px solid #1e88e5; background: #f6f9fd; break-inside: avoid; }
.relhead { font-size: 10pt; }
.relkey { margin-left: 22px; font-size: 9pt; }
.pk { text-decoration: underline; font-weight: 600; }
.nf { break-inside: avoid; margin-bottom: 12px; }
.nf .fig { text-align: left; }
.fdlist { font-size: 9pt; margin: 2px 0; }
.expr { margin: 6px 0 6px 22px; font-weight: 600; }
ul.tight { margin: 4px 0 4px 0; padding-left: 20px; }
ul.tight li { margin: 1px 0; }
.pb { break-before: page; page-break-before: always; }
"""


def build_html():
    del TOC[:]
    erd = fig("erd_engineering_part_sourcer")
    fk = fig("schema_foreign_keys")
    fd_merged = fig("fd_BOMLine_merged_alternative")
    H = []
    # Word's HTML import drops the whole stylesheet if it meets a nested @page margin box
    css = re.sub(r"@page \{[^\n]*", "@page { size: Letter; margin: 0.75in 0.8in; }", CSS, count=1) if WORD else CSS
    H.append('<!doctype html><html lang="en"><head><meta charset="utf-8">'
             '<title>AISE 3309 Assignment 02 - Group 6</title><style>%s</style></head><body>' % css)

    # ---- cover
    H.append('<div class="cover"><div class="banner">Western Engineering<br>Electrical and Computer Engineering</div>'
             '<p class="ctitle">AISE 3309: Database Management Systems</p><p class="csub1">Assignment 02</p>'
             '<p class="csub2">Conceptual Model, Relational Schema and Schema Evaluation</p>')
    rows = "".join("<tr><td>%d.&nbsp; %s</td><td>%s</td></tr>" % (i + 1, n, sid)
                   for i, (n, sid) in enumerate(MEMBERS))
    H.append('<table><tr><td><b>Group #:</b></td><td>6 (Lab 2, AISE 3309A 002)</td></tr>'
             '<tr><td><b>Project Name:</b></td><td>Engineering Part Sourcer</td></tr>'
             '<tr><th style="width:50%">Team Member Name</th><th>Team Member ID</th></tr>' + rows + '</table></div>')

    # ---- toc placeholder (filled at the end, once all headings are known)
    H.append('<p class="toctitle" style="page-break-before:always">Table of Contents</p>')
    toc_at = len(H)
    H.append("")

    # ======================= Task 1
    H.append(h2("1.", "Task 1: Conceptual Model (ER Diagram)"))
    H.append('<p>Figure 1 is the conceptual model of the Engineering Part Sourcer in UML database notation. '
             'It has <b>7 entity types</b>: Customer, Part, Distributor, Listing, ShoppingCart, BOM and SharedProject.</p>')
    H.append('<div class="fig">%s</div><div class="cap">Figure 1. ER diagram of the Engineering Part Sourcer (UML database notation).</div>' % erd)

    H.append(h3("1.1", "Entity types and identifiers", pb=True))
    H.append('<p>An entity has its own identifier only where the real-world thing has one. '
             'The surrogate IDs from Assignment 1 (BOM ID, Cart_ID, Listing_ID, DistributorID) are removed.</p>')
    H.append(table(["Entity type", "Kind", "Identifier", "Why this identifier"], [
        ["Customer", "Strong", "Email {PK}; Username {AK}", "An account is registered with a unique email address. The system also rejects a username that is already taken."],
        ["Part", "Strong", "(ManufacturerName, Manufacturer_PartNum) {PK}", "A manufacturer part number is unique only within one manufacturer's products. Two manufacturers can both have a part \"1001\", so the manufacturer's name is part of the key."],
        ["Distributor", "Strong", "Name {PK}; Website {AK}", "Distributors are known by their company name (DigiKey, Mouser). Each distributor has exactly one website and no two distributors share one, so Website is also unique."],
        ["Listing", "Weak (owner: Distributor)", "Distributor_PartNum {PPK}", "A distributor's part number (SKU) is unique only inside that distributor's catalogue. Each packaging of a part (cut tape, reel, bulk) has its own SKU, so it is its own listing."],
        ["BOM", "Weak (owner: Customer)", "BOM_name {PPK}", "A customer names each BOM. Names are unique only per customer."],
        ["ShoppingCart", "Weak (owner: Customer)", "None", "A customer has at most one cart, so the owner identifies it."],
        ["SharedProject", "Subclass of BOM", "Inherited from BOM; Title {AK} per owner", "A shared project is a BOM that its owner has published. Titles are unique per customer, not across all customers: two users can each share a project called \"Line follower robot\", but one user cannot share two projects with the same title. In the relation the alternate key is (CustomerEmail, Title)."],
    ], ["14%", "17%", "25%", "44%"]))

    H.append(h3("1.2", "Relationship types"))
    H.append('<p>The multiplicity beside an entity is the number of its instances related to one instance at the other end.</p>')
    H.append(table(["Relationship", "Multiplicity", "Participation", "Attributes"], [
        ["Customer <i>Creates</i> BOM", "1..1 to 0..*", "BOM total (identifying); Customer partial", "None"],
        ["Customer <i>Owns</i> ShoppingCart", "1..1 to 0..1", "ShoppingCart total (identifying); Customer partial", "None"],
        ["Customer <i>Reviews</i> Part", "0..* to 0..*", "Partial on both sides", "ReviewText, StarRating"],
        ["Distributor <i>Publishes</i> Listing", "1..1 to 0..*", "Listing total (identifying); Distributor partial", "None"],
        ["Listing <i>Offers</i> Part", "0..* to 1..1", "Listing total; Part partial", "None"],
        ["Part <i>AlternativeTo</i> Part", "0..* to 0..*", "Partial on both sides (recursive)", "None"],
        ["BOM <i>Contains</i> Part", "0..* to 0..*", "Partial on both sides", "Quantity"],
        ["BOM <i>Selects</i> Listing", "0..* to 0..*", "Partial on both sides", "None"],
        ["ShoppingCart <i>Holds</i> Listing", "0..* to 0..*", "Partial on both sides", "Quantity"],
        ["BOM / SharedProject", "Specialization", "{Optional}: a BOM does not have to be shared", "Subclass adds Title, Description, Date_shared"],
    ], ["27%", "14%", "36%", "23%"]))

    H.append(h3("1.3", "Enhanced ER features, constraints and assumptions"))
    H.append('<ul class="tight">'
             '<li><b>Specialization.</b> SharedProject is a subclass of BOM. Participation is {Optional} because most BOMs stay private. '
             'There is one subclass, so a disjoint/overlapping constraint does not apply. The subclass inherits the BOM\'s owner and parts, '
             'so the customer who shared a project and the parts it uses are not recorded twice.</li>'
             '<li><b>Composition.</b> BOM and ShoppingCart are parts of a Customer, and Listing is part of a Distributor. They cannot exist without the owner and are deleted with it (section 2.4).</li>'
             '<li><b>Composite attributes.</b> Customer.Name, Customer.BillingAddress and Part.Dimensions.</li>'
             '<li><b>Derived attributes.</b> /AvgStarRating, /NumberOfParts, /UnpricedParts, /TotalCost, /Subtotal, /ShippingPrice and /TotalPrice (defined in Task 2).</li>'
             '</ul>')
    H.append('<p>Constraints that the diagram cannot show:</p>')
    H.append(table(["#", "Constraint"], [
        ["C1", "StarRating is an integer from 1 to 5. Every Quantity is greater than 0. UnitPrice, StockQuantity and ShippingFee are not negative."],
        ["C2", "A distributor has at most one listing for a given part in a given packaging. The same part can be listed several times by one distributor, once per packaging (for example cut tape and reel), and each of those listings has its own Distributor_PartNum, price and stock."],
        ["C3", "A BOM selects only listings of parts it contains, and at most one listing for each of those parts."],
        ["C4", "AlternativeTo is symmetric, and a part is not an alternative to itself."],
        ["C5", "A SharedProject's BOM contains at least one part at all times."],
        ["C6", "A customer reviews a part at most once. Purchases are completed on the distributor's own website, so the system does not record them and cannot check that the reviewer bought the part."],
        ["C7", "The part offered by a listing never changes. An offer for a different part is a new listing."],
    ], ["6%", "94%"]))
    H.append('<p>Assumptions about stored values:</p>')
    H.append('<ul class="tight">'
             '<li>All money values (UnitPrice, ShippingFee and the derived totals) are in Canadian dollars and exclude tax.</li>'
             '<li>Length, Width and Height are in millimetres. EstShipTime is in days.</li>'
             '<li>Packaging is the distributor\'s packaging name for the listing, such as Cut Tape, Tape &amp; Reel, Tray or Bulk.</li>'
             '<li>Customer.Password holds a salted hash of the password, never the password itself.</li>'
             '<li>ShoppingCart.Date_created is the date the cart was created, which is when its first item was added.</li>'
             '</ul>')

    H.append(h3("1.4", "Changes from the Assignment 1 data requirements"))
    H.append(table(["Assignment 1", "Problem", "This model"], [
        ["BOM ID, Cart_ID, Listing_ID, DistributorID", "Arbitrary surrogate identifiers", "Removed. Real identifiers or weak entities are used."],
        ["Part identified by Manufacturer_PartNum alone", "Part numbers are unique only within a manufacturer", "ManufacturerName added, and the key is (ManufacturerName, Manufacturer_PartNum)."],
        ["Part.Distributor", "Repeats what Listing records, and a part has many distributors", "Removed. Distributors are reached through Listing."],
        ["Distributor \"All parts\", ShoppingCart \"Parts\"", "Multi-valued attributes that are really relationships", "Publishes and Holds relationships."],
        ["Customer Reviews Distributor, with Distributor \"Customer reviews\" and /5-star rating", "The purchase happens on the distributor's website, outside the system. What customers can judge inside the system is the part they looked up and used.", "Customer Reviews Part. /AvgStarRating is a derived attribute of Part."],
        ["Listing Has Part", "\"Has\" does not say what the relationship means", "Renamed Listing Offers Part."],
        ["Listing.Quantity", "Same name as the relationship attribute Quantity", "Renamed StockQuantity."],
        ["ShoppingCart.Date_Added", "Unclear whether it is the date of the cart or of one item", "Renamed Date_created (date of the cart)."],
        ["/Shipping price with no source data", "A derived attribute needs stored data to be derived from", "Distributor.ShippingFee added (flat fee per order from that distributor)."],
        ["Project sharing (functional specification only)", "No entity stored a shared project", "SharedProject added as a subclass of BOM."],
        ["BOM maker \"select supplier listings\"", "No relationship recorded the chosen supplier, so /TotalCost could not be derived", "Selects relationship between BOM and Listing, and /UnpricedParts to show how complete /TotalCost is."],
    ], ["30%", "35%", "35%"]))

    # ======================= Task 2
    H.append(h2("2.", "Task 2: Relational Schema"))
    H.append(h3("2.1", "Transformation steps"))
    H.append(table(["Step", "ER construct", "Result"], [
        ["1. Strong entity types", "Customer, Part, Distributor", "One relation each. Composite attributes are replaced by their simple components (Name by 2, BillingAddress by 6, Dimensions by 3). Part has a composite PK."],
        ["2. Weak entity types", "Listing, BOM, ShoppingCart", "One relation each. The owner's PK is added as an FK, and the PK is the owner's PK plus the partial key. ShoppingCart has no partial key, so its PK is CustomerEmail."],
        ["3. 1:1 relationships", "Owns", "Already mapped in step 2: the FK CustomerEmail in ShoppingCart is also its PK, which enforces one cart per customer."],
        ["4. 1:* relationships", "Creates, Publishes, Offers", "The PK of the \"one\" side is posted to the \"many\" side. Creates and Publishes were mapped in step 2. Offers adds (ManufacturerName, Manufacturer_PartNum) to Listing, NOT NULL."],
        ["5. *:* relationships", "AlternativeTo, Contains, Selects, Holds, Reviews", "A new junction relation each: PartAlternative, BOMLine, BOMSelection, CartLine, Review. The PK is the combination of the two FKs, and relationship attributes become columns."],
        ["6. Multi-valued attributes", "None in the final ER diagram", "The multi-valued attributes of Assignment 1 were already modelled as relationships."],
        ["7. Specialization", "BOM / SharedProject, {Optional}", "Separate relations for superclass and subclass. SharedProject's PK is the BOM PK, which is also an FK to BOM."],
        ["Derived attributes", "Seven attributes marked /", "Not stored. Each is listed under its relation with the rule that computes it."],
    ], ["19%", "27%", "54%"]))

    H.append(h3("2.2", "Relations"))
    H.append('<p>Notation: <b>Relation</b> (attributes), with primary key attributes underlined, followed by the keys. '
             'FK attributes are named after the referenced relation where the original name would be ambiguous '
             '(CustomerEmail references Customer.Email, DistributorName references Distributor.Name).</p>')
    for r in RELS:
        H.append(relation_block(r))

    H.append(h3("2.3", "Referential integrity"))
    H.append('<p>Every foreign key references the complete primary key of an existing relation, and every FK column is NOT NULL. '
             'Each FK column has the same domain as the primary key column it references. '
             'The last column names the ER construct that the foreign key implements: all nine relationship types and the '
             'specialization of Figure 1 are preserved.</p>')
    er_of = {("Listing", "Distributor"): "Publishes", ("Listing", "Part"): "Offers",
             ("ShoppingCart", "Customer"): "Owns", ("BOM", "Customer"): "Creates",
             ("SharedProject", "BOM"): "Specialization",
             "PartAlternative": "AlternativeTo", "BOMLine": "Contains", "BOMSelection": "Selects",
             "CartLine": "Holds", "Review": "Reviews"}
    fk_rows = []
    for r in RELS:
        for f in r["fks"]:
            ok = "Yes" if f[2] == REL[f[1]]["pk"] else "NO"
            er = er_of.get((r["name"], f[1])) or er_of[r["name"]]
            fk_rows.append([r["name"], cols(f[0]), "%s(%s)" % (f[1], cols(f[2])), ok, er])
    assert len(set(row[4] for row in fk_rows)) == 10
    H.append(table(["Relation", "Foreign key", "References", "Full PK of target?", "Implements"], fk_rows,
                   ["14%", "30%", "30%", "11%", "15%"]))
    H.append('<div class="fig">%s</div><div class="cap">Figure 2. Referential integrity. Each arrow goes from a foreign key to the relation whose primary key it references.</div>' % fk)

    H.append(h3("2.4", "Delete rules and constraint maintenance"))
    H.append('<p>Every foreign key uses ON UPDATE CASCADE, so a changed email, distributor name or part key reaches all references. '
             'The delete rules below implement the compositions and the specialization of the ER diagram.</p>')
    act_rows = []
    for r in RELS:
        for f in r["fks"]:
            act_rows.append([r["name"], f[1], f[3], f[4]])
    H.append(table(["Relation", "References", "ON DELETE", "Reason"], act_rows, ["16%", "14%", "12%", "58%"]))
    H.append('<p>C1 and C4 are CHECK constraints (PartAlternative stores each pair once, with the Part1 key ordered before the Part2 key). '
             'C2 is the alternate key of Listing, and C6 is the primary key of Review. '
             'C3, C5 and C7 cannot be written as keys or CHECKs, so each operation that could break them is handled as follows:</p>')
    H.append(table(["Rule", "Operation", "Action"], [
        ["C3", "INSERT or UPDATE on BOMSelection", "Rejected unless the listing's part has a BOMLine in the same BOM and the BOM has no other selection for that part."],
        ["C3", "DELETE on BOMLine", "The BOM's selection for that part, if any, is deleted with the line."],
        ["C3, C7", "UPDATE of the part columns of Listing", "Rejected when made directly. A listing never changes its part, so an existing selection cannot start pointing at a different part. "
         "The one exception is the ON UPDATE CASCADE from Part when a part's own key is corrected: the listing still refers to the same part."],
        ["C3", "DELETE on Listing", "Its BOMSelection rows are removed by ON DELETE CASCADE. The line stays and counts in /UnpricedParts."],
        ["C5", "INSERT on SharedProject", "Rejected if the BOM has no BOMLine."],
        ["C5", "DELETE on BOMLine", "Rejected if it is the last line of a shared BOM. The owner must stop sharing the project first. "
         "This applies to deleting a line on its own: when the BOM or its customer is deleted, the lines and the SharedProject row are removed together by the cascades."],
    ], ["9%", "33%", "58%"]))

    # ======================= Task 3
    H.append(h2("3.", "Task 3: Schema Evaluation"))
    H.append(h3("3.3.1", "Schema flaws and 3NF"))
    H.append('<h4>Flaws, redundancy and anomalies</h4>')
    H.append('<p>We examined the schema for repeated facts and for insert, update and delete anomalies.</p>')
    H.append(table(["Issue", "Assessment", "Decision"], [
        ["Customer address", "In Canada a PostCode usually implies City and Province, which would be a transitive dependency. It is not a dependency in this system: customers can be in any country, postal code formats are not unique across countries, and one code can cover more than one municipality.", "Not treated as an FD. The address stays in Customer and is always read as a whole."],
        ["Derived values", "Storing /TotalCost, /Subtotal or /AvgStarRating would create a second copy that goes out of date whenever a price, quantity or review changes (update anomaly).", "None is stored. They are computed by queries or views."],
        ["Natural keys used as FKs", "Email, distributor Name and the part key appear in several relations. Changing one must change every reference.", "Accepted, because surrogate IDs are not allowed. The FKs use ON UPDATE CASCADE (2.4)."],
        ["PartAlternative", "A symmetric pair could be stored twice as (A, B) and (B, A), which is redundant and can become inconsistent.", "Each pair is stored once (C4)."],
        ["BOMLine and BOMSelection", "The link between a selection and its line is not a foreign key. It goes through the part of the listing, so C3 needs triggers on several operations.", "Accepted and specified in 2.4. Sections 3.3.2 and 3.3.3 explain why the two relations are not merged."],
        ["Shared project parts", "A separate part list per shared project would repeat the BOM's lines.", "Avoided by the specialization. A shared project uses its BOM's BOMLine rows."],
        ["Insert and delete anomalies", "A part can exist with no listing, a distributor with no listings, and a customer with no BOM or cart. Deleting the last listing of a part does not delete the part.", "No anomaly. Each fact is stored in one relation."],
    ], ["17%", "53%", "30%"]))

    H.append('<h4>Normalization of every relation</h4>')
    H.append('<p>Each diagram shows the relation\'s attributes (primary key shaded and underlined) and its functional dependencies. '
             'A dot marks a determinant attribute and an arrow points to each dependent attribute. The tests used are:</p>')
    H.append('<ul class="tight">'
             '<li><b>1NF:</b> every attribute holds a single atomic value.</li>'
             '<li><b>2NF:</b> no non-prime attribute depends on a proper subset of any candidate key.</li>'
             '<li><b>3NF:</b> for every non-trivial FD X → A, X is a superkey or A is a prime attribute.</li>'
             '</ul>'
             '<p>A prime attribute is one that belongs to some candidate key. The tests are applied to every candidate key, not only the primary key.</p>')
    for i, r in enumerate(RELS):
        H.append(nf_block(r, i + 1))
    H.append('<p><b>Result:</b> all 12 relations are in 1NF, 2NF and 3NF. There is no violation to resolve, so no relation is decomposed here.</p>')

    H.append(h3("3.3.2", "Opportunities for combining relations"))
    H.append('<p>Two relations can be combined without repeating rows when they describe the same things, which happens for 1:1 relationships, '
             'superclass/subclass pairs and relationship relations over the same entities. We found three candidates.</p>')
    H.append(table(["Candidate", "Combined without redundancy?", "Decision and query justification"], [
        ["Customer + ShoppingCart (1:1, same key)",
         "Yes. Date_created would become a nullable column of Customer and no row is repeated.",
         "<b>Rejected.</b> Sign-in reads Customer on every visit and never needs the cart. Cart queries join CartLine to Listing and do not need the customer's credentials or address. A customer with no cart would store a NULL, and CartLine's FK would have to point at Customer, which hides the rule that lines belong to a cart."],
        ["BOM + SharedProject (superclass/subclass, same key)",
         "Yes. Title, Description and Date_shared would become nullable columns of BOM.",
         "<b>Rejected.</b> The most common query on shared projects is browsing or searching all of them by title, and it reads only the small SharedProject relation. Opening a private BOM never needs the sharing columns. Most BOMs are private, so the merged relation would be mostly NULLs, and (CustomerEmail, Title) could not be a NOT NULL alternate key."],
        ["BOMLine + BOMSelection (a selection belongs to one line of the BOM)",
         "No. No row is repeated, since the merged relation is BOMLine with nullable DistributorName and Distributor_PartNum. But the part of the selected listing would then be stored both in the line and in Listing.",
         "<b>Rejected.</b> Merging would remove one join from the BOM cost query (BOMSelection), although Listing is still needed for UnitPrice. It would also let the key enforce \"one listing per line\". We still keep them separate: the merged relation is not in BCNF (3.3.3), the supplier choice is optional so two columns of a composite FK would be NULL on many lines, and the frequent BOM queries (open a BOM, upload a CSV, copy a shared project) read parts and quantities only."],
    ], ["22%", "30%", "48%"]))
    H.append('<p>No other pair can be combined. Every remaining pair is linked by a 1:* or *:* relationship, so merging would repeat the '
             'attributes of one side: Distributor with Listing would repeat Website and ShippingFee on every listing, Part with Listing would repeat the part description for every distributor, '
             'and BOM with BOMLine would repeat Date_created on every line.</p>')

    H.append(h3("3.3.3", "BCNF evaluation"))
    H.append('<p><b>Summary.</b> The final schema is entirely in BCNF: in all 12 relations every determinant is a candidate key, '
             'so nothing is decomposed. The only design we considered that is not in BCNF is a single BOMLine that also holds the chosen listing. '
             'We keep BOMLine (parts and quantities) and BOMSelection (chosen listings) separate instead. That keeps the schema in BCNF, '
             'stores the part of each listing only once, and avoids NULLs on lines with no supplier yet. The cost of this is one extra join through Listing, '
             'which the rest of this section shows to be correct.</p>')
    H.append('<p>A relation is in BCNF when the determinant of every non-trivial functional dependency is a superkey. '
             'The determinants below are the ones in the FD diagrams of 3.3.1.</p>')
    b_rows = []
    for r in RELS:
        fds = resolved_fds(r)
        keys = [r["pk"]] + r["aks"]
        if fds:
            assert all(d in keys for d, _ in fds), r["name"]
            dets = "; ".join(paren(d) for d, _ in fds)
            why = "Yes: " + ", ".join("PK" if d == r["pk"] else "AK" for d, _ in fds)
        else:
            dets = "None (all-key)"
            why = "Yes: no non-trivial FD"
        b_rows.append([r["name"], dets, why, "BCNF"])
    H.append(table(["Relation", "Determinants", "Every determinant a superkey?", "Result"], b_rows, ["15%", "52%", "23%", "10%"]))
    H.append('<p><b>All 12 relations are in BCNF, so no relation of the schema is decomposed.</b> Customer, Distributor, Listing and SharedProject each have two candidate keys. '
             'In every case both are determinants of the whole relation, so the overlapping keys in Listing (both contain DistributorName) and in SharedProject (both contain CustomerEmail) cause no violation.</p>')

    H.append('<h4>The design that would not be in BCNF</h4>')
    H.append('<p>The merge considered in 3.3.2 gives BOMLine (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum, Quantity, DistributorName, Distributor_PartNum):</p>')
    H.append('<div class="fig" style="text-align:left">%s</div><div class="cap">Figure 3. FDs of the rejected merged BOMLine. FD2 has a determinant that is not a superkey.</div>' % fd_merged)
    H.append('<ul class="tight">'
             '<li>FD1: (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum) → Quantity, DistributorName, Distributor_PartNum. The determinant is the key.</li>'
             '<li>FD2: (DistributorName, Distributor_PartNum) → ManufacturerName, Manufacturer_PartNum. A listing offers exactly one part. This determinant is not a superkey, so the relation is <b>not in BCNF</b>.</li>'
             '<li>It is still in 3NF, because the attributes on the right of FD2 belong to the key (they are prime).</li>'
             '</ul>')
    H.append('<p><b>Its BCNF decomposition.</b> Decomposing on FD2 gives:</p>'
             '<ul class="tight">'
             '<li>R1 (DistributorName, Distributor_PartNum, ManufacturerName, Manufacturer_PartNum)</li>'
             '<li>R2 (CustomerEmail, BOM_name, DistributorName, Distributor_PartNum, Quantity)</li>'
             '</ul>'
             '<p>This decomposition is lossless, because the common attributes (DistributorName, Distributor_PartNum) are the key of R1. '
             'R1 is a projection of Listing, so it would not need to be stored again. R2 does not fit the system, for two reasons. '
             'A line could exist only after a listing is chosen, but an uploaded BOM has parts and quantities with no supplier yet. '
             'And FD1 is not preserved: Quantity would be keyed by the listing, and nothing would stop a BOM from holding two listings of the same part.</p>')
    H.append('<p><b>What the schema does instead.</b> The schema never forms the merged relation. It maps the two relationships of the ER diagram separately: '
             'BOMLine for Contains (part and quantity) and BOMSelection for Selects (chosen listing). Both are in BCNF. '
             'These two relations are not by themselves a decomposition of the merged relation. They share only (CustomerEmail, BOM_name), '
             'so joining just the two would pair every part of a BOM with every selected listing of that BOM: a BOM with two parts and two selections would give four rows, two of them wrong. '
             'The pairing is recovered through Listing, which records the part of each listing:</p>'
             '<p class="expr">BOMLine ⟕ (BOMSelection ⋈ Listing)</p>'
             '<p>The inner join attaches its part to each selection. The left outer join is on (CustomerEmail, BOM_name, ManufacturerName, Manufacturer_PartNum), and it keeps the lines that have no selection. '
             'By C3 every selection matches exactly one line and a line matches at most one selection, so this expression returns exactly the rows of the merged relation, with nothing lost and no spurious row.</p>')
    H.append(table(["", "Merged BOMLine (3NF only)", "BOMLine + BOMSelection (BCNF, chosen)"], [
        ["Redundancy", "The part of the chosen listing is stored in BOMLine and again in Listing. A row could name a listing of a different part unless an extra check prevents it.", "The part of a listing is stored once, in Listing."],
        ["NULLs", "DistributorName and Distributor_PartNum are NULL until a supplier is chosen, and are part of a composite FK.", "None. A line with no chosen supplier has no BOMSelection row."],
        ["Constraint C3", "\"One listing per line\" is enforced by the key. \"The listing is for the line's part\" still needs a check.", "Both parts of C3 need triggers (2.4)."],
        ["Queries", "BOM cost: BOMLine ⋈ Listing (one join fewer).", "BOM cost: BOMLine ⟕ (BOMSelection ⋈ Listing), joined on key attributes. Listing the parts of a BOM or of a shared project reads BOMLine only in both designs."],
    ], ["14%", "43%", "43%"]))
    H.append('<p><b>Decision:</b> keep the BCNF design. The most frequent BOM operations (open a BOM, upload a BOM from CSV, copy a shared project) work on parts and quantities only and never touch the supplier choice. '
             'The price we accept is one extra join in the cost query, on indexed key columns, and the triggers listed in 2.4. In return no fact is stored twice and no column is NULL.</p>')

    H.append('<h4>Anticipated common queries and how the design serves them</h4>')
    H.append(table(["Query (Assignment 1 function)", "Relations used", "Why the design fits"], [
        ["Search parts by name, part number or keyword (Part Search)", "Part", "Part holds only seller-independent data, so one row per part is searched. It was not merged with Listing."],
        ["Compare offers for N units of a part (Price Match)", "Listing ⋈ Distributor", "All offers for a part are the Listing rows with its part key. A price or stock change updates one row."],
        ["Filter by category, dimensions, distributor, price, stock (Filter)", "Part ⋈ Listing", "Part attributes and Listing attributes are reached with one key join."],
        ["Open, edit or upload a BOM (BOM upload, BOM maker)", "BOM, BOMLine", "Lines are keyed by BOM and part, so the supplier choice is not involved (BCNF decision)."],
        ["BOM line costs, total and stock warnings (BOM maker)", "BOMLine ⟕ (BOMSelection ⋈ Listing)", "The outer join keeps lines with no supplier, so they are reported as unpriced instead of being left out of the total. Costs are computed from the single stored price of each listing, and LastUpdated shows how old that price is."],
        ["Cart subtotals grouped by distributor (Cart)", "CartLine ⋈ Listing ⋈ Distributor", "CartLine carries DistributorName in its key, so grouping needs no extra lookup. Kept apart from Customer (3.3.2)."],
        ["Sign in (Sign in)", "Customer", "One small row by Email or Username. No cart or BOM data is read."],
        ["Browse shared projects and copy their parts (Project Sharing)", "SharedProject, then BOMLine ⋈ Part", "Browsing reads only SharedProject (3.3.2). The parts come from the BOM's lines, with no second copy."],
        ["Part rating", "Review", "AVG(StarRating) grouped by the part key."],
        ["Alternative parts", "PartAlternative ⋈ Part", "Each pair is stored once and queried in both directions."],
    ], ["32%", "27%", "41%"]))

    # ======================= Contribution
    H.append(h2("4.", "Team Contribution Efforts"))
    c_rows = []
    for n, _ in MEMBERS:
        items = CONTRIB.get(n) or ["[to be completed]"]
        c_rows.append([n, '<ul class="tight">%s</ul>' % "".join("<li>%s</li>" % esc(i) for i in items)])
    H.append(table(["Team member", "Contribution"], c_rows, ["22%", "78%"]))
    H.append("</body></html>")
    H[toc_at] = toc_html()
    return "\n".join(H)


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
def find_browser():
    for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if os.path.exists(c):
            return c
    return None


def print_pdf(br):
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html())
    subprocess.run([br, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + OUT_PDF, "file:///" + OUT_HTML.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_pages():
    """Page number of every heading, read back from the PDF (pages 1-2 are cover and contents)."""
    try:
        raw = subprocess.run(["pdftotext", "-enc", "UTF-8", OUT_PDF, "-"], check=True,
                             stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    except Exception as ex:  # pdftotext missing: contents list without page numbers
        print("page numbers skipped:", ex)
        return
    pages = [re.sub(r"\s+", " ", p) for p in raw.split("\f")]
    for _, t in TOC:
        for i, p in enumerate(pages):
            if i >= 2 and t in p:
                PAGES[t] = i + 1
                break
        else:
            print("heading not found in PDF:", t)


def build_docx(br):
    """PNG copies of the diagrams, then Word converts an HTML version to an editable .docx."""
    global WORD
    pngdir = os.path.join(DIAG, "png")
    os.makedirs(pngdir, exist_ok=True)
    for f in sorted(os.listdir(DIAG)):
        if not f.endswith(".svg"):
            continue
        name = f[:-4]
        w, h = svg_size(name)
        subprocess.run([br, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", "--window-size=%d,%d" % (w, h),
                        "--screenshot=" + os.path.join(pngdir, name + ".png"),
                        "file:///" + os.path.join(DIAG, f).replace("\\", "/")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    WORD = True
    tmp = os.path.join(HERE, "_word_source.html")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(build_html())
    WORD = False
    ps = (
        "$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0; "
        "try { $d = $w.Documents.Open('%s', $false, $false); "
        "foreach ($s in $d.InlineShapes) { if ($s.LinkFormat) { $s.LinkFormat.SavePictureWithDocument = $true; $s.LinkFormat.BreakLink() } }; "
        "$d.ActiveWindow.View.Type = 3; "
        "$d.PageSetup.TopMargin = 54; $d.PageSetup.BottomMargin = 54; $d.PageSetup.LeftMargin = 58; $d.PageSetup.RightMargin = 58; "
        "$i = 0; foreach ($t in $d.Tables) { $i++; $t.Rows.AllowBreakAcrossPages = 0; "
        "if ($i -gt 1) { $t.PreferredWidthType = 2; $t.PreferredWidth = 100 } }; "
        "$d.Sections.Item(1).Footers.Item(1).PageNumbers.Add(1) | Out-Null; "
        "$r = $d.Content; if ($r.Find.Execute('[[TOC]]')) { $d.TablesOfContents.Add($r, $true, 2, 3) | Out-Null; $d.TablesOfContents.Item(1).Update() }; "
        "$d.SaveAs2('%s', 16); $d.Close($false) } finally { $w.Quit() }" % (tmp, OUT_DOCX))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    os.remove(tmp)
    print("wrote", OUT_DOCX)


def main():
    os.makedirs(DIAG, exist_ok=True)

    def w(name, s):
        with open(os.path.join(DIAG, name), "w", encoding="utf-8") as f:
            f.write(s)

    for f in os.listdir(DIAG):
        if f.endswith(".svg"):
            os.remove(os.path.join(DIAG, f))
    w("erd_engineering_part_sourcer.svg", build_erd())
    w("schema_foreign_keys.svg", build_fk())
    for r in RELS:
        w("fd_%s.svg" % r["name"], build_fd(r["attrs"], r["pk"], resolved_fds(r)))
    merged = BOMKEY + PARTKEY + ["Quantity"] + LISTKEY
    w("fd_BOMLine_merged_alternative.svg", build_fd(
        merged, BOMKEY + PARTKEY, [(BOMKEY + PARTKEY, ["Quantity"] + LISTKEY), (LISTKEY, PARTKEY)]))

    # integrity check: every FK references the full PK of an existing relation
    for r in RELS:
        assert all(a in r["attrs"] for a in r["pk"])
        for c, ref, rc, act, why in r["fks"]:
            assert ref in REL and rc == REL[ref]["pk"] and len(c) == len(rc), (r["name"], c, ref)
            assert all(a in r["attrs"] for a in c)

    br = find_browser()
    if not br:
        with open(OUT_HTML, "w", encoding="utf-8") as f:
            f.write(build_html())
        print("No Chrome/Edge found: open the HTML and print to PDF manually.")
        return
    print_pdf(br)      # pass 1: lay out
    find_pages()
    print_pdf(br)      # pass 2: contents list with page numbers
    print("wrote", OUT_PDF)
    build_docx(br)


if __name__ == "__main__":
    sys.exit(main())
