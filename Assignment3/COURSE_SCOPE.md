# Course scope for Assignment 3 agents

Every agent reads this before writing SQL, code or report text. Source: `../AISE 3309 Course Outline.md` (Fall 2026, topics 1 to 9). The required text is Connolly & Begg, *Database Systems*, 6th edition (C&B). When a choice is unclear, use the form taught in lectures and C&B. The handout adds: "All SQL statements must be according to ISO standards as covered during lectures."

## In scope (use these)

| Outline topic | What it allows in A3 |
|---|---|
| 3.1 Relations from a conceptual model | Table and column names exactly as in the A2 schema; relational terms (relation, tuple, attribute, PK, FK, AK) |
| 4.1–4.2 Normalization | Justifying the schema with FDs, 3NF and BCNF; no denormalized extra columns |
| 5.1 Relational algebra | Writing each Task 4 query in relational algebra in `explanation.md` (σ, π, ⋈, ⟕, ∪, ∩, −, ρ, γ for grouping) |
| 6.1 Schema and tables | CREATE TABLE, DROP TABLE, data types (CHARACTER/VARCHAR, INTEGER/SMALLINT, DECIMAL/NUMERIC, DATE/TIMESTAMP) |
| 6.2 Integrity constraints | NOT NULL, PRIMARY KEY, UNIQUE, FOREIGN KEY with ON DELETE / ON UPDATE (CASCADE, SET NULL, SET DEFAULT, NO ACTION, RESTRICT), CHECK, named CONSTRAINTs. CREATE DOMAIN and CREATE ASSERTION are ISO features from C&B that MySQL lacks. Mention them in comments as the standard way, next to the MySQL substitute. |
| 7.1 Queries, indexes, views | SELECT-FROM-WHERE, DISTINCT, column aliases, ORDER BY, LIKE, BETWEEN, IN, IS NULL; inner, natural, LEFT/RIGHT/FULL outer joins; COUNT/SUM/AVG/MIN/MAX, GROUP BY, HAVING; subqueries (scalar, row, table, correlated), IN, EXISTS / NOT EXISTS, ANY / ALL; UNION, INTERSECT, EXCEPT; CREATE INDEX / DROP INDEX; CREATE VIEW, WITH CHECK OPTION, view updatability under the ISO rules |
| 7.2 Insert, update, delete | INSERT … VALUES (single and multi-row, with or without a column list), INSERT … SELECT, UPDATE with a subquery, DELETE with a subquery |
| 8.1 ISO transaction model | START TRANSACTION, COMMIT, ROLLBACK (for example, wrapping the data load) |
| 8.2 Triggers | In the course, but **not used in this project** (a group decision; the handout makes them optional). Constraints that need them are documented with CREATE ASSERTION or CHECK instead. |

## The ISO view-updatability rules (C&B), to cite in Task 6

A view is updatable only if all of these hold:
1. DISTINCT is not specified.
2. Every element in the SELECT list is a column name (no expressions, constants or aggregates), and no column appears more than once.
3. The FROM clause names exactly one table: no joins, no UNION, INTERSECT or EXCEPT. If that table is itself a view, the view must also be updatable.
4. The WHERE clause has no nested SELECT that refers to the table in FROM.
5. There is no GROUP BY or HAVING.

In addition, an INSERT through a view fails if the view leaves out a NOT NULL column that has no default. WITH CHECK OPTION rejects an INSERT or UPDATE that would produce a row the view's WHERE clause does not select. Wherever MySQL's own behaviour differs from these rules (MySQL allows some updates through join views, for example), explain it with the ISO rule first, then mention the MySQL difference.

## Out of scope (do not use)

These are not in the outline topics, so a TA may see them as unexplained or AI-written work:
- window functions (`OVER`, `RANK()`, `ROW_NUMBER()`, `PARTITION BY`), CTEs and recursive queries (`WITH … AS`), `LATERAL`, JSON functions, full-text search, regular expressions
- stored procedures, functions, cursors, events, `PREPARE`/`EXECUTE`, user variables (`@x`)
- quoted identifiers of any kind. ISO double quotes are read as string literals by this server, so leave identifiers unquoted (none of the schema names is a reserved word)
- MySQL-only shortcuts with a standard form: backticks, `LIMIT`, `IF()`, `IFNULL`, `GROUP_CONCAT`, `ENUM`, `SET`, `AUTO_INCREMENT`, `UNSIGNED`, `INSERT IGNORE`, `REPLACE`, `ON DUPLICATE KEY UPDATE`, `INSERT … SET`, `STR_TO_DATE`, `NOW()` (use `CURRENT_TIMESTAMP` or `CURRENT_DATE`)
- NoSQL (topic 9), application code or ORMs (those belong to Assignment 4), GRANT/REVOKE (not asked for in A3)
- denormalization, surrogate keys, or columns for derived attributes, all of which the A2 design rejected

**Row limits.** Top-N syntax is not part of the course. Write queries whose WHERE, GROUP BY or HAVING already keep the result short. If a result is still long, truncate it in the screenshot, as the handout allows, instead of adding `LIMIT`.

## Unavoidable MySQL syntax (allowed only with a `-- MySQL-specific:` comment)

The comment names the ISO or C&B form being replaced:
- `CREATE INDEX` (not part of ISO SQL, but covered in outline topic 7.1)
- `DROP TABLE IF EXISTS`

## Writing

- The outline allows up to 10% off for poor English. Report text and `explanation.md` must be clear, correct English.
- Students must write their reports in their own words. Agent text is a draft. Mark it for the group to read, understand and rewrite where needed, and record the agent's part in `ai_log.md`.
- Use the course terms (relation, tuple, attribute, candidate/alternate key, referential integrity, updatable view), and cite C&B or lectures, not web sources.
