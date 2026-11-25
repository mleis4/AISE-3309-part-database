# -*- coding: utf-8 -*-
"""Builds the Assignment 2 report (HTML + SVG diagrams, then PDF via headless Chrome).

Run:  python build_report.py
The schema is defined once in RELS; the relation listing, FK table, FD diagrams
and BCNF table are all generated from it so names stay consistent.
"""
import html
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIAG = os.path.join(HERE, "diagrams")
OUT_HTML = os.path.join(HERE, "AISE3309-Assignment02_Group6.html")
OUT_PDF = os.path.join(HERE, "AISE3309-Assignment02_Group6.pdf")

MEMBERS = [
    ("Shaan Wrench", "251422184"),
    ("Mats Leis", "251409940"),
    ("Ayman Hossain", "251430600"),
    ("Samuel Huang", "251418742"),
    ("Anish Jami", "251419182"),
]

# Team Contribution Efforts: fill in before submitting. List of short bullets per member.
CONTRIB = {
    "Shaan Wrench": [
        "Task 3.3.1: assessed the schema for flaws, redundancy and anomalies, listed the functional "
        "dependencies and made the FD diagrams and the 1NF/2NF/3NF argument for each of the 12 relations.",
    ],
    "Mats Leis": [
        "Task 2: did the ER-to-relational transformation, wrote the 12 relations with their primary, "
        "alternate and foreign keys and derived attributes, and made the referential integrity table and diagram (2.1 to 2.3).",
        "Compiled the report and diagrams into the final PDF and submitted it as group leader.",
    ],
    "Ayman Hossain": [
        "Task 1: defined the relationship types, multiplicities and participation, the Enhanced ER features "
        "(specialization, composition) and the constraints list (1.2 and 1.3).",
    ],
    "Samuel Huang": [
        "Task 1: defined the 7 entity types of the ER diagram, their attributes and identifiers (1.1), and "
        "documented the changes from the Assignment 1 data requirements (1.4).",
    ],
    "Anish Jami": [
        "Task 3.3.2 and 3.3.3: evaluated the candidates for combining relations, did the BCNF evaluation and "
        "the merged BOMLine trade-off, and wrote the anticipated-query justification against the Assignment 1 functions.",
    ],
}

FONT = "Segoe UI, Arial, Helvetica, sans-serif"
esc = html.escape


# ----------------------------------------------------------------------------
# Schema (single source of truth)
# ----------------------------------------------------------------------------
RELS = [
    dict(
        name="Customer",
        attrs=["Email", "Username", "Password", "FirstName", "LastName", "HouseAddress",
               "UnitNum", "City", "Province", "Country", "PostCode"],
        pk=["Email"], aks=[["Username"]], fks=[], derived=[],
        fds=[(["Email"], "rest"), (["Username"], "rest")],
        nf2="Single-attribute key, so no partial dependency is possible.",
        nf3="The only determinants are Email (PK) and Username (AK). No non-key attribute "
            "determines another (see the customer address issue above).",
    ),
    dict(
        name="Part",
        attrs=["Manufacturer_PartNum", "Name", "Description", "Category", "Length", "Width",
               "Height", "Datasheet_link"],
        pk=["Manufacturer_PartNum"], aks=[], fks=[], derived=[],
        fds=[(["Manufacturer_PartNum"], "rest")],
        nf2="Single-attribute key, so no partial dependency is possible.",
        nf3="Category does not determine Name, the dimensions or the datasheet, and two parts "
            "can share a Name. No transitive dependency.",
    ),
    dict(
        name="Distributor",
        attrs=["Name", "Website", "ShippingFee"],
        pk=["Name"], aks=[["Website"]], fks=[],
        derived=["/AvgStarRating = AVG(Review.StarRating) over the distributor's reviews"],
        fds=[(["Name"], "rest"), (["Website"], "rest")],
        nf2="Single-attribute key, so no partial dependency is possible.",
        nf3="Website determines Name and ShippingFee, but Website is a candidate key, so this is "
            "not a transitive dependency.",
    ),
    dict(
        name="Listing",
        attrs=["DistributorName", "Distributor_PartNum", "Manufacturer_PartNum", "UnitPrice",
               "StockQuantity", "EstShipTime", "LastUpdated"],
        pk=["DistributorName", "Distributor_PartNum"],
        aks=[["DistributorName", "Manufacturer_PartNum"]],
        fks=[(["DistributorName"], "Distributor", ["Name"]),
             (["Manufacturer_PartNum"], "Part", ["Manufacturer_PartNum"])],
        derived=[],
        fds=[(["DistributorName", "Distributor_PartNum"], "rest"),
             (["DistributorName", "Manufacturer_PartNum"], "rest")],
        nf2="A distributor part number (SKU) is only unique within its distributor, so price, "
            "stock, shipping time and the part offered all need the whole key. Nothing depends "
            "on DistributorName or Distributor_PartNum alone.",
        nf3="UnitPrice, StockQuantity, EstShipTime and LastUpdated are independent of each "
            "other. The second determinant is the alternate key.",
    ),
    dict(
        name="ShoppingCart",
        attrs=["CustomerEmail", "Date_Added"],
        pk=["CustomerEmail"], aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"])],
        derived=["/Subtotal = SUM(CartLine.Quantity × Listing.UnitPrice)",
                 "/ShippingPrice = SUM(Distributor.ShippingFee) over the distinct distributors in the cart",
                 "/TotalPrice = /Subtotal + /ShippingPrice"],
        fds=[(["CustomerEmail"], "rest")],
        nf2="Single-attribute key, so no partial dependency is possible.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="BOM",
        attrs=["CustomerEmail", "BOM_name", "Date_created"],
        pk=["CustomerEmail", "BOM_name"], aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"])],
        derived=["/NumberOfParts = COUNT of the BOM's BOMLine rows",
                 "/TotalCost = SUM(BOMLine.Quantity × Listing.UnitPrice) over the listings in BOMSelection"],
        fds=[(["CustomerEmail", "BOM_name"], "rest")],
        nf2="Date_created belongs to one named BOM of one customer. A customer has many BOMs and "
            "a name can be reused by other customers, so neither key attribute alone determines it.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="SharedProject",
        attrs=["CustomerEmail", "BOM_name", "Title", "Description", "Date_shared"],
        pk=["CustomerEmail", "BOM_name"], aks=[["Title"]],
        fks=[(["CustomerEmail", "BOM_name"], "BOM", ["CustomerEmail", "BOM_name"])],
        derived=[],
        fds=[(["CustomerEmail", "BOM_name"], "rest"), (["Title"], "rest")],
        nf2="Title, Description and Date_shared describe one shared BOM, which is identified "
            "only by the whole key.",
        nf3="Title determines the other attributes, but Title is a candidate key. Description "
            "and Date_shared determine nothing.",
    ),
    dict(
        name="PartAlternative",
        attrs=["Part1_PartNum", "Part2_PartNum"],
        pk=["Part1_PartNum", "Part2_PartNum"], aks=[],
        fks=[(["Part1_PartNum"], "Part", ["Manufacturer_PartNum"]),
             (["Part2_PartNum"], "Part", ["Manufacturer_PartNum"])],
        derived=[], fds=[],
        nf2="All-key relation: there are no non-key attributes.",
        nf3="All-key relation: there are no non-key attributes.",
    ),
    dict(
        name="BOMLine",
        attrs=["CustomerEmail", "BOM_name", "Manufacturer_PartNum", "Quantity"],
        pk=["CustomerEmail", "BOM_name", "Manufacturer_PartNum"], aks=[],
        fks=[(["CustomerEmail", "BOM_name"], "BOM", ["CustomerEmail", "BOM_name"]),
             (["Manufacturer_PartNum"], "Part", ["Manufacturer_PartNum"])],
        derived=[],
        fds=[(["CustomerEmail", "BOM_name", "Manufacturer_PartNum"], "rest")],
        nf2="Quantity is how many of one part one BOM needs. It changes with the BOM and with "
            "the part, so it depends on the whole key.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="BOMSelection",
        attrs=["CustomerEmail", "BOM_name", "DistributorName", "Distributor_PartNum"],
        pk=["CustomerEmail", "BOM_name", "DistributorName", "Distributor_PartNum"], aks=[],
        fks=[(["CustomerEmail", "BOM_name"], "BOM", ["CustomerEmail", "BOM_name"]),
             (["DistributorName", "Distributor_PartNum"], "Listing",
              ["DistributorName", "Distributor_PartNum"])],
        derived=[], fds=[],
        nf2="All-key relation: there are no non-key attributes.",
        nf3="All-key relation: there are no non-key attributes.",
    ),
    dict(
        name="CartLine",
        attrs=["CustomerEmail", "DistributorName", "Distributor_PartNum", "Quantity"],
        pk=["CustomerEmail", "DistributorName", "Distributor_PartNum"], aks=[],
        fks=[(["CustomerEmail"], "ShoppingCart", ["CustomerEmail"]),
             (["DistributorName", "Distributor_PartNum"], "Listing",
              ["DistributorName", "Distributor_PartNum"])],
        derived=[],
        fds=[(["CustomerEmail", "DistributorName", "Distributor_PartNum"], "rest")],
        nf2="Quantity is how many units of one listing one cart holds, so it depends on the "
            "whole key.",
        nf3="One non-key attribute, so no transitive dependency is possible.",
    ),
    dict(
        name="Review",
        attrs=["CustomerEmail", "DistributorName", "ReviewText", "StarRating"],
        pk=["CustomerEmail", "DistributorName"], aks=[],
        fks=[(["CustomerEmail"], "Customer", ["Email"]),
             (["DistributorName"], "Distributor", ["Name"])],
        derived=[],
        fds=[(["CustomerEmail", "DistributorName"], "rest")],
        nf2="A customer reviews many distributors and a distributor has many reviewers, so the "
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


def entity(x, y, w, name, rows):
    """rows: list of (text, indented). Returns (svg, height)."""
    h = HDR + PAD + ROW * len(rows)
    s = ['<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#000" stroke-width="1.4"/>' % (x, y, w, h),
         '<rect x="%d" y="%d" width="%d" height="%d" fill="#dce9f7" stroke="#000" stroke-width="1.4"/>' % (x, y, w, HDR),
         text(x + w / 2, y + 22, name, 16, "middle", "bold")]
    for i, (t, ind) in enumerate(rows):
        s.append(text(x + (26 if ind else 10), y + HDR + 18 + ROW * i, t, 14))
    return "\n".join(s), h


def attr_box(x, y, w, rows):
    h = 8 + 18 * len(rows)
    s = ['<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#000" stroke-width="1" stroke-dasharray="5,4"/>' % (x, y, w, h)]
    for i, t in enumerate(rows):
        s.append(text(x + 8, y + 18 + 18 * i, t, 13))
    return "\n".join(s), h


def diamond(cx, cy_top):
    """Filled composition diamond hanging below (cx, cy_top)."""
    return '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#000"/>' % (
        cx, cy_top, cx + 7, cy_top + 11, cx, cy_top + 22, cx - 7, cy_top + 11)


def build_erd():
    b = []
    ents = {}

    def add(key, x, y, w, name, rows):
        s, h = entity(x, y, w, name, rows)
        ents[key] = (x, y, w, h)
        return s

    e_svg = [
        add("cust", 440, 30, 260, "Customer", [
            ("Email {PK}", 0), ("Username {AK}", 0), ("Password", 0),
            ("Name", 0), ("FirstName", 1), ("LastName", 1),
            ("BillingAddress", 0), ("HouseAddress", 1), ("UnitNum", 1), ("City", 1),
            ("Province", 1), ("Country", 1), ("PostCode", 1)]),
        add("bom", 300, 410, 200, "BOM", [
            ("BOM_name {PPK}", 0), ("Date_created", 0), ("/NumberOfParts", 0), ("/TotalCost", 0)]),
        add("sp", 20, 420, 190, "SharedProject", [
            ("Title {AK}", 0), ("Description", 0), ("Date_shared", 0)]),
        add("cart", 570, 410, 200, "ShoppingCart", [
            ("Date_Added", 0), ("/Subtotal", 0), ("/ShippingPrice", 0), ("/TotalPrice", 0)]),
        add("dist", 860, 410, 210, "Distributor", [
            ("Name {PK}", 0), ("Website {AK}", 0), ("ShippingFee", 0), ("/AvgStarRating", 0)]),
        add("list", 570, 670, 220, "Listing", [
            ("Distributor_PartNum {PPK}", 0), ("UnitPrice", 0), ("StockQuantity", 0),
            ("EstShipTime", 0), ("LastUpdated", 0)]),
        add("part", 300, 890, 230, "Part", [
            ("Manufacturer_PartNum {PK}", 0), ("Name", 0), ("Description", 0), ("Category", 0),
            ("Dimensions", 0), ("Length", 1), ("Width", 1), ("Height", 1), ("Datasheet_link", 0)]),
    ]

    def bottom(k):
        x, y, w, h = ents[k]
        return y + h

    cb, bb, kb, db, lb = bottom("cust"), bottom("bom"), bottom("cart"), bottom("dist"), bottom("list")
    bom_mid = ents["bom"][1] + ents["bom"][3] / 2.0
    M = 13  # multiplicity / label font size

    # Creates: Customer 1..1 -- 0..* BOM (identifying, composition)
    b.append(poly([(470, cb), (470, 410)]))
    b.append(diamond(470, cb))
    b.append(text(482, cb + 20, "1..1", M))
    b.append(text(482, cb + 52, "Creates ▼", M, style="italic"))
    b.append(text(478, 403, "0..*", M))

    # Owns: Customer 1..1 -- 0..1 ShoppingCart (identifying, composition)
    b.append(poly([(670, cb), (670, 410)]))
    b.append(diamond(670, cb))
    b.append(text(682, cb + 20, "1..1", M))
    b.append(text(682, cb + 52, "Owns ▼", M, style="italic"))
    b.append(text(678, 403, "0..1", M))

    # Reviews: Customer 0..* -- 0..* Distributor, attributes ReviewText, StarRating
    b.append(poly([(700, 120), (965, 120), (965, 410)]))
    b.append(text(706, 112, "0..*", M))
    b.append(text(835, 112, "Reviews ►", M, "middle", style="italic"))
    b.append(text(973, 403, "0..*", M))
    s, h = attr_box(770, 160, 130, ["ReviewText", "StarRating"])
    b.append(s)
    b.append(poly([(835, 120), (835, 160)], dash=True))

    # Specialization: BOM (superclass) <|-- SharedProject (subclass), {Optional}
    b.append(poly([(300, bom_mid), (210, bom_mid)]))
    b.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#fff" stroke="#000" stroke-width="1.3"/>'
             % (286, bom_mid, 264, bom_mid - 12, 264, bom_mid + 12))
    b.append(text(255, bom_mid + 34, "{Optional}", M, "middle"))

    # Contains: BOM 0..* -- 0..* Part, attribute Quantity
    b.append(poly([(400, bb), (400, 890)]))
    b.append(text(392, bb + 17, "0..*", M, "end"))
    b.append(text(392, 640, "Contains ▼", M, "end", style="italic"))
    b.append(text(392, 882, "0..*", M, "end"))
    s, h = attr_box(285, 737, 82, ["Quantity"])
    b.append(s)
    b.append(poly([(400, 750), (367, 750)], dash=True))

    # Selects: BOM 0..* -- 0..* Listing
    b.append(poly([(500, 495), (535, 495), (535, 715), (570, 715)]))
    b.append(text(505, 489, "0..*", M))
    b.append(text(543, 570, "Selects ▼", M, style="italic"))
    b.append(text(541, 709, "0..*", M))

    # Holds: ShoppingCart 0..* -- 0..* Listing, attribute Quantity
    b.append(poly([(670, kb), (670, 670)]))
    b.append(text(678, kb + 17, "0..*", M))
    b.append(text(662, 640, "Holds ▼", M, "end", style="italic"))
    b.append(text(678, 663, "0..*", M))
    s, h = attr_box(705, 588, 82, ["Quantity"])
    b.append(s)
    b.append(poly([(670, 601), (705, 601)], dash=True))

    # Publishes: Distributor 1..1 -- 0..* Listing (identifying, composition)
    b.append(poly([(965, db), (965, 737), (790, 737)]))
    b.append(diamond(965, db))
    b.append(text(977, db + 20, "1..1", M))
    b.append(text(885, 729, "◄ Publishes", M, "middle", style="italic"))
    b.append(text(796, 731, "0..*", M))

    # Has: Listing 0..* -- 1..1 Part
    b.append(poly([(670, lb), (670, 990), (530, 990)]))
    b.append(text(678, lb + 17, "0..*", M))
    b.append(text(678, 850, "Has ▼", M, style="italic"))
    b.append(text(536, 984, "1..1", M))

    # AlternativeTo: Part 0..* -- 0..* Part (recursive)
    b.append(poly([(300, 950), (235, 950), (235, 1040), (300, 1040)]))
    b.append(text(267, 944, "0..*", M, "middle"))
    b.append(text(267, 1057, "0..*", M, "middle"))
    b.append(text(227, 999, "AlternativeTo", M, "end", style="italic"))

    # Legend
    lx, ly = 715, 868
    leg = ['<rect x="%d" y="%d" width="360" height="232" fill="#fafafa" stroke="#666" stroke-width="1"/>' % (lx, ly),
           text(lx + 12, ly + 22, "Notation", 14, weight="bold")]
    lines = [
        "{PK} primary key     {AK} alternate key",
        "{PPK} partial key of a weak entity",
        "/Attr   derived attribute",
        "Indented attributes are parts of a composite",
        "0..*   multiplicity (min..max)",
        "Dashed box: attributes of the relationship",
    ]
    for i, t in enumerate(lines):
        leg.append(text(lx + 12, ly + 46 + 20 * i, t, 13))
    yy = ly + 46 + 20 * len(lines) + 2
    leg.append(diamond(lx + 22, yy - 14))
    leg.append(text(lx + 40, yy + 2, "Composition (identifying relationship)", 13))
    yy += 26
    leg.append('<polygon points="%d,%d %d,%d %d,%d" fill="#fff" stroke="#000" stroke-width="1.3"/>'
               % (lx + 32, yy - 4, lx + 12, yy - 14, lx + 12, yy + 6))
    leg.append(text(lx + 40, yy + 1, "Specialization, points to the superclass", 13))

    return svg_wrap(1090, 1115, "\n".join(e_svg + b + leg))


# ----------------------------------------------------------------------------
# Figure 2: referential integrity (FK -> PK)
# ----------------------------------------------------------------------------
def build_fk():
    BW, BH = 150, 36
    pos = {
        "Customer": (260, 20), "Distributor": (640, 20),
        "ShoppingCart": (100, 190), "BOM": (300, 190), "Review": (490, 190),
        "Listing": (690, 190), "Part": (930, 190),
        "SharedProject": (100, 360), "BOMLine": (300, 360), "BOMSelection": (500, 360),
        "CartLine": (700, 360), "PartAlternative": (930, 360),
    }
    s = []
    edges = []
    for r in RELS:
        for cols, ref, refcols in r["fks"]:
            edges.append((r["name"], ref))
    seen = {}
    for src, tgt in edges:
        sx, sy = pos[src]
        tx, ty = pos[tgt]
        k = seen.get((src, tgt), 0)
        seen[(src, tgt)] = k + 1
        if sy == ty:  # same row: horizontal
            s.append(poly([(sx + BW / 2, sy + BH / 2), (tx - BW / 2, ty + BH / 2)], marker=True))
            continue
        off = max(-60, min(60, (sx - tx) * 0.14)) + (14 if k else 0)
        if src == "PartAlternative":
            off = -10 + 20 * k
            s.append(poly([(sx + off, sy), (tx + off, ty + BH)], marker=True))
            continue
        s.append(poly([(sx - off * 0.5, sy), (tx + off, ty + BH)], marker=True))
    for name, (cx, cy) in pos.items():
        s.append('<rect x="%.1f" y="%d" width="%d" height="%d" rx="3" fill="#dce9f7" stroke="#000" stroke-width="1.3"/>'
                 % (cx - BW / 2, cy, BW, BH))
        s.append(text(cx, cy + 23, name, 14, "middle", "bold"))
    return svg_wrap(1030, 415, "\n".join(s))


# ----------------------------------------------------------------------------
# FD diagrams
# ----------------------------------------------------------------------------
def build_fd(name, attrs, pk, fds, note=None):
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
        s.append(text(44, base + 20, note or "All-key relation: the only FDs are trivial.", FS, style="italic"))
        height = base + 30
    return svg_wrap(int(width), int(height), "\n".join(s))


# ----------------------------------------------------------------------------
# HTML pieces
# ----------------------------------------------------------------------------
def table(headers, rows, widths=None, cls=""):
    out = ['<table class="%s">' % cls]
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


WORD = False  # True while building the HTML that Word converts to .docx


def svg_size(name):
    import re
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


def relation_block(r):
    parts = []
    for a in r["attrs"]:
        parts.append('<span class="pk">%s</span>' % a if a in r["pk"] else a)
    lines = ['<div class="relhead"><b>%s</b> (%s)</div>' % (r["name"], ", ".join(parts)),
             '<div class="relkey"><b>Primary Key</b> %s</div>' % cols(r["pk"])]
    if r["aks"]:
        for ak in r["aks"]:
            lines.append('<div class="relkey"><b>Alternate Key</b> %s</div>' % cols(ak))
    else:
        lines.append('<div class="relkey"><b>Alternate Key</b> none</div>')
    if r["fks"]:
        for c, ref, rc in r["fks"]:
            lines.append('<div class="relkey"><b>Foreign Key</b> %s <b>references</b> %s(%s)</div>'
                         % (cols(c), ref, cols(rc)))
    else:
        lines.append('<div class="relkey"><b>Foreign Key</b> none</div>')
    if r["derived"]:
        for d in r["derived"]:
            lines.append('<div class="relkey"><b>Derived</b> %s</div>' % esc(d))
    else:
        lines.append('<div class="relkey"><b>Derived</b> none</div>')
    return '<div class="rel">%s</div>' % "\n".join(lines)


def nf_block(r, idx):
    fds = resolved_fds(r)
    fd_txt = []
    for i, (det, dep) in enumerate(fds):
        fd_txt.append("FD%d: %s → %s" % (i + 1, paren(det) if len(det) > 1 else det[0], cols(dep)))
    if not fd_txt:
        fd_txt = ["No non-trivial FDs."]
    svg = fig("fd_%s" % r["name"])
    cks = [cols(r["pk"])] + [cols(a) for a in r["aks"]]
    return ('<div class="nf"><h4>%d. %s</h4>'
            '<div class="fig">%s</div>'
            '<p class="fdlist">%s<br><b>Candidate keys:</b> %s</p>'
            '<ul class="tight"><li><b>1NF:</b> every attribute holds a single atomic value.</li>'
            '<li><b>2NF:</b> %s</li><li><b>3NF:</b> %s</li></ul></div>'
            % (idx, r["name"], svg, "<br>".join(esc(t) for t in fd_txt),
               "; ".join("{%s}" % c for c in cks), esc(r["nf2"]), esc(r["nf3"])))


CSS = """
@page { size: Letter; margin: 0.75in 0.8in; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, Helvetica, sans-serif; font-size: 10pt; line-height: 1.4; color: #000; margin: 0; }
.cover { text-align: center; break-after: page; }
.banner { background: #1565c0; color: #fff; padding: 46px 10px 40px; font-size: 15pt; font-weight: 600; border-radius: 0 0 50% 50% / 0 0 26px 26px; }
.cover h1 { color: #1565c0; font-size: 22pt; margin: 150px 0 40px; }
.cover h2 { color: #1565c0; font-size: 18pt; margin: 0; }
.cover .sub { color: #1565c0; font-size: 12pt; margin: 4px 0 40px; }
.cover table { width: 78%; margin: 0 auto; text-align: left; }
h2.sec { background: #cfe2f6; border-top: 3px solid #1e88e5; color: #1565c0; font-weight: 500; font-size: 14pt; padding: 4px 10px; margin: 22px 0 12px; break-after: avoid; }
h3 { color: #1565c0; font-size: 12pt; margin: 18px 0 6px; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 12px 0 4px; break-after: avoid; }
p { margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9pt; }
th, td { border: 1px solid #000; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #bdd7ee; text-align: center; }
tr { break-inside: avoid; }
.toc { break-after: page; }
.toc h1 { color: #1565c0; text-align: center; font-size: 22pt; margin: 10px 0 24px; }
.toc div { margin: 5px 0; }
.toc .l2 { margin-left: 26px; }
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
ul.tight { margin: 4px 0 4px 0; padding-left: 20px; }
ul.tight li { margin: 1px 0; }
.todo { background: #fff3a6; }
.pb { break-before: page; page-break-before: always; }
"""


def build_html():
    erd = fig("erd_engineering_part_sourcer")
    fk = fig("schema_foreign_keys")
    fd_merged = fig("fd_BOMLine_merged_alternative")
    H = []
    H.append('<!doctype html><html lang="en"><head><meta charset="utf-8">'
             '<title>AISE 3309 Assignment 02 - Group 6</title><style>%s</style></head><body>' % CSS)

    # ---- cover
    H.append('<div class="cover"><div class="banner">Western Engineering<br>Electrical and Computer Engineering</div>'
             '<h1>AISE 3309: Database Management Systems</h1><h2>Assignment 02</h2>'
             '<div class="sub">Conceptual Model, Relational Schema and Schema Evaluation</div>')
    rows = "".join("<tr><td>%d.&nbsp; %s</td><td>%s</td></tr>" % (i + 1, n, sid)
                   for i, (n, sid) in enumerate(MEMBERS))
    H.append('<table><tr><td><b>Group #:</b></td><td>6 (Lab 2, AISE 3309A 002)</td></tr>'
             '<tr><td><b>Project Name:</b></td><td>Engineering Part Sourcer</td></tr>'
             '<tr><th style="width:50%">Team Member Name</th><th>Team Member ID</th></tr>' + rows + '</table></div>')

    # ---- toc
    H.append('<div class="toc"><h1 class="pb">Table of Contents</h1>'
             '<div>1.&nbsp; Task 1: Conceptual Model (ER Diagram)</div>'
             '<div>2.&nbsp; Task 2: Relational Schema</div>'
             '<div>3.&nbsp; Task 3: Schema Evaluation</div>'
             '<div class="l2">3.3.1&nbsp; Schema Flaws and 3NF</div>'
             '<div class="l2">3.3.2&nbsp; Opportunities for Combining Relations</div>'
             '<div class="l2">3.3.3&nbsp; BCNF Evaluation</div>'
             '<div>4.&nbsp; Team Contribution Efforts</div></div>')

    # ---- Task 1
    H.append('<h2 class="sec pb">1.&nbsp; Task 1: Conceptual Model (ER Diagram)</h2>')
    H.append('<p>Figure 1 is the conceptual model of the Engineering Part Sourcer in UML database notation. '
             'It has <b>7 entity types</b>: Customer, Part, Distributor, Listing, ShoppingCart, BOM and SharedProject.</p>')
    H.append('<div class="fig">%s</div><div class="cap">Figure 1. ER diagram of the Engineering Part Sourcer (UML database notation).</div>' % erd)

    H.append('<h3 class="pb">1.1&nbsp; Entity types and identifiers</h3>')
    H.append('<p>An entity has its own identifier only where the real-world thing has one. '
             'The surrogate IDs from Assignment 1 (BOM ID, Cart_ID, Listing_ID, DistributorID) are removed.</p>')
    H.append(table(["Entity type", "Kind", "Identifier", "Why this identifier"], [
        ["Customer", "Strong", "Email {PK}; Username {AK}", "An account is registered with a unique email address. The username is also unique."],
        ["Part", "Strong", "Manufacturer_PartNum {PK}", "The manufacturer part number is the industry identifier of a component."],
        ["Distributor", "Strong", "Name {PK}; Website {AK}", "Distributors are known by their company name (DigiKey, Mouser). Each has one website."],
        ["Listing", "Weak (owner: Distributor)", "Distributor_PartNum {PPK}", "A distributor's SKU is unique only inside that distributor's catalogue."],
        ["BOM", "Weak (owner: Customer)", "BOM_name {PPK}", "A customer names each BOM. Names are unique only per customer."],
        ["ShoppingCart", "Weak (owner: Customer)", "None", "A customer has at most one cart, so the owner identifies it."],
        ["SharedProject", "Subclass of BOM", "Inherited from BOM; Title {AK}", "A shared project is a BOM that its owner has published. Titles are unique on the sharing page."],
    ], ["15%", "19%", "24%", "42%"]))

    H.append('<h3>1.2&nbsp; Relationship types</h3>')
    H.append('<p>The multiplicity beside an entity is the number of its instances related to one instance at the other end.</p>')
    H.append(table(["Relationship", "Multiplicity", "Participation", "Attributes"], [
        ["Customer <i>Creates</i> BOM", "1..1 to 0..*", "BOM total (identifying); Customer partial", "None"],
        ["Customer <i>Owns</i> ShoppingCart", "1..1 to 0..1", "ShoppingCart total (identifying); Customer partial", "None"],
        ["Customer <i>Reviews</i> Distributor", "0..* to 0..*", "Partial on both sides", "ReviewText, StarRating"],
        ["Distributor <i>Publishes</i> Listing", "1..1 to 0..*", "Listing total (identifying); Distributor partial", "None"],
        ["Listing <i>Has</i> Part", "0..* to 1..1", "Listing total; Part partial", "None"],
        ["Part <i>AlternativeTo</i> Part", "0..* to 0..*", "Partial on both sides (recursive)", "None"],
        ["BOM <i>Contains</i> Part", "0..* to 0..*", "Partial on both sides", "Quantity"],
        ["BOM <i>Selects</i> Listing", "0..* to 0..*", "Partial on both sides", "None"],
        ["ShoppingCart <i>Holds</i> Listing", "0..* to 0..*", "Partial on both sides", "Quantity"],
        ["BOM / SharedProject", "Specialization", "{Optional}: a BOM does not have to be shared", "Subclass adds Title, Description, Date_shared"],
    ], ["27%", "14%", "36%", "23%"]))

    H.append('<h3>1.3&nbsp; Enhanced ER features and constraints</h3>')
    H.append('<ul class="tight">'
             '<li><b>Specialization.</b> SharedProject is a subclass of BOM. Participation is {Optional} because most BOMs stay private. '
             'There is one subclass, so a disjoint/overlapping constraint does not apply. The subclass inherits the BOM\'s owner and parts, '
             'so the customer who shared a project and the parts it uses are not recorded twice.</li>'
             '<li><b>Composition.</b> BOM and ShoppingCart are parts of a Customer, and Listing is part of a Distributor. They cannot exist without the owner and are deleted with it.</li>'
             '<li><b>Composite attributes.</b> Customer.Name, Customer.BillingAddress and Part.Dimensions.</li>'
             '<li><b>Derived attributes.</b> /AvgStarRating, /NumberOfParts, /TotalCost, /Subtotal, /ShippingPrice and /TotalPrice (defined in Task 2).</li>'
             '</ul>')
    H.append('<p>Constraints that the diagram cannot show:</p>')
    H.append(table(["#", "Constraint"], [
        ["C1", "StarRating is an integer from 1 to 5. Every Quantity is greater than 0. UnitPrice, StockQuantity and ShippingFee are not negative."],
        ["C2", "A distributor has at most one listing for a given part (Assignment 1: a listing is \"one distributor's offer for one part\")."],
        ["C3", "A BOM selects at most one listing for each part it contains, and only listings of parts it contains."],
        ["C4", "AlternativeTo is symmetric, and a part is not an alternative to itself."],
        ["C5", "A BOM must contain at least one part before it can be shared as a SharedProject."],
        ["C6", "A customer reviews a distributor at most once. Purchases are completed on the distributor's own website, so the system does not record them and cannot check that a review follows a purchase."],
    ], ["6%", "94%"]))

    H.append('<h3>1.4&nbsp; Changes from the Assignment 1 data requirements</h3>')
    H.append(table(["Assignment 1", "Problem", "This model"], [
        ["BOM ID, Cart_ID, Listing_ID, DistributorID", "Arbitrary surrogate identifiers", "Removed. Real identifiers or weak entities are used."],
        ["Part.Distributor", "Repeats what Listing records, and a part has many distributors", "Removed. Distributors are reached through Listing."],
        ["Distributor \"Customer reviews\" and \"All parts\", ShoppingCart \"Parts\"", "Multi-valued attributes that are really relationships", "Reviews, Publishes and Holds relationships."],
        ["Listing.Quantity", "Same name as the relationship attribute Quantity", "Renamed StockQuantity."],
        ["/Shipping price with no source data", "A derived attribute needs stored data to be derived from", "Distributor.ShippingFee added (flat fee per order from that distributor)."],
        ["Project sharing (functional specification only)", "No entity stored a shared project", "SharedProject added as a subclass of BOM."],
        ["BOM maker \"select supplier listings\"", "No relationship recorded the chosen supplier, so /TotalCost could not be derived", "Selects relationship between BOM and Listing."],
    ], ["30%", "35%", "35%"]))

    # ---- Task 2
    H.append('<h2 class="sec pb">2.&nbsp; Task 2: Relational Schema</h2>')
    H.append('<h3>2.1&nbsp; Transformation steps</h3>')
    H.append(table(["Step", "ER construct", "Result"], [
        ["1. Strong entity types", "Customer, Part, Distributor", "One relation each. Composite attributes are replaced by their simple components (Name by 2, BillingAddress by 6, Dimensions by 3)."],
        ["2. Weak entity types", "Listing, BOM, ShoppingCart", "One relation each. The owner's PK is added as an FK, and the PK is the owner's PK plus the partial key. ShoppingCart has no partial key, so its PK is CustomerEmail."],
        ["3. 1:1 relationships", "Owns", "Already mapped in step 2: the FK CustomerEmail in ShoppingCart is also its PK, which enforces one cart per customer."],
        ["4. 1:* relationships", "Creates, Publishes, Has", "The PK of the \"one\" side is posted to the \"many\" side. Creates and Publishes were mapped in step 2. Has adds Manufacturer_PartNum to Listing (NOT NULL)."],
        ["5. *:* relationships", "AlternativeTo, Contains, Selects, Holds, Reviews", "A new relation each: PartAlternative, BOMLine, BOMSelection, CartLine, Review. The PK is the combination of the two FKs, and relationship attributes become columns."],
        ["6. Multi-valued attributes", "None in the final ER diagram", "The multi-valued attributes of Assignment 1 were already modelled as relationships."],
        ["7. Specialization", "BOM / SharedProject, {Optional}", "Separate relations for superclass and subclass. SharedProject's PK is the BOM PK, which is also an FK to BOM."],
        ["Derived attributes", "Six attributes marked /", "Not stored. Each is listed under its relation with the rule that computes it."],
    ], ["19%", "27%", "54%"]))

    H.append('<h3>2.2&nbsp; Relations</h3>')
    H.append('<p>Notation: <b>Relation</b> (attributes), with primary key attributes underlined, followed by the keys. '
             'FK attributes are named after the referenced relation where the original name would be ambiguous '
             '(CustomerEmail references Customer.Email, DistributorName references Distributor.Name).</p>')
    for r in RELS:
        H.append(relation_block(r))
    H.append('<p>Additional integrity rules for the implementation: constraints C1 and C4 become CHECK constraints '
             '(PartAlternative stores each pair once with Part1_PartNum &lt; Part2_PartNum), C2 is the alternate key of Listing, '
             'and C3 and C5 need a trigger or an application check. All FK columns are NOT NULL.</p>')

    H.append('<h3>2.3&nbsp; Referential integrity</h3>')
    H.append('<p>Every foreign key references the complete primary key of an existing relation.</p>')
    fk_rows = []
    for r in RELS:
        for c, ref, rc in r["fks"]:
            ok = "Yes" if rc == REL[ref]["pk"] else "NO"
            fk_rows.append([r["name"], cols(c), "%s(%s)" % (ref, cols(rc)), ok])
    H.append(table(["Relation", "Foreign key", "References", "Full PK of target?"], fk_rows, ["18%", "34%", "34%", "14%"]))
    H.append('<div class="fig">%s</div><div class="cap">Figure 2. Referential integrity. Each arrow goes from a foreign key to the relation whose primary key it references.</div>' % fk)

    # ---- Task 3
    H.append('<h2 class="sec pb">3.&nbsp; Task 3: Schema Evaluation</h2>')
    H.append('<h3>3.3.1&nbsp; Schema flaws and 3NF</h3>')
    H.append('<h4>Flaws, redundancy and anomalies</h4>')
    H.append('<p>We checked the schema for repeated facts and for insert, update and delete anomalies.</p>')
    H.append(table(["Issue", "Assessment", "Decision"], [
        ["Customer address", "In Canada a PostCode usually implies City and Province, which would be a transitive dependency. It is not a dependency in this system: customers can be in any country, postal code formats are not unique across countries, and one code can cover more than one municipality.", "Not treated as an FD. The address stays in Customer and is always read as a whole."],
        ["Derived values", "Storing /TotalCost, /Subtotal or /AvgStarRating would go out of date whenever a price, quantity or review changes (update anomaly).", "None is stored. They are computed by queries or views."],
        ["Natural keys used as FKs", "Email and distributor Name appear in several relations. Changing one must change every reference.", "Accepted, because surrogate IDs are not allowed. The FKs use ON UPDATE CASCADE."],
        ["PartAlternative", "A symmetric pair could be stored twice as (A, B) and (B, A), which is redundant and can become inconsistent.", "Each pair is stored once (C4)."],
        ["BOMSelection", "The key cannot enforce C3 (one selected listing per part).", "Enforced by a trigger. Section 3.3.3 explains why the relations were not merged to enforce it by a key."],
        ["Shared project parts", "A separate part list per shared project would repeat the BOM's lines.", "Avoided by the specialization. A shared project uses its BOM's BOMLine rows."],
        ["Insert and delete anomalies", "A part can exist with no listing, a distributor with no listings, and a customer with no BOM or cart. Deleting the last listing of a part does not delete the part.", "No anomaly. Each fact is stored in one relation."],
    ], ["17%", "53%", "30%"]))

    H.append('<h4>Normalization of every relation</h4>')
    H.append('<p>Each diagram shows the relation\'s attributes (primary key shaded and underlined) and its functional dependencies. '
             'A dot marks a determinant attribute and an arrow points to each dependent attribute. '
             '2NF requires that no non-key attribute depends on part of a candidate key. '
             '3NF requires that no non-key attribute depends on another non-key attribute.</p>')
    for i, r in enumerate(RELS):
        H.append(nf_block(r, i + 1))
    H.append('<p><b>Result:</b> all 12 relations are in 1NF, 2NF and 3NF.</p>')

    H.append('<h3>3.3.2&nbsp; Opportunities for combining relations</h3>')
    H.append('<p>Two relations can be combined without redundancy when they have the same key, which happens for 1:1 relationships, '
             'superclass/subclass pairs and relationship relations over the same entities. We found three candidates.</p>')
    H.append(table(["Candidate", "Combined without redundancy?", "Decision and query justification"], [
        ["Customer + ShoppingCart (1:1, same key)",
         "Yes. Date_Added would become a nullable column of Customer and no row is repeated.",
         "<b>Kept separate.</b> Sign-in reads Customer on every visit and never needs the cart. Cart queries join CartLine to Listing and do not need the customer's credentials or address. A customer with no cart would store a NULL, and CartLine's FK would have to point at Customer, which hides the rule that lines belong to a cart."],
        ["BOM + SharedProject (superclass/subclass, same key)",
         "Yes. Title, Description and Date_shared would become nullable columns of BOM.",
         "<b>Kept separate.</b> The most common query on shared projects is browsing or searching all of them by title, and it reads only the small SharedProject relation. Opening a private BOM never needs the sharing columns. Most BOMs are private, so the merged relation would be mostly NULLs, and Title could not be a simple NOT NULL alternate key."],
        ["BOMLine + BOMSelection (both between a BOM and one of its parts)",
         "No row is repeated: the merged relation is BOMLine with nullable DistributorName and Distributor_PartNum. It does add a dependency whose determinant is not a key.",
         "<b>Kept separate.</b> The merged relation is 3NF but not BCNF (shown in 3.3.3). The BOM cost query needs Listing for UnitPrice in either design, so merging removes no join from it."],
    ], ["22%", "30%", "48%"]))
    H.append('<p>No other pair can be combined. Every remaining pair is linked by a 1:* or *:* relationship, so merging would repeat the '
             'attributes of one side: Distributor with Listing would repeat Website and ShippingFee on every listing, Part with Listing would repeat the part description for every distributor, '
             'and BOM with BOMLine would repeat Date_created on every line.</p>')

    H.append('<h3>3.3.3&nbsp; BCNF evaluation</h3>')
    H.append('<p>A relation is in BCNF when the determinant of every non-trivial functional dependency is a superkey. '
             'The determinants below are the ones in the FD diagrams of 3.3.1.</p>')
    b_rows = []
    for r in RELS:
        fds = resolved_fds(r)
        if fds:
            dets = "; ".join(paren(d) for d, _ in fds)
            keys = [r["pk"]] + r["aks"]
            allkey = all(d in keys for d, _ in fds)
            why = "Yes: " + ", ".join("PK" if d == r["pk"] else "AK" for d, _ in fds)
            assert allkey
        else:
            dets = "None (all-key)"
            why = "Yes: no non-trivial FD"
        b_rows.append([r["name"], dets, why, "BCNF"])
    H.append(table(["Relation", "Determinants", "Every determinant a superkey?", "Result"], b_rows, ["16%", "50%", "24%", "10%"]))
    H.append('<p><b>All 12 relations are in BCNF, so no relation is decomposed.</b> Customer, Distributor, Listing and SharedProject each have two candidate keys. '
             'In every case both are determinants of the whole relation, so the overlapping keys in Listing (both contain DistributorName) cause no violation.</p>')
    H.append('<h4>The design that would not be in BCNF</h4>')
    H.append('<p>The merge considered in 3.3.2 gives BOMLine (CustomerEmail, BOM_name, Manufacturer_PartNum, Quantity, DistributorName, Distributor_PartNum):</p>')
    H.append('<div class="fig" style="text-align:left">%s</div><div class="cap">Figure 3. FDs of the rejected merged BOMLine. FD2 has a determinant that is not a superkey.</div>' % fd_merged)
    H.append('<ul class="tight">'
             '<li>FD1: (CustomerEmail, BOM_name, Manufacturer_PartNum) → Quantity, DistributorName, Distributor_PartNum. The determinant is the key.</li>'
             '<li>FD2: (DistributorName, Distributor_PartNum) → Manufacturer_PartNum. A listing is for exactly one part. This determinant is not a superkey, so the relation is <b>not in BCNF</b>.</li>'
             '<li>It is still in 3NF, because Manufacturer_PartNum is part of a candidate key.</li>'
             '</ul>')
    H.append('<p>The BCNF decomposition of that relation on FD2 is exactly the pair we already have: BOMLine (CustomerEmail, BOM_name, Manufacturer_PartNum, Quantity) and '
             'BOMSelection (CustomerEmail, BOM_name, DistributorName, Distributor_PartNum), with the listing\'s part found in Listing. The trade-off is:</p>')
    H.append(table(["", "Merged BOMLine (3NF only)", "BOMLine + BOMSelection (BCNF, chosen)"], [
        ["Redundancy", "The part of the chosen listing is stored in BOMLine and again in Listing. A row could name a listing for a different part.", "The part of a listing is stored once, in Listing."],
        ["NULLs", "DistributorName and Distributor_PartNum are NULL until a supplier is chosen, and are part of a composite FK.", "None. A line with no chosen supplier has no BOMSelection row."],
        ["Constraint C3", "\"One listing per line\" is enforced by the key.", "Not dependency preserving: C3 needs a trigger."],
        ["Queries", "BOM cost: BOMLine ⋈ Listing.", "BOM cost: BOMLine ⋈ BOMSelection ⋈ Listing, all on key attributes. Listing the parts of a BOM or of a shared project reads BOMLine only."],
    ], ["14%", "43%", "43%"]))
    H.append('<p><b>Decision:</b> keep the BCNF design. The most frequent BOM operations (open a BOM, upload a BOM from CSV, replicate a shared project) work on parts and quantities only and never touch the supplier choice. '
             'The cost query needs one extra join on indexed key columns, and the trigger for C3 runs only when a supplier is selected, which is rare compared with reads.</p>')

    H.append('<h4>Anticipated common queries and how the design serves them</h4>')
    H.append(table(["Query (Assignment 1 function)", "Relations used", "Why the design fits"], [
        ["Search parts by name, part number or keyword (Part Search)", "Part", "Part holds only seller-independent data, so one row per part is searched. It was not merged with Listing."],
        ["Compare offers for N units of a part (Price Match)", "Listing ⋈ Distributor", "All offers for a part are the Listing rows with its Manufacturer_PartNum. A price or stock change updates one row."],
        ["Filter by category, dimensions, distributor, price, stock (Filter)", "Part ⋈ Listing", "Part attributes and Listing attributes are reached with one key join."],
        ["Open, edit or upload a BOM (BOM upload, BOM maker)", "BOM, BOMLine", "Lines are keyed by BOM and part, so the supplier choice is not involved (BCNF decision)."],
        ["BOM line costs, total and stock warnings (BOM maker)", "BOMLine ⋈ BOMSelection ⋈ Listing", "Costs are derived at read time from current prices, so they cannot be stale."],
        ["Cart subtotals grouped by distributor (Cart)", "CartLine ⋈ Listing ⋈ Distributor", "CartLine carries DistributorName in its key, so grouping needs no extra lookup. Kept apart from Customer (3.3.2)."],
        ["Sign in (Sign in)", "Customer", "One small row by Email or Username. No cart or BOM data is read."],
        ["Browse shared projects and copy their parts (Project Sharing)", "SharedProject, then BOMLine ⋈ Part", "Browsing reads only SharedProject (3.3.2). The parts come from the BOM's lines, with no second copy."],
        ["Distributor rating", "Review", "AVG(StarRating) grouped by DistributorName."],
        ["Alternative parts", "PartAlternative ⋈ Part", "Each pair is stored once and queried in both directions."],
    ], ["34%", "25%", "41%"]))

    # ---- Contribution
    H.append('<h2 class="sec pb">4.&nbsp; Team Contribution Efforts</h2>')
    c_rows = []
    for n, _ in MEMBERS:
        items = CONTRIB.get(n) or []
        if items:
            cell = '<ul class="tight">%s</ul>' % "".join("<li>%s</li>" % esc(i) for i in items)
        else:
            cell = '<span class="todo">[to be completed by this member]</span>'
        c_rows.append([n, cell])
    H.append(table(["Team member", "Contribution"], c_rows, ["25%", "75%"]))
    H.append("</body></html>")
    return "\n".join(H)


def find_browser():
    cands = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def main():
    os.makedirs(DIAG, exist_ok=True)

    def w(name, s):
        with open(os.path.join(DIAG, name), "w", encoding="utf-8") as f:
            f.write(s)

    w("erd_engineering_part_sourcer.svg", build_erd())
    w("schema_foreign_keys.svg", build_fk())
    for r in RELS:
        w("fd_%s.svg" % r["name"], build_fd(r["name"], r["attrs"], r["pk"], resolved_fds(r)))
    merged = ["CustomerEmail", "BOM_name", "Manufacturer_PartNum", "Quantity", "DistributorName", "Distributor_PartNum"]
    w("fd_BOMLine_merged_alternative.svg", build_fd(
        "BOMLine (merged)", merged, merged[:3],
        [(merged[:3], merged[3:]), (merged[4:], ["Manufacturer_PartNum"])]))

    # integrity check: every FK references the full PK of an existing relation
    for r in RELS:
        for c, ref, rc in r["fks"]:
            assert ref in REL and rc == REL[ref]["pk"] and len(c) == len(rc), (r["name"], c, ref)
            assert all(a in r["attrs"] for a in c)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("wrote", OUT_HTML)

    br = find_browser()
    if not br:
        print("No Chrome/Edge found: open the HTML and print to PDF manually.")
        return
    subprocess.run([br, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + OUT_PDF, "file:///" + OUT_HTML.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", OUT_PDF)
    build_docx(br)


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
    out = os.path.join(HERE, "AISE3309-Assignment02_Group6.docx")
    ps = (
        "$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0; "
        "try { $d = $w.Documents.Open('%s', $false, $false); "
        "foreach ($s in $d.InlineShapes) { if ($s.LinkFormat) { $s.LinkFormat.SavePictureWithDocument = $true; $s.LinkFormat.BreakLink() } }; "
        "$d.ActiveWindow.View.Type = 3; "
        "$d.PageSetup.TopMargin = 54; $d.PageSetup.BottomMargin = 54; $d.PageSetup.LeftMargin = 58; $d.PageSetup.RightMargin = 58; "
        "$d.SaveAs2('%s', 16); $d.Close($false) } finally { $w.Quit() }" % (tmp, out))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    os.remove(tmp)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
