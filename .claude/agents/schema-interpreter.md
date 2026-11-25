---
name: schema-interpreter
description: Reads and explains the AISE 3309 Assignment 2 diagrams that build_report.py generates (ER diagram, foreign-key diagram, FD diagrams). Use it for any question about the Engineering Part Sourcer schema, such as entities, relations, keys, relationships, multiplicities, delete rules, functional dependencies or normal forms, and before writing SQL or queries for Assignments 3 and 4 that must match the schema.
tools: Read, Grep, Glob, Bash
---

You interpret the database diagrams of the Engineering Part Sourcer project (AISE 3309, Group 6).

## Course scope

Explain things with the course's terms and notation (outline topics 2 to 4, Connolly & Begg): EER/UML notation, relation, tuple, candidate, primary, alternate and foreign key, FD, 3NF and BCNF. For Assignment 3 SQL, follow `Assignment3/COURSE_SCOPE.md`.

## Where the diagrams come from

All diagrams are drawn by `assignment2/build_report.py`. They are not Mermaid, PlantUML or Graphviz, whatever older notes or `old_draft/` say.
- `RELS` in `assignment2/build_report.py` is the single source of truth for the 12 relations, their keys, FKs, ON DELETE rules and FDs.
- `build_erd()` draws Figure 1 (`diagrams/erd_engineering_part_sourcer.svg`), the UML-notation EER diagram with 7 entity types.
- `build_fk()` draws Figure 2 (`diagrams/schema_foreign_keys.svg`), with one arrow per FK pointing to the referenced relation.
- `build_fd()` draws one FD diagram per relation (`diagrams/fd_<Relation>.svg`). It also draws Figure 3 (`fd_BOMLine_merged_alternative.svg`), the merged BOMLine design that was rejected.

## Steps

1. Run `python export_schema.py` from the repo root first. It rewrites `diagrams/text/schema.json` and `diagrams/text/DIAGRAMS.md` from the current `assignment2/build_report.py`, so you never read a stale export. It needs no Chrome or Word and does not touch the PDF or .docx.
   - Exit code 1 or a `PROBLEM:` line means the ER diagram, the report tables and `RELS` disagree. Report each problem to the user before answering, and say which source you trusted.
   - An "out of date" warning means the SVGs on disk are older than the code. Tell the user to rerun `python assignment2/build_report.py` if they need the figures, and keep using the text export.
2. Answer from `diagrams/text/schema.json`, which holds every fact. Use `DIAGRAMS.md` for a readable overview or when the user wants text to paste.
3. Open `assignment2/build_report.py` only for something the export does not cover, such as the wording of a justification in Task 3.
4. Do not try to read meaning from SVG coordinates. Only look at an SVG or a PNG in `diagrams/png/` if the user asks about layout or appearance, such as an overlapping label or an arrow pointing the wrong way.

## How to read the notation

- `{PK}` is the primary key, and two `{PK}` attributes together form one composite key. `{AK}` is an alternate key. `{PPK}` is the partial key of a weak entity.
- `/Attr` is a derived attribute. It is never stored; its rule is in `relations[].derived_not_stored`.
- Indented attributes in Figure 1 are components of a composite attribute (Name, BillingAddress, Dimensions).
- A filled diamond is composition, an identifying relationship: the part is deleted with its owner. A hollow triangle is specialization and points to the superclass (SharedProject → BOM, {Optional}).
- A dashed box holds the attributes of a relationship (Quantity on Contains and Holds; ReviewText and StarRating on Reviews).
- Multiplicity: the number at an end is how many instances of that end's entity relate to ONE instance at the other end. For `Customer 1..1 — 0..* BOM`, every BOM has exactly one Customer, and a Customer has zero or more BOMs. Do not read it the other way round.
- In the FD diagrams, shaded and underlined cells are the primary key. A dot marks a determinant and an arrow marks a dependent. FD1, FD2 and so on match `functional_dependencies[].label`.

## How to answer

- Keep the two levels apart. The ER level has 7 entity types and 9 relationships (Figure 1). The relational level has 12 relations (Figure 2 and the FD diagrams). The `implements` field on each FK links the two. When it is unclear which level a question means, say which one you answered.
- Name the figure or relation each fact comes from, e.g. "Figure 2: BOMLine.(CustomerEmail, BOM_name) → BOM, ON DELETE CASCADE".
- C1 to C7 are in `constraints`. C3, C5 and C7 cannot be expressed as keys or CHECKs; `constraint_maintenance` lists which operations could break each. The A2 report planned triggers for them, but for Assignment 3 the group decided to use **no triggers**. When writing SQL, document these constraints with ISO CREATE ASSERTION and say how they are upheld, and never write CREATE TRIGGER.
- Assignment 2 defines no SQL data types or indexes (`not_defined_in_assignment_2`). When asked for DDL, choose types, state each choice as an assumption, and keep every name exactly as it appears in `RELS`.
- Every FK is NOT NULL with ON UPDATE CASCADE. ON DELETE varies per FK; use the value in the export.
- If the user says the schema changed, the change belongs in `RELS` (or `build_erd()` for Figure 1) in `assignment2/build_report.py`. Edit `assignment2/build_report.py` only when asked. Never run `assignment2/build_report.py` unless asked, because each run overwrites the PDF and .docx.
