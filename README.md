# Engineering Part Sourcer

**AISE 3309 — Database Management Systems** · Western University, Fall 2026 · Group 6

## What this repo is

This is our semester-long database project for AISE 3309. Over the term we design, build and use a complete database system on a topic we chose (and our TA approved). The work runs in four phases, one per assignment, and each phase builds on the one before:

| Phase | Assignment | What we deliver |
|---|---|---|
| 1. Requirements | Assignment 1 | Requirements specification: project overview, functional specs, entity and relationship types |
| 2. Design | Assignment 2 | Conceptual EER diagram (UML notation), relational schema, normalization (3NF / BCNF) and schema evaluation |
| 3. Implementation & data | Assignment 3 | SQL implementation of the schema, loaded with data |
| 4. Application | Assignment 4 | A simple web application, built with AI assistance, that interacts with the database |

## The project: Engineering Part Sourcer

Engineering Part Sourcer is a web application that helps engineers find and compare electronic and mechanical parts across multiple distributors. Instead of checking each supplier's site by hand, users can:

- **Search** for parts by name, manufacturer part number or keyword
- **Filter** by category, dimensions, distributor, price range and minimum stock
- **Compare prices**: see each distributor's unit price, stock, estimated shipping time and subtotal for a given quantity
- **Build or upload BOMs** (bills of materials), either by hand or from a CSV, with unmatched parts and stock shortfalls flagged
- **Keep a cart** of supplier listings, with subtotals grouped by distributor and links out to buy
- **Sign in** to save BOMs and carts between visits
- **Share projects** with other users: a title, description and the list of parts used, so others can replicate the build
- **AI-assisted search** that turns plain-language component requirements into catalogue filters

### Data model (from Assignment 2)

The main relations in the schema are:

`Customer`, `Part`, `PartAlternative`, `Distributor`, `Listing`, `BOM`, `BOMLine`, `BOMSelection`, `ShoppingCart`, `CartLine`, `Review`, `SharedProject`

The ER diagram, foreign-key schema diagram and one functional-dependency diagram per relation are in [`Assignment2/diagrams/`](Assignment2/diagrams/).

## Repo layout

```
.
├── AISE3309-Assignment01_Template.md   # Assignment 1: requirements specification
├── Assignment2/                        # Assignment 2: conceptual + relational design
│   ├── AISE3309-Assignment02_Group6.pdf   # Final submitted report
│   ├── build_report.py                    # Script that builds the report (.docx/.pdf/.html)
│   ├── diagrams/                          # ERD, FK schema and FD diagrams (SVG + PNG)
│   ├── AGENTS.md                          # Context and requirements for AI assistants
│   ├── Rubric.pdf                         # Marking rubric
│   └── old_draft/                         # Earlier drafts, kept for reference
└── Assignment3/                        # Assignment 3: SQL implementation (mock data, screenshots pending)
    ├── SQL/  SRC/  DUMP/                  # The archive contents (python package.py builds the .zip)
    ├── capture_responses.py               # Rebuilds the test DB and records every statement's response
    ├── build_report.py                    # Builds the A3 report (.html/.pdf)
    ├── explanation.md                     # Required explanation of Tasks 4-6
    └── ai_log.md                          # What the AI did and how it was checked
```

## Team

| Member | Student ID |
|---|---|
| Mats Leis (group leader) | 251409940 |
| Shaan Wrench | 251422184 |
| Ayman Hossain | 251430600 |
| Samuel Huang | 251418742 |
| Anish Jami | 251419182 |
