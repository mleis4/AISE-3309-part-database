# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         generate_data.py
# Description:     Assignment 3, Task 3: fabricates a realistic-sized, joinable
#                  data set for the Engineering Part Sourcer and writes it as
#                  multi-row INSERT statements:
#                    - SRC/load_data.sql  (run after SQL/task3.sql)
#                    - SRC/samples.md     (about 5 related rows per relation,
#                                          for the report)
#                  Every key, foreign key and constraint C1 to C7 is asserted
#                  in Python before anything is written, because the database
#                  does not enforce C3, C4 and C5 (no triggers; see task3.sql).
#                  The data is mock data: names look realistic, but every part,
#                  price and customer is invented.
#
# Run:             python SRC/generate_data.py      (from Assignment3/)
#                  stdlib only; a fixed seed gives identical output every run.
# ------------------------------------------------------------------------------
import hashlib
import os
import random
import sys
from datetime import date, datetime, timedelta

SEED = 3309
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_SQL = os.path.join(SCRIPT_DIR, "load_data.sql")
OUT_SAMPLES = os.path.join(SCRIPT_DIR, "samples.md")
BATCH = 500

# Target sizes (the handout asks for >= 2 relations with thousands of tuples
# and >= 1 with hundreds)
N_CUSTOMERS = 300
N_PARTS = 3000
N_BOMS = 800
N_BOMLINES = 4000
N_SHARED = 150
N_CARTS = 200
N_CARTLINES = 1200
N_REVIEWS = 1500
N_ALTERNATIVES = 500
P_PART_UNLISTED = 0.12        # parts no distributor sells
P_EXTRA_PACKAGING = 0.20      # (distributor, part) pairs with 2-3 packagings
P_OUT_OF_STOCK = 0.12
P_LINE_SELECTED = 0.72        # BOM lines (with a listed part) that have a supplier chosen
TODAY = date(2026, 11, 25)

# ------------------------------------------------------------------------------
# Reference lists (mock but realistic-looking)
# All key strings use only letters, digits, spaces and hyphens, and are
# compared in lower case, so Python's ordering and uniqueness agree with
# MySQL's case-insensitive utf8mb4_0900_ai_ci collation.
# ------------------------------------------------------------------------------
DISTRIBUTORS = [  # name, website, shipping fee, SKU prefix, price factor
    ("DigiKey", "https://www.digikey.ca", 8.99, "DK", 1.00),
    ("Mouser", "https://www.mouser.ca", 7.99, "MO", 0.98),
    ("Arrow", "https://www.arrow.com", 0.00, "AR", 1.03),
    ("Newark", "https://canada.newark.com", 9.50, "NW", 1.05),
    ("LCSC", "https://www.lcsc.com", 4.50, "LC", 0.62),
    ("RS Components", "https://ca.rs-online.com", 10.00, "RS", 1.08),
    ("TME", "https://www.tme.eu", 12.00, "TM", 0.90),
    ("Farnell", "https://uk.farnell.com", 11.25, "FA", 1.06),
    ("Allied Electronics", "https://www.alliedelec.com", 9.00, "AL", 1.10),
    ("Future Electronics", "https://www.futureelectronics.com", 6.00, "FE", 0.97),
    ("Avnet", "https://www.avnet.com", 0.00, "AV", 1.02),
    ("Sager Electronics", "https://www.sager.com", 7.25, "SG", 1.04),
    ("Jameco", "https://www.jameco.com", 5.95, "JM", 1.12),
    ("Adafruit", "https://www.adafruit.com", 6.50, "AD", 1.25),
    ("SparkFun", "https://www.sparkfun.com", 6.75, "SF", 1.22),
]

# category: (weight, base price range, SKU code, manufacturers, name builder key)
CATEGORIES = {
    "Resistor":          (22, (0.01, 0.40), "RC", ["Yageo", "Vishay", "Bourns", "Panasonic", "Samsung"]),
    "Capacitor":         (20, (0.02, 1.80), "CC", ["Murata", "Kemet", "TDK", "Samsung", "Yageo", "Panasonic"]),
    "Inductor":          (6, (0.08, 2.50), "IN", ["TDK", "Murata", "Bourns", "Wurth Elektronik"]),
    "Diode":             (7, (0.03, 0.90), "DI", ["Vishay", "onsemi", "Nexperia", "Diodes Inc"]),
    "Transistor":        (7, (0.04, 2.20), "TR", ["onsemi", "Nexperia", "Infineon", "STMicroelectronics"]),
    "MCU":               (5, (0.60, 18.00), "MC", ["STMicroelectronics", "Microchip", "NXP", "Espressif", "Texas Instruments"]),
    "Op-Amp":            (4, (0.20, 6.50), "OA", ["Texas Instruments", "Analog Devices", "Microchip", "STMicroelectronics"]),
    "Voltage Regulator": (5, (0.15, 5.00), "VR", ["Texas Instruments", "Analog Devices", "onsemi", "Diodes Inc"]),
    "Connector":         (8, (0.10, 7.50), "CN", ["Molex", "TE Connectivity", "Wurth Elektronik", "Amphenol"]),
    "Crystal":           (3, (0.15, 2.00), "XT", ["Abracon", "Epson", "ECS"]),
    "LED":               (4, (0.03, 1.20), "LD", ["Kingbright", "Lite-On", "Wurth Elektronik"]),
    "Sensor":            (4, (0.50, 25.00), "SN", ["Bosch", "Texas Instruments", "Analog Devices", "Sensirion"]),
    "Fuse":              (2, (0.10, 3.00), "FU", ["Littelfuse", "Bourns", "Eaton"]),
    "Switch":            (2, (0.10, 4.00), "SW", ["CK", "E-Switch", "Omron"]),
    "Mechanical":        (1, (0.05, 3.50), "ME", ["Keystone", "Wurth Elektronik", "Essentra"]),
}
PACKAGES = ["0402", "0603", "0805", "1206", "SOT-23", "SOIC-8", "QFN-32", "TO-220", "DIP-8", "LQFP-48"]
PACKAGINGS = ["Cut Tape", "Tape & Reel", "Tray", "Bulk", "Tube"]  # must match ck_Listing_pack
PACK_FACTOR = {"Cut Tape": 1.00, "Tape & Reel": 0.82, "Tray": 0.90, "Bulk": 0.88, "Tube": 0.93}

# Generic parts made by several manufacturers (the reason Part has a composite key)
GENERIC_PARTS = [
    ("Vishay", "1N4148", "Diode", "1N4148 Small Signal Diode 100V"),
    ("onsemi", "1N4148", "Diode", "1N4148 Small Signal Diode 100V"),
    ("Nexperia", "1N4148", "Diode", "1N4148 Small Signal Diode 100V"),
    ("onsemi", "2N3904", "Transistor", "2N3904 NPN General Purpose Transistor"),
    ("Nexperia", "2N3904", "Transistor", "2N3904 NPN General Purpose Transistor"),
    ("Texas Instruments", "LM358", "Op-Amp", "LM358 Dual Op-Amp"),
    ("STMicroelectronics", "LM358", "Op-Amp", "LM358 Dual Op-Amp"),
    ("Texas Instruments", "NE555", "Sensor", "NE555 Precision Timer"),
    ("STMicroelectronics", "NE555", "Sensor", "NE555 Precision Timer"),
    ("STMicroelectronics", "L7805", "Voltage Regulator", "L7805 5V 1.5A Linear Regulator"),
    ("onsemi", "L7805", "Voltage Regulator", "L7805 5V 1.5A Linear Regulator"),
]

FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Avery", "Quinn",
         "Priya", "Wei", "Omar", "Fatima", "Lucas", "Sofia", "Noah", "Emma", "Liam", "Olivia",
         "Arjun", "Mei", "Hassan", "Leila", "Ethan", "Chloe", "Daniel", "Grace", "Ravi", "Aisha"]
LAST = ["Chen", "Patel", "Smith", "Nguyen", "Brown", "Singh", "Martin", "Li", "Wilson", "Khan",
        "Tremblay", "Roy", "Gagnon", "Lee", "Wong", "Taylor", "Campbell", "Ali", "Kumar", "Park"]
CITIES = [("London", "Ontario", "N6A"), ("Toronto", "Ontario", "M5V"), ("Waterloo", "Ontario", "N2L"),
          ("Ottawa", "Ontario", "K1P"), ("Montreal", "Quebec", "H3A"), ("Vancouver", "British Columbia", "V6B"),
          ("Calgary", "Alberta", "T2P"), ("Halifax", "Nova Scotia", "B3H"), ("Winnipeg", "Manitoba", "R3C")]
STREETS = ["Richmond St", "Oxford St", "Wharncliffe Rd", "King St", "Queen St", "Main St",
           "Western Rd", "Dundas St", "University Ave", "Elm St"]
PROJECT_WORDS = ["Weather Station", "Drone Flight Controller", "Line Follower Robot", "Smart Thermostat",
                 "LED Matrix Clock", "Bench Power Supply", "Guitar Pedal", "Soil Moisture Logger",
                 "CAN Bus Sniffer", "Mini Synth", "Battery Charger", "Motor Driver Board",
                 "Air Quality Monitor", "Capstone Prototype", "IoT Door Sensor", "Solar Tracker",
                 "Ham Radio Kit", "Keyboard PCB", "3D Printer Mainboard", "Lab Signal Generator"]
BOM_SUFFIXES = ["v1", "v2", "v3", "Rev A", "Rev B", "Final", "Test"]
REVIEW_TEXT = {
    1: ["Arrived dead on arrival.", "Does not match the datasheet.", "Overheats at rated current."],
    2: ["Works but tolerance is worse than stated.", "Pins bent in packaging."],
    3: ["Does the job.", "Average part, nothing special.", "Fine for prototyping."],
    4: ["Reliable, would buy again.", "Good value for the price.", "Easy to solder."],
    5: ["Excellent part, exactly as specified.", "Used it in three builds without a failure.",
        "Best option in this category."],
}


# ------------------------------------------------------------------------------
# Generation
# ------------------------------------------------------------------------------
def money(x):
    return round(x + 1e-9, 2)


def rand_date(rng, start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def gen_customers(rng):
    rows, emails, usernames = [], set(), set()
    for i in range(N_CUSTOMERS):
        f, l = FIRST[i % len(FIRST)], LAST[(i * 7) % len(LAST)]
        email = "%s.%s%d@example.com" % (f.lower(), l.lower(), i)
        user = "%s%s%d" % (f[0].lower(), l.lower(), i)
        city, prov, fsa = CITIES[rng.randrange(len(CITIES))]
        pw = hashlib.sha256(("mock-password-%d" % i).encode()).hexdigest()
        rows.append(dict(Email=email, Username=user, Password=pw, FirstName=f, LastName=l,
                         HouseAddress="%d %s" % (rng.randint(1, 2400), rng.choice(STREETS)),
                         UnitNum=str(rng.randint(100, 2200)) if rng.random() < 0.25 else None,
                         City=city, Province=prov, Country="Canada",
                         PostCode="%s %d%s%d" % (fsa, rng.randint(0, 9), chr(65 + rng.randint(0, 25)),
                                                 rng.randint(0, 9))))
        emails.add(email.lower())
        usernames.add(user.lower())
    return rows


def part_name(rng, cat, num):
    pkg = rng.choice(PACKAGES)
    if cat == "Resistor":
        v = rng.choice(["10", "47", "100", "220", "1k", "4.7k", "10k", "47k", "100k", "1M"])
        return "%s Ohm %s Resistor %s" % (v, pkg, rng.choice(["1%", "5%", "0.1%"]))
    if cat == "Capacitor":
        v = rng.choice(["10pF", "100pF", "1nF", "10nF", "100nF", "1uF", "4.7uF", "10uF", "47uF"])
        return "%s %s %s Capacitor %sV" % (v, pkg, rng.choice(["X7R", "X5R", "C0G"]), rng.choice([6, 16, 25, 50]))
    if cat == "Inductor":
        return "%suH Power Inductor %s" % (rng.choice([1, 2.2, 4.7, 10, 22, 47]), pkg)
    if cat == "MCU":
        return "%s-bit Microcontroller %dKB Flash %s" % (rng.choice([8, 32]), rng.choice([32, 64, 128, 256, 512]), pkg)
    if cat == "Connector":
        return "%d-Pin %s Header %smm" % (rng.randint(2, 40), rng.choice(["Male", "Female", "Right-Angle"]),
                                         rng.choice(["2.54", "1.27", "2.00"]))
    if cat == "Mechanical":
        return "M%d %s %dmm" % (rng.choice([2, 3, 4]), rng.choice(["Standoff", "Screw", "Nut", "Spacer"]),
                                rng.randint(4, 30))
    return "%s %s %d" % (cat, pkg, num)


def gen_parts(rng):
    rows, keys = [], set()
    for man, num, cat, name in GENERIC_PARTS:
        rows.append(dict(ManufacturerName=man, Manufacturer_PartNum=num, Name=name,
                         Description="Generic industry-standard part, second-sourced by several manufacturers.",
                         Category=cat, Length=None, Width=None, Height=None,
                         Datasheet_link="https://datasheets.example.com/%s/%s.pdf" % (man.replace(" ", "-").lower(), num)))
        keys.add((man.lower(), num.lower()))
    cats = list(CATEGORIES)
    weights = [CATEGORIES[c][0] for c in cats]
    n = 0
    while len(rows) < N_PARTS:
        cat = rng.choices(cats, weights)[0]
        _, _, code, mans = CATEGORIES[cat]
        man = rng.choice(mans)
        n += 1
        num = "%s%05d-%s" % (code, 10000 + n * 7 % 90000, rng.choice("ABCDEFGHJK"))
        key = (man.lower(), num.lower())
        if key in keys:
            continue
        keys.add(key)
        has_dims = rng.random() < 0.85
        rows.append(dict(
            ManufacturerName=man, Manufacturer_PartNum=num, Name=part_name(rng, cat, n),
            Description=("%s by %s, mock catalogue entry %d." % (cat, man, n)) if rng.random() < 0.8 else None,
            Category=cat,
            Length=money(rng.uniform(0.5, 60)) if has_dims else None,
            Width=money(rng.uniform(0.3, 40)) if has_dims else None,
            Height=money(rng.uniform(0.2, 20)) if has_dims else None,
            Datasheet_link=("https://datasheets.example.com/%s/%s.pdf" % (man.replace(" ", "-").lower(), num.lower()))
            if rng.random() < 0.9 else None))
    return rows


def gen_distributors():
    return [dict(Name=n, Website=w, ShippingFee=fee) for n, w, fee, _, _ in DISTRIBUTORS]


def gen_listings(rng, parts):
    rows, pk, ak = [], set(), set()
    counters = {d[0]: 0 for d in DISTRIBUTORS}
    for i, p in enumerate(parts):
        if i >= len(GENERIC_PARTS) and rng.random() < P_PART_UNLISTED:
            continue
        lo, hi = CATEGORIES[p["Category"]][1]
        base = rng.uniform(lo, hi)
        k = rng.choices([1, 2, 3, 4], [30, 40, 20, 10])[0]
        for dname, _, _, prefix, factor in rng.sample(DISTRIBUTORS, k):
            n_pack = 1 if rng.random() >= P_EXTRA_PACKAGING else rng.choice([2, 3])
            for packaging in rng.sample(PACKAGINGS, n_pack):
                counters[dname] += 1
                sku = "%s-%06d" % (prefix, counters[dname] * 13)
                stock = 0 if rng.random() < P_OUT_OF_STOCK else rng.choice(
                    [rng.randint(1, 50), rng.randint(50, 5000), rng.randint(5000, 250000)])
                # 06:00-21:59 only: a TIMESTAMP in the 02:00-03:00 hour of a
                # daylight-saving switch does not exist in local time (error 1292)
                updated = datetime(2025, 11, 25) + timedelta(days=rng.randint(0, 364), hours=rng.randint(6, 21),
                                                             minutes=rng.randint(0, 59))
                rows.append(dict(DistributorName=dname, Distributor_PartNum=sku,
                                 ManufacturerName=p["ManufacturerName"],
                                 Manufacturer_PartNum=p["Manufacturer_PartNum"], Packaging=packaging,
                                 UnitPrice=max(0.01, money(base * factor * PACK_FACTOR[packaging])),
                                 StockQuantity=stock, EstShipTime=rng.randint(1, 14),
                                 LastUpdated=updated.replace(second=0)))
                pk.add((dname.lower(), sku.lower()))
                ak.add((dname.lower(), p["ManufacturerName"].lower(), p["Manufacturer_PartNum"].lower(),
                        packaging.lower()))
    return rows


def gen_boms(rng, customers):
    # Customer 0 is the "showcase" customer used for the report samples.
    owners = [c["Email"] for c in customers[:240]]       # customers 240+ have no BOM
    rows, keys = [], set()
    per = {e: 0 for e in owners}
    showcase = customers[0]["Email"]
    for name in ["Weather Station v2", "Line Follower Robot", "Capstone Prototype", "Empty Draft"]:
        rows.append(dict(CustomerEmail=showcase, BOM_name=name, Date_created=date(2026, 3, 1) + timedelta(days=20 * len(rows))))
        keys.add((showcase.lower(), name.lower()))
    while len(rows) < N_BOMS:
        e = rng.choice(owners)
        per[e] += 1
        name = "%s %s" % (rng.choice(PROJECT_WORDS), rng.choice(BOM_SUFFIXES))
        if (e.lower(), name.lower()) in keys:
            continue
        keys.add((e.lower(), name.lower()))
        rows.append(dict(CustomerEmail=e, BOM_name=name, Date_created=rand_date(rng, date(2025, 1, 1), TODAY)))
    return rows


def gen_bomlines(rng, boms, parts, listed_parts):
    pkeys = [(p["ManufacturerName"], p["Manufacturer_PartNum"]) for p in parts]
    listed = [k for k in pkeys if k in listed_parts]
    empty = {(b["CustomerEmail"], b["BOM_name"]) for b in boms if b["BOM_name"] == "Empty Draft"}
    empty |= {(b["CustomerEmail"], b["BOM_name"]) for b in rng.sample(boms[4:], 40)}   # ~5% empty BOMs
    rows, keys = [], set()
    fillable = [b for b in boms if (b["CustomerEmail"], b["BOM_name"]) not in empty]
    # every non-empty BOM gets at least one line, then the rest at random
    order = fillable + [rng.choice(fillable) for _ in range(N_BOMLINES * 2)]
    for b in order:
        if len(rows) >= N_BOMLINES:
            break
        part = rng.choice(listed) if rng.random() < 0.9 else rng.choice(pkeys)
        key = (b["CustomerEmail"].lower(), b["BOM_name"].lower(), part[0].lower(), part[1].lower())
        if key in keys:
            continue
        keys.add(key)
        rows.append(dict(CustomerEmail=b["CustomerEmail"], BOM_name=b["BOM_name"], ManufacturerName=part[0],
                         Manufacturer_PartNum=part[1], Quantity=rng.choice([1, 1, 2, 4, 5, 10, 10, 20, 25, 50, 100])))
    return rows


def gen_selections(rng, bomlines, listings_by_part):
    rows = []
    for line in bomlines:
        offers = listings_by_part.get((line["ManufacturerName"], line["Manufacturer_PartNum"]))
        if not offers or rng.random() >= P_LINE_SELECTED:
            continue                       # leave unselected: counts in /UnpricedParts
        offer = min(offers, key=lambda l: l["UnitPrice"]) if rng.random() < 0.5 else rng.choice(offers)
        rows.append(dict(CustomerEmail=line["CustomerEmail"], BOM_name=line["BOM_name"],
                         DistributorName=offer["DistributorName"], Distributor_PartNum=offer["Distributor_PartNum"]))
    return rows


def gen_shared(rng, boms, bomlines):
    with_lines = {(l["CustomerEmail"], l["BOM_name"]) for l in bomlines}
    candidates = [b for b in boms if (b["CustomerEmail"], b["BOM_name"]) in with_lines]
    showcase = [b for b in candidates if b["CustomerEmail"] == boms[0]["CustomerEmail"]][:2]
    chosen = showcase + rng.sample([b for b in candidates if b not in showcase], N_SHARED - len(showcase))
    rows, titles = [], set()
    for b in chosen:
        base = b["BOM_name"]
        for suffix in BOM_SUFFIXES:                   # "Battery Charger Rev A" -> "Battery Charger"
            if base.endswith(" " + suffix):
                base = base[:-len(suffix) - 1]
                break
        title, n = "Open %s" % base, 2
        while (b["CustomerEmail"].lower(), title.lower()) in titles:
            title = "Open %s %d" % (base, n)
            n += 1
        titles.add((b["CustomerEmail"].lower(), title.lower()))
        shared = b["Date_created"] + timedelta(days=rng.randint(1, 60))
        rows.append(dict(CustomerEmail=b["CustomerEmail"], BOM_name=b["BOM_name"], Title=title,
                         Description=("Parts list for my %s build. Feel free to copy it." % base.lower())
                         if rng.random() < 0.85 else None,
                         Date_shared=min(shared, TODAY)))
    return rows


def gen_carts(rng, customers):
    chosen = [customers[0]] + rng.sample(customers[1:], N_CARTS - 1)
    return [dict(CustomerEmail=c["Email"], Date_created=rand_date(rng, date(2026, 6, 1), TODAY)) for c in chosen]


def gen_cartlines(rng, carts, listings):
    rows, keys = [], set()
    empty = set(c["CustomerEmail"] for c in rng.sample(carts[1:], 15))   # some empty carts
    full = [c for c in carts if c["CustomerEmail"] not in empty]
    while len(rows) < N_CARTLINES:
        c = rng.choice(full)
        l = rng.choice(listings)
        key = (c["CustomerEmail"].lower(), l["DistributorName"].lower(), l["Distributor_PartNum"].lower())
        if key in keys:
            continue
        keys.add(key)
        rows.append(dict(CustomerEmail=c["CustomerEmail"], DistributorName=l["DistributorName"],
                         Distributor_PartNum=l["Distributor_PartNum"], Quantity=rng.choice([1, 2, 5, 10, 25, 50])))
    return rows


def gen_reviews(rng, customers, parts):
    pkeys = [(p["ManufacturerName"], p["Manufacturer_PartNum"]) for p in parts]
    popular = pkeys[:len(GENERIC_PARTS)] + rng.sample(pkeys[len(GENERIC_PARTS):], 120)
    quality = {k: rng.choice([1.5, 2.5, 3.5, 4.2, 4.6]) for k in pkeys}
    rows, keys = [], set()
    while len(rows) < N_REVIEWS:
        c = rng.choice(customers)["Email"]
        part = rng.choice(popular) if rng.random() < 0.6 else rng.choice(pkeys)
        key = (c.lower(), part[0].lower(), part[1].lower())
        if key in keys:
            continue
        keys.add(key)
        stars = min(5, max(1, int(round(rng.gauss(quality[part], 0.8)))))
        rows.append(dict(CustomerEmail=c, ManufacturerName=part[0], Manufacturer_PartNum=part[1],
                         ReviewText=rng.choice(REVIEW_TEXT[stars]) if rng.random() < 0.8 else None,
                         StarRating=stars))
    return rows


def sort_key(part):
    """Matches MySQL's (a, b) < (c, d) under the case-insensitive collation."""
    return (part[0].lower(), part[1].lower())


def gen_alternatives(rng, parts):
    by_cat = {}
    for p in parts:
        by_cat.setdefault(p["Category"], []).append((p["ManufacturerName"], p["Manufacturer_PartNum"]))
    rows, keys = [], set()
    # generic parts: every second source is an alternative to the others
    generic = {}
    for man, num, _, _ in GENERIC_PARTS:
        generic.setdefault(num, []).append((man, num))
    pairs = [(a, b) for group in generic.values() for i, a in enumerate(group) for b in group[i + 1:]]
    cats = list(by_cat)
    while len(pairs) < N_ALTERNATIVES * 2:
        group = by_cat[rng.choice(cats)]
        pairs.append(tuple(rng.sample(group, 2)))
    for a, b in pairs:
        if len(rows) >= N_ALTERNATIVES:
            break
        first, second = sorted([a, b], key=sort_key)     # C4: smaller key first
        key = sort_key(first) + sort_key(second)
        if key in keys or sort_key(first) == sort_key(second):
            continue
        keys.add(key)
        rows.append(dict(Part1_ManufacturerName=first[0], Part1_PartNum=first[1],
                         Part2_ManufacturerName=second[0], Part2_PartNum=second[1]))
    return rows


# ------------------------------------------------------------------------------
# Checks: every rule the database does not (or cannot) enforce for us
# ------------------------------------------------------------------------------
def k(row, cols):
    return tuple(str(row[c]).lower() for c in cols)


def assert_unique(name, rows, cols):
    seen = set()
    for r in rows:
        key = k(r, cols)
        assert key not in seen, "duplicate %s key %s" % (name, key)
        seen.add(key)
    return seen


def assert_fk(name, rows, cols, parent_keys):
    for r in rows:
        assert k(r, cols) in parent_keys, "orphan %s row %s" % (name, k(r, cols))


def check_all(d):
    PK = ["ManufacturerName", "Manufacturer_PartNum"]
    BK = ["CustomerEmail", "BOM_name"]
    LK = ["DistributorName", "Distributor_PartNum"]
    cust = assert_unique("Customer", d["Customer"], ["Email"])
    assert_unique("Customer AK", d["Customer"], ["Username"])
    part = assert_unique("Part", d["Part"], PK)
    dist = assert_unique("Distributor", d["Distributor"], ["Name"])
    assert_unique("Distributor AK", d["Distributor"], ["Website"])
    lst = assert_unique("Listing", d["Listing"], LK)
    assert_unique("Listing AK (C2)", d["Listing"], ["DistributorName"] + PK + ["Packaging"])
    assert_fk("Listing", d["Listing"], ["DistributorName"], dist)
    assert_fk("Listing", d["Listing"], PK, part)
    cart = assert_unique("ShoppingCart", d["ShoppingCart"], ["CustomerEmail"])
    assert_fk("ShoppingCart", d["ShoppingCart"], ["CustomerEmail"], cust)
    bom = assert_unique("BOM", d["BOM"], BK)
    assert_fk("BOM", d["BOM"], ["CustomerEmail"], cust)
    assert_unique("SharedProject", d["SharedProject"], BK)
    assert_unique("SharedProject AK", d["SharedProject"], ["CustomerEmail", "Title"])
    assert_fk("SharedProject", d["SharedProject"], BK, bom)
    assert_unique("PartAlternative", d["PartAlternative"],
                  ["Part1_ManufacturerName", "Part1_PartNum", "Part2_ManufacturerName", "Part2_PartNum"])
    assert_fk("PartAlternative", d["PartAlternative"], ["Part1_ManufacturerName", "Part1_PartNum"], part)
    assert_fk("PartAlternative", d["PartAlternative"], ["Part2_ManufacturerName", "Part2_PartNum"], part)
    line = assert_unique("BOMLine", d["BOMLine"], BK + PK)
    assert_fk("BOMLine", d["BOMLine"], BK, bom)
    assert_fk("BOMLine", d["BOMLine"], PK, part)
    assert_unique("BOMSelection", d["BOMSelection"], BK + LK)
    assert_fk("BOMSelection", d["BOMSelection"], BK, bom)
    assert_fk("BOMSelection", d["BOMSelection"], LK, lst)
    assert_unique("CartLine", d["CartLine"], ["CustomerEmail"] + LK)
    assert_fk("CartLine", d["CartLine"], ["CustomerEmail"], cart)
    assert_fk("CartLine", d["CartLine"], LK, lst)
    assert_unique("Review (C6)", d["Review"], ["CustomerEmail"] + PK)
    assert_fk("Review", d["Review"], ["CustomerEmail"], cust)
    assert_fk("Review", d["Review"], PK, part)

    # C1
    assert all(1 <= r["StarRating"] <= 5 for r in d["Review"])
    assert all(r["Quantity"] > 0 for r in d["BOMLine"] + d["CartLine"])
    assert all(r["UnitPrice"] >= 0 and r["StockQuantity"] >= 0 for r in d["Listing"])
    assert all(r["ShippingFee"] >= 0 for r in d["Distributor"])
    assert all(r["Packaging"] in PACKAGINGS for r in d["Listing"])
    # C3: the selected listing's part is a line of the same BOM, one selection per part
    part_of = {k(l, LK): k(l, PK) for l in d["Listing"]}
    per_part = set()
    for s in d["BOMSelection"]:
        p = part_of[k(s, LK)]
        assert k(s, BK) + p in line, "C3: selection without a line %s" % (k(s, BK + LK),)
        assert k(s, BK) + p not in per_part, "C3: two selections for one part %s" % (k(s, BK),)
        per_part.add(k(s, BK) + p)
    # C4
    for a in d["PartAlternative"]:
        first = sort_key((a["Part1_ManufacturerName"], a["Part1_PartNum"]))
        second = sort_key((a["Part2_ManufacturerName"], a["Part2_PartNum"]))
        assert first < second, "C4 violated %s" % (a,)
    # C5
    bom_with_lines = {k(l, BK) for l in d["BOMLine"]}
    assert all(k(s, BK) in bom_with_lines for s in d["SharedProject"]), "C5 violated"
    # lengths fit the column types in task3.sql
    for r in d["Customer"]:
        assert len(r["Email"]) <= 254 and len(r["Username"]) <= 30 and len(r["PostCode"]) <= 10
    for r in d["Part"]:
        assert len(r["Name"]) <= 100 and len(r["Manufacturer_PartNum"]) <= 60
    for r in d["BOM"]:
        assert len(r["BOM_name"]) <= 100
    for r in d["SharedProject"]:
        assert len(r["Title"]) <= 100 and r["Date_shared"] >= [b for b in d["BOM"] if k(b, BK) == k(r, BK)][0]["Date_created"]


# ------------------------------------------------------------------------------
# Output
# ------------------------------------------------------------------------------
COLUMNS = {
    "Customer": ["Email", "Username", "Password", "FirstName", "LastName", "HouseAddress", "UnitNum",
                 "City", "Province", "Country", "PostCode"],
    "Part": ["ManufacturerName", "Manufacturer_PartNum", "Name", "Description", "Category", "Length",
             "Width", "Height", "Datasheet_link"],
    "Distributor": ["Name", "Website", "ShippingFee"],
    "Listing": ["DistributorName", "Distributor_PartNum", "ManufacturerName", "Manufacturer_PartNum",
                "Packaging", "UnitPrice", "StockQuantity", "EstShipTime", "LastUpdated"],
    "ShoppingCart": ["CustomerEmail", "Date_created"],
    "BOM": ["CustomerEmail", "BOM_name", "Date_created"],
    "SharedProject": ["CustomerEmail", "BOM_name", "Title", "Description", "Date_shared"],
    "PartAlternative": ["Part1_ManufacturerName", "Part1_PartNum", "Part2_ManufacturerName", "Part2_PartNum"],
    "BOMLine": ["CustomerEmail", "BOM_name", "ManufacturerName", "Manufacturer_PartNum", "Quantity"],
    "BOMSelection": ["CustomerEmail", "BOM_name", "DistributorName", "Distributor_PartNum"],
    "CartLine": ["CustomerEmail", "DistributorName", "Distributor_PartNum", "Quantity"],
    "Review": ["CustomerEmail", "ManufacturerName", "Manufacturer_PartNum", "ReviewText", "StarRating"],
}
ORDER = list(COLUMNS)   # parents before children


def sql_value(v):
    if v is None:
        return "NULL"
    if isinstance(v, datetime):
        return "TIMESTAMP '%s'" % v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return "DATE '%s'" % v.isoformat()
    if isinstance(v, float):
        return "%.2f" % v
    if isinstance(v, int):
        return str(v)
    s = str(v)
    assert "\\" not in s and s.isascii(), s
    return "'%s'" % s.replace("'", "''")


def write_sql(d):
    out = ["-- load_data.sql: Task 3, fabricated (mock) data for the Engineering Part Sourcer",
           "-- Generated by SRC/generate_data.py (seed %d). Do not edit by hand." % SEED,
           "-- Run after SQL/task3.sql. Every FK value refers to a row inserted earlier.",
           "-- Row counts: " + ", ".join("%s %d" % (t, len(d[t])) for t in ORDER),
           "",
           "START TRANSACTION;",
           ""]
    for t in ORDER:
        cols = COLUMNS[t]
        rows = d[t]
        out.append("-- %s (%d rows)" % (t, len(rows)))
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i + BATCH]
            out.append("INSERT INTO %s (%s) VALUES" % (t, ", ".join(cols)))
            out.append(",\n".join("(%s)" % ", ".join(sql_value(r[c]) for c in cols) for r in chunk) + ";")
        out.append("")
    out.append("COMMIT;")
    with open(OUT_SQL, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def md_table(rows, cols):
    def cell(v):
        if v is None:
            return "NULL"
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M")
        if isinstance(v, float):
            return "%.2f" % v
        s = str(v)
        return (s[:40] + "...") if len(s) > 43 else s.replace("|", "\\|")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def write_samples(d):
    show = d["Customer"][0]["Email"]
    boms = [b for b in d["BOM"] if b["CustomerEmail"] == show]
    lines = [l for l in d["BOMLine"] if l["CustomerEmail"] == show][:5]
    line_parts = {(l["ManufacturerName"], l["Manufacturer_PartNum"]) for l in lines}
    sels = [s for s in d["BOMSelection"] if s["CustomerEmail"] == show][:5]
    sel_keys = {(s["DistributorName"], s["Distributor_PartNum"]) for s in sels}
    listings = [l for l in d["Listing"] if (l["DistributorName"], l["Distributor_PartNum"]) in sel_keys]
    listings += [l for l in d["Listing"] if (l["ManufacturerName"], l["Manufacturer_PartNum"]) in line_parts
                 and l not in listings]
    parts = [p for p in d["Part"] if (p["ManufacturerName"], p["Manufacturer_PartNum"]) in line_parts]
    dnames = [l["DistributorName"] for l in listings[:5]]
    dists = [x for x in d["Distributor"] if x["Name"] in dnames][:5]
    cartlines = [c for c in d["CartLine"] if c["CustomerEmail"] == show][:5]
    carts = [d["ShoppingCart"][0]] + d["ShoppingCart"][1:5]
    reviews = [r for r in d["Review"] if r["ManufacturerName"] == "Vishay" and r["Manufacturer_PartNum"] == "1N4148"]
    reviews = (reviews + [r for r in d["Review"] if r["CustomerEmail"] == show])[:5]
    alts = d["PartAlternative"][:5]
    shared = [s for s in d["SharedProject"] if s["CustomerEmail"] == show] + d["SharedProject"][2:5]
    sections = [
        ("Customer", [d["Customer"][0]] + d["Customer"][1:5], "The first row is the showcase customer that the rows below belong to."),
        ("Part", (parts + d["Part"][:5])[:5], "Parts in the showcase customer's BOM lines (generic second-sourced parts fill in if needed)."),
        ("Distributor", dists, "Distributors of the listings below."),
        ("Listing", listings[:5], "The listings the showcase BOMs selected, then other offers for the same parts."),
        ("ShoppingCart", carts, "The first cart is the showcase customer's."),
        ("BOM", boms[:5], "\"Empty Draft\" has no lines on purpose (edge case: /NumberOfParts = 0)."),
        ("SharedProject", shared[:5], "Only BOMs with at least one line are shared (C5)."),
        ("PartAlternative", alts, "Each pair is stored once with the smaller part key first (C4)."),
        ("BOMLine", lines, "Lines of the showcase customer's BOMs."),
        ("BOMSelection", sels, "The listing chosen for some of those lines; the other lines are unpriced."),
        ("CartLine", cartlines, "Lines in the showcase customer's cart."),
        ("Review", reviews, "Reviews of the generic part Vishay 1N4148, then the showcase customer's reviews."),
    ]
    out = ["# Task 3: sample records",
           "",
           "_Generated by `SRC/generate_data.py` (seed %d). Mock data: every name, price and address is invented._" % SEED,
           "",
           "| Relation | Rows loaded |", "|---|---|"]
    out += ["| %s | %d |" % (t, len(d[t])) for t in ORDER]
    out.append("")
    for t, rows, note in sections:
        cols = [c for c in COLUMNS[t] if not (t == "Customer" and c == "Password")]
        out += ["## %s" % t, "", note, "", md_table(rows, cols), ""]
    out.append("Customer.Password holds a mock SHA-256 hash and is left out of the sample above.")
    with open(OUT_SAMPLES, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def main():
    rng = random.Random(SEED)
    d = {}
    d["Customer"] = gen_customers(rng)
    d["Part"] = gen_parts(rng)
    d["Distributor"] = gen_distributors()
    d["Listing"] = gen_listings(rng, d["Part"])
    by_part = {}
    for l in d["Listing"]:
        by_part.setdefault((l["ManufacturerName"], l["Manufacturer_PartNum"]), []).append(l)
    d["ShoppingCart"] = gen_carts(rng, d["Customer"])
    d["BOM"] = gen_boms(rng, d["Customer"])
    d["BOMLine"] = gen_bomlines(rng, d["BOM"], d["Part"], set(by_part))
    d["BOMSelection"] = gen_selections(rng, d["BOMLine"], by_part)
    d["SharedProject"] = gen_shared(rng, d["BOM"], d["BOMLine"])
    d["PartAlternative"] = gen_alternatives(rng, d["Part"])
    d["CartLine"] = gen_cartlines(rng, d["ShoppingCart"], d["Listing"])
    d["Review"] = gen_reviews(rng, d["Customer"], d["Part"])
    check_all(d)
    write_sql(d)
    write_samples(d)
    for t in ORDER:
        print("%-16s %6d" % (t, len(d[t])))
    print("wrote", OUT_SQL)
    print("wrote", OUT_SAMPLES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
