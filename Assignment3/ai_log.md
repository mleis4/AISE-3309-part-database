# AI log: Assignment 3

Every AI-assisted change to the Assignment 3 files, with how it was checked. This log is the evidence for the "AI Use and Understanding" criterion and feeds the A4 reflection.

## 2026-11-25: Claude (Claude Code, main session), first complete draft with mock data

The work was done in one session, following the agent specs in `.claude/agents/` (ddl-builder, insert-writer, data-generator, query-author, submission-packager) and `COURSE_SCOPE.md`, without starting separate subagents.

**Files written:** `SRC/build_ddl.py` → `SQL/task3.sql`; `SQL/task4.sql`; `SRC/generate_data.py` → `SRC/load_data.sql`, `SRC/samples.md`; `SRC/check_data.sql`; `SQL/task6.sql`, `SQL/task7.sql`, `SQL/task8.sql`; `explanation.md`; `capture_responses.py` → `responses/*.json`, `DUMP/ep_sourcer_dump.sql`; `build_report.py` → `AISE3309-Assignment03_Group6.{html,pdf}`, `screenshots/README.md`; `package.py` → `AISE3309-Assignment03_Group6.zip`.

**How the output was checked**
- `export_schema.py` was rerun first (exit 0, no problems). `task3.sql` is generated from `RELS`, so names, keys and FKs match `schema.json` by construction. `build_ddl.py` and `generate_data.py` were each run twice and gave byte-identical output (md5).
- Every file was run on MySQL 26.10 as `ep_agent` in `ep_sourcer_test`, in the documented order: task3 → task4 → load_data → check_data → task6 → task7 → task8. All 21 checks in `check_data.sql` return 0 (orphaned FKs, C2, C3 (two checks), C4, C5, shared-project AK).
- The dump was restored into `ep_sourcer_grade` and gave the same counts (Listing 7,259; BOMTotals 802 rows).
- Each query result was compared with the intent: Q3 shows "Empty Draft" with 0 parts (proves the outer join and COUNT(column)); Q7 returns one alternative from each UNION branch; the six failing statements in task7/task8 fail with exactly the predicted errors (3819, 1451, 1471, 1288, 1369 ×2).
- A grep for out-of-scope syntax (backticks, double quotes, LIMIT, IFNULL, IF(), GROUP_CONCAT, NOW(), ENUM, AUTO_INCREMENT, UNSIGNED, window functions, triggers) finds nothing outside comments.
- Numbers quoted in `explanation.md` and the report were read back from the captured responses and from the database.

**What the AI got wrong, and how it was corrected**
1. The first `load_data.sql` failed with `ERROR 1292: Incorrect datetime value '2026-03-08 02:49:00'`: random TIMESTAMPs fell in the hour skipped by the daylight-saving change. Fixed by generating times between 06:00 and 21:59 only.
2. Shared-project titles were built by cutting off the last word of the BOM name, which turned "3D Printer Mainboard Rev B" into "Open 3D Printer Mainboard Rev". Fixed by removing the known suffix list (v1, Rev A, ...) instead.
3. M2 at first wrote `UnitPrice * 1.10` directly into DECIMAL(10,2), and MySQL raised 118 "data truncated" warnings. Fixed with an explicit `CAST(... AS DECIMAL(10,2))`.
4. The first dump attempt failed (`FLUSH TABLES` needs the RELOAD privilege, which ep_agent does not have). Fixed with `--skip-lock-tables` instead of `--single-transaction`. mysqldump still prints a harmless warning about masking policies, but the dump is complete and restores correctly.
5. The first explanation draft quoted the M2 "before" average as 0.4803. The captured response says 0.479380, so it was corrected (the extra 0.2% rise comes from rounding to cents).

**Decisions the AI made that the group must confirm**
- All data types (`TYPES` in `build_ddl.py`), the nullable columns, the Packaging CHECK list and the two indexes.
- task4.sql runs on the empty schema before the bulk load, so its SELECT * results are short.
- task7.sql and task8.sql end with ROLLBACK so they can be rerun and the database stays equal to the dump.
- `explanation.md` and `ai_log.md` are not in the zip by default (the handout's list does not include them); `python package.py --with-explanation` adds them.

**Not done (only a person can do it):** Workbench screenshots (79 names in `screenshots/README.md`), a Workbench Data Export to replace the mysqldump stand-in, team contributions in the report, and rewriting the AI-drafted text in the group's own words.
