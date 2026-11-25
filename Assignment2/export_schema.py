# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         export_schema.py
# Description:     Exports the Assignment 2 diagrams drawn by build_report.py as
#                  plain text that an LLM agent can read reliably:
#                    - diagrams/text/schema.json  (machine-readable, every fact)
#                    - diagrams/text/DIAGRAMS.md  (readable walk-through of each
#                                                  figure, plus a Mermaid ER view)
#                  Nothing is typed in twice. Facts come from three places that
#                  build_report.py already produces:
#                    1. RELS                 -> relations, keys, FKs, FDs
#                    2. the ER diagram SVG   -> entity attributes, notation legend
#                    3. the report HTML      -> entity kinds, relationships,
#                                               multiplicities, constraints
#                  It then cross-checks those sources against each other and
#                  against the SVGs on disk, and exits with code 1 on a mismatch.
#
# Run:             python export_schema.py
#                  (needs no Chrome, Word or network; does not touch the PDF/.docx)
# ------------------------------------------------------------------------------
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# Import build_report.py from the same folder as this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import build_report as report  # noqa: E402  (import after the path is set)

OUTPUT_DIR = os.path.join(report.DIAG, "text")
SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"

# The one fact not available outside build_report.main(): the merged BOMLine
# design that 3.3.3 rejects. Keep this in step with main() in build_report.py.
# (If diagrams/fd_BOMLine_merged_alternative.svg exists it is compared below.)
MERGED_BOMLINE_ATTRIBUTES = report.BOMKEY + report.PARTKEY + ["Quantity"] + report.LISTKEY
MERGED_BOMLINE_KEY = report.BOMKEY + report.PARTKEY
MERGED_BOMLINE_FDS = [(report.BOMKEY + report.PARTKEY, ["Quantity"] + report.LISTKEY),
                      (report.LISTKEY, report.PARTKEY)]

# Words for each UML multiplicity, used in the readable text
MULTIPLICITY_WORDS = {"1..1": "exactly one", "0..1": "zero or one",
                      "0..*": "zero or more", "1..*": "one or more"}

# Mermaid crow's-foot markers: (left-side marker, right-side marker)
MERMAID_MARKERS = {"1..1": ("||", "||"), "0..1": ("|o", "o|"),
                   "0..*": ("}o", "o{"), "1..*": ("}|", "|{")}


# ------------------------------------------------------------------------------
# Reading the report HTML
# ------------------------------------------------------------------------------
class TableCollector(HTMLParser):
    """Collects every <table> in an HTML page as a list of rows of cell text."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.current_table = []
        elif tag == "tr" and self.current_table is not None:
            self.current_row = []
        elif tag in ("td", "th") and self.current_row is not None:
            self.current_cell = []
        elif tag in ("li", "br") and self.current_cell is not None:
            self.current_cell.append(" ")  # keep list items apart

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.current_cell is not None:
            cell_text = " ".join("".join(self.current_cell).split())
            self.current_row.append(cell_text)
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            self.current_table.append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.current_table is not None:
            self.tables.append(self.current_table)
            self.current_table = None

    def handle_data(self, data):
        if self.current_cell is not None:
            self.current_cell.append(data)


def build_report_html():
    """Builds the report HTML in memory, without reading any SVG from disk."""
    original_fig = report.fig
    report.fig = lambda name: ""  # figures are not needed to read the tables
    try:
        return report.build_html()
    finally:
        report.fig = original_fig


def table_with_header(tables, header):
    """Returns the body rows of the first table whose first row equals header."""
    for rows in tables:
        if rows and rows[0] == header:
            return rows[1:]
    raise ValueError("Table not found in report: %s" % header)


# ------------------------------------------------------------------------------
# Reading the ER diagram SVG
# ------------------------------------------------------------------------------
def parse_erd_svg(erd_svg):
    """Returns (entities, legend_lines, all_labels) read from the ER diagram.

    build_erd() writes each entity name in 16 px bold, each attribute row in
    14 px (indented rows are components of a composite attribute) and the
    legend after a bold 14 px "Notation" title.
    """
    root = ET.fromstring(erd_svg)
    entities = []
    legend_lines = None
    all_labels = []
    current_entity = None

    for element in root.iter(SVG_NAMESPACE + "text"):
        label = element.text or ""
        font_size = element.get("font-size")
        font_weight = element.get("font-weight")
        all_labels.append(label)

        if legend_lines is not None:            # everything after the title
            legend_lines.append(label)
        elif font_size == "16" and font_weight == "bold":
            current_entity = {"name": label, "rows": []}
            entities.append(current_entity)
        elif font_size == "14" and font_weight == "bold" and label == "Notation":
            legend_lines = []
        elif font_size == "14" and current_entity is not None:
            current_entity["rows"].append((float(element.get("x")), label))

    for entity in entities:
        entity["attributes"] = rows_to_attributes(entity.pop("rows"))
    return entities, legend_lines or [], all_labels


def rows_to_attributes(rows):
    """Turns the drawn attribute rows of one entity into structured attributes."""
    left_edge = min(x for x, _ in rows)
    attributes = []
    for x, label in rows:
        key_tags = re.findall(r"\{(\w+)\}", label)
        shown_name = re.sub(r"\s*\{\w+\}", "", label).strip()
        attribute = {"name": shown_name.lstrip("/"),
                     "keys": key_tags,
                     "derived": shown_name.startswith("/")}
        if x > left_edge + 1:                   # indented: part of a composite
            attributes[-1].setdefault("components", []).append(attribute["name"])
        else:
            attributes.append(attribute)
    return attributes


# ------------------------------------------------------------------------------
# Assembling the model
# ------------------------------------------------------------------------------
def build_er_model(erd_svg, html_tables):
    """ER (conceptual) level: entities, relationships, specialization."""
    entities_drawn, legend_lines, erd_labels = parse_erd_svg(erd_svg)

    entity_rows = table_with_header(html_tables,
                                    ["Entity type", "Kind", "Identifier", "Why this identifier"])
    entity_info = {row[0]: row for row in entity_rows}

    entities = []
    for drawn in entities_drawn:
        info = entity_info.get(drawn["name"], [drawn["name"], "", "", ""])
        entities.append({"name": drawn["name"], "kind": info[1], "identifier": info[2],
                         "identifier_reason": info[3], "attributes": drawn["attributes"]})

    relationship_rows = table_with_header(html_tables,
                                          ["Relationship", "Multiplicity", "Participation", "Attributes"])
    relationships = []
    specializations = []
    for name_cell, multiplicity_cell, participation, attribute_cell in relationship_rows:
        if " / " in name_cell:                  # "BOM / SharedProject"
            superclass, subclass = name_cell.split(" / ")
            specializations.append({"superclass": superclass, "subclass": subclass,
                                    "constraint": participation,
                                    "subclass_adds": attribute_cell})
            continue
        first_entity, relationship_name, second_entity = name_cell.split()
        first_multiplicity, second_multiplicity = multiplicity_cell.split(" to ")
        relationships.append({
            "name": relationship_name,
            "ends": [{"entity": first_entity, "multiplicity": first_multiplicity},
                     {"entity": second_entity, "multiplicity": second_multiplicity}],
            "identifying": "identifying" in participation,
            "recursive": first_entity == second_entity,
            "participation": participation,
            "attributes": [] if attribute_cell == "None" else attribute_cell.split(", "),
        })

    return {
        "multiplicity_rule": ("The multiplicity at an end is how many instances of THAT end's entity "
                              "relate to ONE instance of the other end. Customer 1..1 / BOM 0..* means "
                              "every BOM has exactly one Customer and a Customer has zero or more BOMs."),
        "notation_legend": legend_lines,
        "entities": entities,
        "relationships": relationships,
        "specializations": specializations,
    }, erd_labels


def build_relations(html_tables):
    """Relational level: the 12 relations, straight from RELS."""
    fk_rows = table_with_header(html_tables,
                                ["Relation", "Foreign key", "References", "Full PK of target?", "Implements"])
    implements_lookup = {(row[0], row[1]): row[4] for row in fk_rows}

    relations = []
    for relation in report.RELS:
        candidate_keys = [relation["pk"]] + relation["aks"]

        foreign_keys = []
        for columns, target, target_columns, on_delete, reason in relation["fks"]:
            foreign_keys.append({
                "columns": columns, "references": target, "referenced_columns": target_columns,
                "on_delete": on_delete, "on_update": "CASCADE", "reason": reason,
                "implements": implements_lookup.get((relation["name"], report.cols(columns)), ""),
            })

        derived = []
        for rule_text in relation["derived"]:
            derived_name, rule = rule_text.split(" = ", 1)
            derived.append({"name": derived_name.lstrip("/"), "rule": rule})

        dependencies = []
        for number, (determinant, dependents) in enumerate(report.resolved_fds(relation), start=1):
            dependencies.append({
                "label": "FD%d" % number, "determinant": determinant, "dependents": dependents,
                "determinant_is": "PK" if determinant == relation["pk"] else
                                  "AK" if determinant in relation["aks"] else "NOT A KEY",
            })

        in_bcnf = all(fd["determinant_is"] != "NOT A KEY" for fd in dependencies)
        relations.append({
            "name": relation["name"],
            "attributes": relation["attrs"],
            "primary_key": relation["pk"],
            "alternate_keys": relation["aks"],
            "candidate_keys": candidate_keys,
            "foreign_keys": foreign_keys,
            "derived_not_stored": derived,
            "functional_dependencies": dependencies,
            "normal_forms": {"1NF": "Every attribute holds a single atomic value.",
                             "2NF": relation["nf2"], "3NF": relation["nf3"], "BCNF": in_bcnf},
            "diagram": "fd_%s.svg" % relation["name"],
        })
    return relations


def build_rejected_designs():
    """The merged BOMLine relation that section 3.3.3 rejects (Figure 3)."""
    return [{
        "name": "BOMLine (merged with BOMSelection) - REJECTED",
        "diagram": "fd_BOMLine_merged_alternative.svg",
        "attributes": MERGED_BOMLINE_ATTRIBUTES,
        "primary_key": MERGED_BOMLINE_KEY,
        "functional_dependencies": [
            {"label": "FD%d" % number, "determinant": determinant, "dependents": dependents}
            for number, (determinant, dependents) in enumerate(MERGED_BOMLINE_FDS, start=1)],
        "verdict": ("In 3NF but not BCNF: FD2's determinant (DistributorName, Distributor_PartNum) "
                    "is not a superkey. The schema keeps BOMLine and BOMSelection separate."),
    }]


def build_diagram_index(report_html):
    """Maps every diagram file to its figure caption and to the JSON that describes it."""
    captions = re.findall(r'<div class="cap">(.*?)</div>', report_html)
    caption_for = {}
    for caption in captions:
        number = re.match(r"Figure (\d+)", caption)
        if number:
            caption_for[int(number.group(1))] = caption

    index = [
        {"file": "erd_engineering_part_sourcer.svg", "figure": caption_for.get(1, ""),
         "described_by": "er_model"},
        {"file": "schema_foreign_keys.svg", "figure": caption_for.get(2, ""),
         "described_by": "relations[*].foreign_keys"},
    ]
    for relation in report.RELS:
        index.append({"file": "fd_%s.svg" % relation["name"],
                      "figure": "FD diagram of %s (section 3.3.1)" % relation["name"],
                      "described_by": "relations[name=%s].functional_dependencies" % relation["name"]})
    index.append({"file": "fd_BOMLine_merged_alternative.svg", "figure": caption_for.get(3, ""),
                  "described_by": "rejected_designs[0]"})
    return index


# ------------------------------------------------------------------------------
# Consistency checks
# ------------------------------------------------------------------------------
def fresh_svgs():
    """Every diagram exactly as build_report.py would draw it now."""
    svgs = {"erd_engineering_part_sourcer.svg": report.build_erd(),
            "schema_foreign_keys.svg": report.build_fk(),
            "fd_BOMLine_merged_alternative.svg": report.build_fd(
                MERGED_BOMLINE_ATTRIBUTES, MERGED_BOMLINE_KEY, MERGED_BOMLINE_FDS)}
    for relation in report.RELS:
        svgs["fd_%s.svg" % relation["name"]] = report.build_fd(
            relation["attrs"], relation["pk"], report.resolved_fds(relation))
    return svgs


def check_consistency(er_model, erd_labels, relations, svgs, html_tables):
    """Returns (problems, warnings). Problems mean the text export may be wrong."""
    problems, warnings = [], []
    joined_erd_text = " ".join(erd_labels)

    # 1. The ER diagram and table 1.1 list the same entities
    drawn_names = {e["name"] for e in er_model["entities"]}
    table_names = {row[0] for row in table_with_header(
        html_tables, ["Entity type", "Kind", "Identifier", "Why this identifier"])}
    if drawn_names != table_names:
        problems.append("Entities differ between Figure 1 %s and table 1.1 %s"
                        % (sorted(drawn_names), sorted(table_names)))

    # 2. Every relationship in table 1.2 is labelled on the ER diagram
    for relationship in er_model["relationships"]:
        if relationship["name"] not in joined_erd_text:
            problems.append("Relationship %s is in table 1.2 but not drawn in Figure 1"
                            % relationship["name"])
        for end in relationship["ends"]:
            if end["entity"] not in drawn_names:
                problems.append("Relationship %s uses unknown entity %s"
                                % (relationship["name"], end["entity"]))

    # 3. Every FK names the ER construct it implements, and that construct exists
    known_constructs = {r["name"] for r in er_model["relationships"]} | {"Specialization"}
    for relation in relations:
        for foreign_key in relation["foreign_keys"]:
            if foreign_key["implements"] not in known_constructs:
                problems.append("FK %s.%s implements unknown construct '%s'"
                                % (relation["name"], foreign_key["columns"], foreign_key["implements"]))

    # 4. The FK diagram has one arrow per foreign key
    fk_count = sum(len(r["foreign_keys"]) for r in relations)
    arrow_count = svgs["schema_foreign_keys.svg"].count('marker-end="url(#ah)"')
    if arrow_count != fk_count:
        problems.append("Figure 2 has %d arrows but the schema has %d foreign keys"
                        % (arrow_count, fk_count))

    # 5. Each FD diagram shows one labelled line per FD
    for relation in relations:
        drawn_fds = len(re.findall(r">FD\d+<", svgs[relation["diagram"]]))
        if drawn_fds != len(relation["functional_dependencies"]):
            problems.append("%s shows %d FDs, RELS has %d" % (
                relation["diagram"], drawn_fds, len(relation["functional_dependencies"])))

    # 6. Diagrams on disk match what build_report.py draws now (stale check)
    for file_name, svg_text in svgs.items():
        disk_path = os.path.join(report.DIAG, file_name)
        if not os.path.exists(disk_path):
            warnings.append("%s not on disk yet (run build_report.py to draw it)" % file_name)
            continue
        with open(disk_path, encoding="utf-8") as disk_file:
            if disk_file.read() != svg_text:
                warnings.append("%s on disk is out of date: rerun build_report.py" % file_name)
    return problems, warnings


# ------------------------------------------------------------------------------
# Writing the readable Markdown
# ------------------------------------------------------------------------------
def paren(columns):
    """(A, B) for a composite list, A for a single column."""
    return "(%s)" % ", ".join(columns) if len(columns) > 1 else columns[0]


def mermaid_er(er_model):
    """Mermaid erDiagram of the relationships (solid line = identifying)."""
    lines = ["```mermaid", "erDiagram"]
    for relationship in er_model["relationships"]:
        first, second = relationship["ends"]
        left_marker = MERMAID_MARKERS[first["multiplicity"]][0]
        right_marker = MERMAID_MARKERS[second["multiplicity"]][1]
        line_style = "--" if relationship["identifying"] else ".."
        lines.append('    %s %s%s%s %s : "%s"' % (first["entity"], left_marker, line_style,
                                                  right_marker, second["entity"], relationship["name"]))
    for specialization in er_model["specializations"]:
        lines.append('    %s ||--o| %s : "specialization (subclass, Optional)"'
                     % (specialization["superclass"], specialization["subclass"]))
    lines.append("```")
    return lines


def write_markdown(model, path):
    er_model = model["er_model"]
    out = ["# Assignment 2 diagrams as text",
           "",
           "_Generated by `python export_schema.py` from `build_report.py`. Do not edit by hand._",
           ""]
    if model["consistency_problems"]:
        out += ["> **Consistency problems:** " + "; ".join(model["consistency_problems"]), ""]

    # Figure 1
    out += ["## Figure 1: ER diagram (`erd_engineering_part_sourcer.svg`)", "",
            "**Notation:** " + " | ".join(er_model["notation_legend"]), "",
            "**Reading multiplicities:** " + er_model["multiplicity_rule"], "",
            "### Entities", ""]
    for entity in er_model["entities"]:
        shown = []
        for attribute in entity["attributes"]:
            label = ("/" if attribute["derived"] else "") + attribute["name"]
            if attribute["keys"]:
                label += " {%s}" % ", ".join(attribute["keys"])
            if attribute.get("components"):
                label += " = (%s)" % ", ".join(attribute["components"])
            shown.append(label)
        out.append("- **%s** (%s; identifier: %s): %s"
                   % (entity["name"], entity["kind"], entity["identifier"], "; ".join(shown)))
    out += ["", "### Relationships", ""]
    for relationship in er_model["relationships"]:
        first, second = relationship["ends"]
        sentence = ("each %s has %s %s; each %s has %s %s"
                    % (second["entity"], MULTIPLICITY_WORDS[first["multiplicity"]], first["entity"],
                       first["entity"], MULTIPLICITY_WORDS[second["multiplicity"]], second["entity"]))
        extras = []
        if relationship["identifying"]:
            extras.append("identifying / composition")
        if relationship["attributes"]:
            extras.append("attributes: " + ", ".join(relationship["attributes"]))
        out.append("- **%s %s %s** [%s to %s]: %s.%s"
                   % (first["entity"], relationship["name"], second["entity"],
                      first["multiplicity"], second["multiplicity"], sentence,
                      (" (" + "; ".join(extras) + ")") if extras else ""))
    for specialization in er_model["specializations"]:
        out.append("- **%s is a subclass of %s**: %s. %s." % (
            specialization["subclass"], specialization["superclass"],
            specialization["constraint"], specialization["subclass_adds"]))
    out += [""] + mermaid_er(er_model) + [""]

    # Figure 2
    out += ["## Figure 2: Referential integrity (`schema_foreign_keys.svg`)", "",
            "Each arrow goes from a foreign key to the relation whose primary key it references. "
            "All FK columns are NOT NULL and use ON UPDATE CASCADE.", "",
            "| Relation | Foreign key | References | ON DELETE | Implements |",
            "|---|---|---|---|---|"]
    for relation in model["relations"]:
        for foreign_key in relation["foreign_keys"]:
            out.append("| %s | %s | %s(%s) | %s | %s |" % (
                relation["name"], ", ".join(foreign_key["columns"]), foreign_key["references"],
                ", ".join(foreign_key["referenced_columns"]), foreign_key["on_delete"],
                foreign_key["implements"]))
    out.append("")

    # FD diagrams
    out += ["## FD diagrams (`fd_<Relation>.svg`, section 3.3.1)", "",
            "In each diagram the shaded, underlined cells are the primary key; a dot marks a "
            "determinant attribute and an arrow points to each dependent.", ""]
    for relation in model["relations"]:
        out.append("### %s" % relation["name"])
        out.append("- Attributes: %s" % ", ".join(relation["attributes"]))
        out.append("- Candidate keys: %s" % "; ".join("{%s}" % ", ".join(k) for k in relation["candidate_keys"]))
        if relation["functional_dependencies"]:
            for fd in relation["functional_dependencies"]:
                out.append("- %s: %s -> %s  (determinant is %s)" % (
                    fd["label"], paren(fd["determinant"]), ", ".join(fd["dependents"]), fd["determinant_is"]))
        else:
            out.append("- No non-trivial FDs (all-key relation).")
        for derived in relation["derived_not_stored"]:
            out.append("- Derived, not stored: /%s = %s" % (derived["name"], derived["rule"]))
        out.append("- BCNF: %s" % ("yes" if relation["normal_forms"]["BCNF"] else "NO"))
        out.append("")

    # Figure 3
    for rejected in model["rejected_designs"]:
        out += ["## Figure 3: %s (`%s`)" % (rejected["name"], rejected["diagram"]), "",
                "- Attributes: %s" % ", ".join(rejected["attributes"]),
                "- Primary key: %s" % paren(rejected["primary_key"])]
        for fd in rejected["functional_dependencies"]:
            out.append("- %s: %s -> %s" % (fd["label"], paren(fd["determinant"]), ", ".join(fd["dependents"])))
        out += ["- Verdict: " + rejected["verdict"], ""]

    # Constraints
    out += ["## Constraints the diagrams cannot show", ""]
    for constraint in model["constraints"]:
        out.append("- **%s**: %s" % (constraint["id"], constraint["text"]))
    out += ["", "How C3, C5 and C7 are maintained (triggers):", ""]
    for rule in model["constraint_maintenance"]:
        out.append("- **%s** on %s: %s" % (rule["rule"], rule["operation"], rule["action"]))
    out.append("")

    with open(path, "w", encoding="utf-8") as markdown_file:
        markdown_file.write("\n".join(out))


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    report_html = build_report_html()
    collector = TableCollector()
    collector.feed(report_html)
    html_tables = collector.tables

    svgs = fresh_svgs()
    er_model, erd_labels = build_er_model(svgs["erd_engineering_part_sourcer.svg"], html_tables)
    relations = build_relations(html_tables)
    problems, warnings = check_consistency(er_model, erd_labels, relations, svgs, html_tables)

    model = {
        "generated_from": "build_report.py (RELS, build_erd(), report HTML)",
        "consistency_problems": problems,
        "diagrams": build_diagram_index(report_html),
        "er_model": er_model,
        "relations": relations,
        "rejected_designs": build_rejected_designs(),
        "constraints": [{"id": row[0], "text": row[1]}
                        for row in table_with_header(html_tables, ["#", "Constraint"])],
        "constraint_maintenance": [{"rule": row[0], "operation": row[1], "action": row[2]}
                                   for row in table_with_header(html_tables, ["Rule", "Operation", "Action"])],
        "not_defined_in_assignment_2": ["SQL data types", "indexes", "trigger code"],
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "schema.json"), "w", encoding="utf-8") as json_file:
        json.dump(model, json_file, indent=2, ensure_ascii=False)
    write_markdown(model, os.path.join(OUTPUT_DIR, "DIAGRAMS.md"))

    print("wrote", os.path.join(OUTPUT_DIR, "schema.json"))
    print("wrote", os.path.join(OUTPUT_DIR, "DIAGRAMS.md"))
    for warning in warnings:
        print("warning:", warning)
    for problem in problems:
        print("PROBLEM:", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
