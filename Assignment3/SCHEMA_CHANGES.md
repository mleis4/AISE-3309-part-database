# Schema changes after the Assignment 2 peer review

Assignment 3 begins with "a final, critical evaluation of your relational schema". This file records what changed since the submitted A2 report and why, so it can go in the A3 report. Every change is in `RELS` in `../Assignment2/build_report.py`, and `schema.json` has been regenerated.

| # | Peer feedback | Change | Effect on the schema |
|---|---|---|---|
| 1 | "Part key: generic part numbers like 1N4148 are made by several manufacturers, so use (Manufacturer, Manufacturer_PartNum)." | No change needed. The key was already (ManufacturerName, Manufacturer_PartNum) in RELS, and table 1.4 records the change from Assignment 1. | None |
| 2 | "C2 (one listing per distributor per part) is a shortcut: a distributor that sells a part as both cut tape and reel can't store both." | Added the attribute **Listing.Packaging**. C2 is now "at most one listing per distributor, part and packaging", and the AK of Listing is (DistributorName, ManufacturerName, Manufacturer_PartNum, Packaging). | Listing has a new column, and its AK and FD2 change. It is still in BCNF, since both determinants are candidate keys. C3 is unchanged: a BOM still selects at most one listing per part, and the C3 trigger now has real alternatives to choose between. |
| 3 | "SharedProject.Title unique across all customers means two users can't share projects with the same name." | The AK changed from Title to **(CustomerEmail, Title)**. | Titles are unique per customer only. FD2 of SharedProject changes, and it is still in BCNF. |
| 4 | "BCNF section is dense; add a short summary at the start." | Added a summary paragraph at the start of 3.3.3: everything is in BCNF, and why BOMLine and BOMSelection are kept separate. | Report text only |

## Implementation decision: no triggers

Section 2.4 of the A2 report says triggers will maintain C3, C5 and C7. In A3 the group uses **no triggers**, because the handout only asks us to "consider" them. The A3 report should say so and explain how each constraint is handled instead:

| Constraint | Why the DBMS cannot enforce it | How it is upheld |
|---|---|---|
| C3 (a selection must be for a part the BOM contains, at most one per part) | It spans BOMSelection, Listing and BOMLine, so the ISO form is CREATE ASSERTION, which MySQL does not support | Data generator and A4 application; `check_data.sql` query |
| C4 (Part1 < Part2, no self-pair) | The ISO CHECK is rejected by MySQL error 3823 because the columns have FK referential actions | Data generator and application; `check_data.sql` query |
| C5 (a shared BOM has at least one line) | Needs CREATE ASSERTION | Data generator and application; `check_data.sql` query |
| C7 (a listing's part never changes) | A rule about updates, which no assertion can express | The application never updates those columns |

## Still to do

- The A2 PDF and .docx were **not** rebuilt, so they still show the submitted version. The SVG diagrams in `Assignment2/diagrams/` and `schema.json` show the new schema. Running `build_report.py` overwrites the submitted PDF and .docx, so copy those two files elsewhere first if you rebuild.
- `Assignment2/diagrams/png/` (used only for the .docx) still holds the old ER and FD images until `build_report.py` is run.
- Group decision: does the Packaging attribute stay? The simpler alternative is to drop C2 and the AK entirely, so that listings of the same part are told apart only by their Distributor_PartNum. That keeps the ER diagram unchanged, but loses a meaningful constraint.
