# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:            Mats Leis
# Student Number:  251409940
# Date:            November 25, 2026
# Program:         capture_responses.py
# Description:     Rebuilds the scratch database ep_sourcer_test from the
#                  archive files in the documented run order and records the
#                  server's response to every statement:
#                    task3.sql -> task4.sql -> load_data.sql -> check_data.sql
#                    -> task6.sql -> task7.sql -> task8.sql, then DESCRIBE.
#                  The responses go to responses/<file>.json, which
#                  build_report.py shows next to each statement until the
#                  group's Workbench screenshots replace them. It also writes
#                  a stand-in dump to DUMP/ with mysqldump.
#
# Run:             python capture_responses.py     (from Assignment3/)
#                  Logs in as ep_agent through the option file outside the
#                  repo; no password is stored in this project.
# ------------------------------------------------------------------------------
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = r"C:\Program Files\MySQL\MySQL Server 26.10\bin"
MYSQL = os.path.join(BIN, "mysql.exe")
MYSQLDUMP = os.path.join(BIN, "mysqldump.exe")
OPTION_FILE = r"C:\Users\leism\.ep_sourcer_agent.cnf"
DATABASE = "ep_sourcer_test"
OUT_DIR = os.path.join(HERE, "responses")
DUMP_PATH = os.path.join(HERE, "DUMP", "ep_sourcer_dump.sql")
SEPARATOR = "--------------\n"

TABLES = ["Customer", "Part", "Distributor", "Listing", "ShoppingCart", "BOM", "SharedProject",
          "PartAlternative", "BOMLine", "BOMSelection", "CartLine", "Review"]

RUN_ORDER = [  # (file, capture responses?)
    ("SQL/task3.sql", True),
    ("SQL/task4.sql", True),
    ("SRC/load_data.sql", False),
    ("SRC/check_data.sql", True),
    ("SQL/task6.sql", True),
    ("SQL/task7.sql", True),
    ("SQL/task8.sql", True),
]


def split_statements(sql_text):
    """Splits a file into statements, each with the comment lines above it.

    Returns a list of (comments, statement). A statement ends at a non-comment
    line ending in ';'. None of the project files has ';' inside a string.
    """
    chunks, comments, body = [], [], []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not body and (stripped.startswith("--") or not stripped):
            comments.append(line)
            continue
        if stripped.startswith("--"):
            continue                        # comment inside a statement
        body.append(line)
        if stripped.endswith(";"):
            chunks.append(("\n".join(comments).strip("\n"), "\n".join(body)))
            comments, body = [], []
    return chunks


def run_mysql(sql_text, verbose=True):
    args = [MYSQL, "--defaults-extra-file=" + OPTION_FILE, "--table", "--force", DATABASE]
    if verbose:
        args.insert(2, "-vvv")
    result = subprocess.run(args, input=sql_text.encode("utf-8"), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


def parse_verbose(output):
    """-vvv output: SEPARATOR stmt SEPARATOR result ... -> list of results."""
    parts = output.split(SEPARATOR)
    results = []
    for i in range(2, len(parts), 2):
        text = parts[i].strip("\n")
        if text.endswith("Bye"):
            text = text[:-3].rstrip("\n")
        results.append(text)
    return results


def capture(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as f:
        chunks = split_statements(f.read())
    output = run_mysql("\n".join(stmt for _, stmt in chunks) + "\n")
    results = parse_verbose(output)
    if len(results) != len(chunks):
        raise SystemExit("PROBLEM: %s has %d statements but %d responses\n%s"
                         % (path, len(chunks), len(results), output[-2000:]))
    return [{"comments": c, "sql": s, "response": r} for (c, s), r in zip(chunks, results)]


def main():
    if not os.path.exists(OPTION_FILE):
        print("Option file missing: database not set up for agents. Nothing captured.")
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    errors = []
    for path, keep in RUN_ORDER:
        if keep:
            records = capture(path)
            name = os.path.splitext(os.path.basename(path))[0]
            with open(os.path.join(OUT_DIR, name + ".json"), "w", encoding="utf-8") as f:
                json.dump(records, f, indent=1)
            failed = [r for r in records if r["response"].startswith("ERROR")]
            errors += ["%s: %s" % (path, r["response"].splitlines()[0]) for r in failed]
            print("captured %-20s %3d statements, %d errors" % (path, len(records), len(failed)))
        else:
            out = run_mysql(open(os.path.join(HERE, path), encoding="utf-8").read(), verbose=False)
            if "ERROR" in out:
                raise SystemExit("PROBLEM loading %s:\n%s" % (path, out))
            print("loaded   %s" % path)

    describe = [{"comments": "", "sql": "DESCRIBE %s;" % t,
                 "response": r} for t, r in zip(TABLES, parse_verbose(
                     run_mysql("\n".join("DESCRIBE %s;" % t for t in TABLES) + "\n")))]
    with open(os.path.join(OUT_DIR, "describe.json"), "w", encoding="utf-8") as f:
        json.dump(describe, f, indent=1)
    print("captured DESCRIBE for %d tables" % len(describe))

    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)
    with open(DUMP_PATH, "wb") as f:
        subprocess.run([MYSQLDUMP, "--defaults-extra-file=" + OPTION_FILE, "--skip-lock-tables", "--set-gtid-purged=OFF",
                        "--no-tablespaces", "--skip-dump-date", DATABASE], stdout=f, check=True)
    print("wrote", DUMP_PATH)
    print("expected errors (statements that fail on purpose):")
    for e in errors:
        print("  ", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
