# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         package.py
# Description:     Builds AISE3309-Assignment03_Group6.zip with exactly the
#                  layout the handout (section 5) requires:
#                    SQL/task3.sql task4.sql task6.sql task7.sql task8.sql
#                    SRC/  generator source and generated load script
#                    DUMP/ the database dump (.sql)
#                  Checks that every required file exists and is not empty
#                  first, and writes nothing if anything is missing.
#
# Run:             python package.py                     (from Assignment3/)
#                  python package.py --with-explanation  (also adds explanation.md
#                                                         and ai_log.md at the root)
# ------------------------------------------------------------------------------
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(HERE, "AISE3309-Assignment03_Group6.zip")

REQUIRED = [
    "SQL/task3.sql",   # Task 1: CREATE TABLE
    "SQL/task4.sql",   # Task 2: INSERT
    "SQL/task6.sql",   # Task 4: SELECT
    "SQL/task7.sql",   # Task 5: data modification
    "SQL/task8.sql",   # Task 6: CREATE VIEW
    "SRC/build_ddl.py",
    "SRC/generate_data.py",
    "SRC/load_data.sql",
    "SRC/check_data.sql",
    "SRC/samples.md",
]
OPTIONAL_ROOT = ["explanation.md", "ai_log.md"]


def main():
    problems = []
    for rel in REQUIRED:
        path = os.path.join(HERE, rel)
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            problems.append("missing or empty: " + rel)
    dumps = [f for f in os.listdir(os.path.join(HERE, "DUMP"))
             if f.endswith(".sql") and os.path.getsize(os.path.join(HERE, "DUMP", f)) > 0] \
        if os.path.isdir(os.path.join(HERE, "DUMP")) else []
    if not dumps:
        problems.append("DUMP/ has no .sql dump (Workbench: Server > Data Export)")
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        print("No zip written.")
        return 1

    entries = REQUIRED + ["DUMP/" + f for f in sorted(dumps)]
    if "--with-explanation" in sys.argv:
        entries += [f for f in OPTIONAL_ROOT if os.path.isfile(os.path.join(HERE, f))]

    tmp = ZIP_PATH + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in entries:
            z.write(os.path.join(HERE, rel), rel)
    os.replace(tmp, ZIP_PATH)

    print("wrote", ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH) as z:
        for info in z.infolist():
            print("  %-28s %10d bytes" % (info.filename, info.file_size))
    print("Note: the handout's file numbers differ from the task numbers (task3.sql holds Task 1).")
    print("      They are followed exactly; confirm with the TA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
