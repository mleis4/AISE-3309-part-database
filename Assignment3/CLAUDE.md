# Assignment 3: how the agents work together

The agents for this assignment are in `.claude/agents/`. The rubric is `A3_mock_rubric.md`, and the handout is `AISE 3309 - Assignment 03.md`.

## Who owns what

| Rubric criterion | Owner agent |
|---|---|
| Schema Implementation (Task 1) | ddl-builder |
| Data Insertion and Loading (Tasks 2 and 3) | insert-writer (Task 2), data-generator (Task 3) |
| SELECT Queries (Task 4), Data Modification Commands (Task 5), Views and Updatability (Task 6) | query-author |
| Report and Code Archive | submission-packager |
| AI Use and Understanding | query-author (explanation.md), and every agent for its own entries in ai_log.md |

## The grading loop

Subagents cannot start other subagents, so the main session runs this loop:

1. **Build.** Run the owner agent for a piece of work. Before it replies, it grades itself against its own rubric rows (the "Self-grade" section in each agent file) and fixes what it can.
2. **Grade.** Run `rubric-grader` on the criteria that changed, or on all of them before submitting. Pass it the previous grade report, if there is one.
3. **Hand back.** For each `HANDBACK → <agent>` block in the grade, start that agent with the block pasted in unchanged, under the heading "Grader feedback". Agents whose work does not depend on each other can run in parallel. Run ddl-builder before the agents that read `task3.sql`.
4. **Repeat** from step 2 until the verdict is `AGENT-COMPLETE` or `PERFECT`, for **at most 3 rounds**. Stop early if a round raises no criterion, or if a criterion went down. Then show the user the latest grade, and the problem the agents keep missing.
5. **Finish.** Show the user the score table and the human to-do list: screenshots, DESCRIBE output, the Workbench dump, the data-type decisions and the TA question about file numbering. Do not try to work around those items. Only a person can do them.

Run `sql-reviewer` once before the first grading round. It catches ISO-SQL and composite-key problems more cheaply than a full grade.

## Database

- Server: MySQL Community Server 26.10.0 on `127.0.0.1`, port **3306**, running as the Windows service `MySQL2610`. sql_mode includes ONLY_FULL_GROUP_BY and STRICT_TRANS_TABLES.
- Client: `"/c/Program Files/MySQL/MySQL Server 26.10/bin/mysql.exe"` (it is not on PATH).
- Log in only as the `ep_agent` user, through its option file outside the repo:
  `"<mysql.exe>" --defaults-extra-file="C:/Users/leism/.ep_sourcer_agent.cnf" ep_sourcer_test < file.sql`
  Never write a password into any file in this project, because the project files get zipped and submitted.
- Only the scratch databases `ep_sourcer_test` (building and testing) and `ep_sourcer_grade` (rubric-grader) may be used. Never touch `sakila`, `mysql`, `sys` or any other database.
- If the option file does not exist, the database is not set up for agents yet. Mark the work "untested" and say so. Do not fall back to root.
- Run SQL files through stdin (`< file.sql`).
- **No triggers.** The group decided not to use them (the handout makes them optional). C3, C4, C5 and C7 are documented in task3.sql, upheld by the data generator and the application, and verified by `SRC/check_data.sql`.

### Verified on this server (2026-11-25)

| Behaviour | Result |
|---|---|
| CHECK constraints | Enforced (error 3819) |
| CHECK on a column with an FK referential action | Rejected with error 3823, so C4 is documented as a commented ISO CHECK |
| INTERSECT, EXCEPT, row-value comparison `(a,b) < (c,d)` | Supported |
| `FETCH FIRST n ROWS ONLY` | Not supported (error 1064) |
| Double-quoted identifiers | **Not identifiers.** Without ANSI_QUOTES, `"Name"` is the string `'Name'`, so a query using it runs but returns wrong results. Leave every identifier **unquoted**: no double quotes and no backticks. |
| CREATE TRIGGER as ep_agent | Fails with error 1419 (binary logging). This doesn't matter, because the project uses no triggers. |

## Shared rules

- Stay within the course material. `COURSE_SCOPE.md`, built from `../AISE 3309 Course Outline.md` and Connolly & Begg, lists what is allowed and what is not. Every agent reads it, and the grader enforces it.
- Use ISO SQL. Mark unavoidable MySQL syntax with `-- MySQL-specific:`.
- Never run `../Assignment2/build_report.py` (it overwrites the A2 PDF and .docx). Importing it is fine.
- Use the file names from the handout exactly: task3.sql holds Task 1, task4.sql Task 2, task6.sql Task 4, task7.sql Task 5 and task8.sql Task 6.
- Every agent that changes a file adds an entry to `ai_log.md` (see the Self-grade section in each agent file).
