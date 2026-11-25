#### Electrical and Computer Engineering

## AISE 3309: Database Management Systems

### Assignment 03

##### Database Implementation

##### Released on: Tuesday, 17<sup>th</sup>November 2026

##### Due on: Friday 4th December 2026

**Note:** Due date includes 48 hours grace period.

-- page 1 --

# Table of Contents

<div style="display: flex; justify-content: space-between;"><span>1. Assignment Overview</span><span>2</span></div>
<div style="display: flex; justify-content: space-between;"><span>2. Objectives</span><span>2</span></div>
<div style="display: flex; justify-content: space-between;"><span>3. Assignment Details</span><span>2</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 20px;"><span>MySQL Installation and Setup</span><span>2</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 1: SQL Database Schema Creation</span><span>3</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 2: Basic Data Insertion</span><span>3</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 3: Substantial Data Loading</span><span>3</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 4: SQL Queries (SELECT)</span><span>3</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 5: Data Modification Commands</span><span>3</span></div>
<div style="display: flex; justify-content: space-between; padding-left: 40px;"><span>Task 6: View Creation and Evaluation</span><span>3</span></div>
<div style="display: flex; justify-content: space-between;"><span>4. Recommendations and Policy on AI Assistance</span><span>4</span></div>
<div style="display: flex; justify-content: space-between;"><span>5. Submission Details</span><span>4</span></div>
<div style="display: flex; justify-content: space-between;"><span>6. Grading Criteria</span><span>4</span></div>
<div style="display: flex; justify-content: space-between;"><span>7. Team Collaboration</span><span>4</span></div>
<bn>
<bn>

**1. Assignment Overview** In this third phase of your database project, you will build upon the foundational work from Assignments 1 and
2. This assignment now begins with a final, critical evaluation of your relational schema to ensure its integrity and efficiency. Following this schema refinement, you will take a hands-on approach to apply your knowledge of SQL through MySQL. You will create the database structure, populate it with substantial sample data, and execute a variety of queries to demonstrate its functionality. This stage is crucial as it sets the groundwork for the project's final phase, where you will develop an application that interfaces with your database.
**2. Objectives** Upon successful completion of this assignment, you will be able to:
- Critically evaluate a relational schema for design flaws, redundancy, and adherence to 3NF and BCNF.
- Justify design decisions regarding normalization and potential de-normalization.
- Implement a refined relational database schema using SQL CREATE TABLE commands in MySQL.
- Populate a database with substantial, fabricated data suitable for testing.
- Write and execute various SQL commands, including complex queries (SELECT), data modifications (INSERT, UPDATE, DELETE), and view creation (CREATE VIEW).
- Gain hands-on experience using the MySQL server and MySQL Workbench.
**3. Assignment Details** **MySQL Installation and Setup**
- Install the MySQL server and MySQL Workbench following the "Installing MySQL" instructions.

-- page 2 --

- Login to the MySQL server, remove the anonymous user and change the root password if applicable. Use the "Getting Started with MySQL" guide to see how to execute these steps.
- Try simple commands like creating a table and inserting/retrieving data.
- (No credit will be given for this task, but it is essential for completing the assignment.) **Task 1: SQL Database Schema Creation**
- Based on your refined schema from**the previous assignment**, write an SQL database schema for your application using theCREATE TABLEcommands.
- Use referential constraints and consider using other constraints, indexes, and triggers as appropriate.
- Hand in a file with the commands you used to create your database schema. Show the response of the SQL Editor to the creation of each table (or, alternatively, use aDESCRIBE Client;query for each of your relations). **Task 2: Basic Data Insertion**
- Execute three distinct types ofINSERTcommands to insert tuples into one of your relations.
- TheINSERTcommands should be "interesting" so youdo not submit the sameINSERTstatement with different values (they will be considered the same). For example, use theINSERT... SELECTsyntax.
- Show the response of the SQL Editor and the relation that results when you issue a "SELECT *" command. **Task 3: Substantial Data Loading**
- Develop substantial data for your database and load it into your relations.
- You can write a program to fabricate this data (random or sequential) using any scripting language you wish. You are also permitted to use AI models to help generate data files orINSERTstatements. Note thatit is acceptable for string values to be meaningless. The point is to experiment with a realistic-sized database.
- The data you generate and load should be on the order of: o At least two relations with a few thousand tuples each. o At least one additional relation with hundreds of tuples.
- **Important Considerations:** o Make sure not to generate duplicated values for the keys in your relations. o Ensure you generate values that will join correctly (e.g.,clientNovalues in aRenttable must match
existingclientNovalues in theClienttable).

- With your report, include a small sample of meaningful records for each relation (5 or so records per relation).
- Once the data is loaded, export a copy of your database as a DUMP file using Workbench ("Server" > "Data Export"). **Task 4: SQL Queries (SELECT)**
- Write seven (7) queries on your application database using theSELECT-FROM-WHEREconstruct.
- To receive full credit, all but one of your queries should exhibit some "interesting" feature of SQL: queries over more than one relation, subqueries,EXISTS,GROUPBY, etc.
- The queries should be diverse (using different SQL features).
- Turn in a copy of all your SQL queries and the system's response.**Please do not turn in query results** **that are thousands of lines long.** **Task 5: Data Modification Commands**
- Write three (3) "interesting" data modification commands (INSERT,UPDATE,DELETE).
- These should involve a complex feature, such as inserting the result of a query, updating several tuples at once, or deleting a specific set of tuples.
- Hand in your modification commands and the response of the system. **Task 6: View Creation and Evaluation**
- Create two (2) views on top of your database schema.
- Hand in yourCREATE VIEWstatements and the responseof the system.
- Show a query involving each view and the system's response (truncate if large).
- Show a script of what happens when you try to modify your view (e.g., by inserting a new tuple).
- Are your views updatable? Explain why or why not. **NOTE:** All SQL statements must be according to ISOstandards as covered during lectures.

-- page 3 --

##### 4. Recommendations and Policy on AI Assistance

- **Policy on AI-Assisted Work:** 
    - **For Data Population (Task 3):** You are explicitly allowed to use scripting languages or AI models to help generate your sample data. The goal is to have a substantial, testable database. 
    - **For Queries (Tasks 4, 5, 6):** Get AI to thoroughly explain the logic, syntax, and execution of every query in an explaination.md file, to ensure that students understand the concepts are are ready to be questioned by the TA's
    - **Verification:** Be prepared for TAs to ask you specificquestions about your queries to verify your understanding. An inability to explain your submitted work may be considered an academic integrity issue.
##### 5. Submission Details

You must submit**two (2)**items to OWL:

**1. PDF Report**Upload a**single document**in PDF format containing:
- **For Tasks 1-6:** 
    - All your SQL statements and commands. 
    - The corresponding screenshots showing the response of the editor for each query/command. 
    - The small sample of data for Task 3. 
    - Your explanation of view updatability for Task 6.
**2. Code & Data Archive (.zip file)**Create and uploada**single .zip file**containing the following foldersand files:
- /SQL/folder: 
    - task3.sql: CREATETABLEstatements (from Task 1). 
    - task4.sql: INSERTstatements (from Task 2). 
    - task6.sql: SELECTstatements (from Task 4). 
    - task7.sql: Data modification statements (from Task 5). 
    - task8.sql: CREATE VIEWstatements (from Task 6).
- /SRC/folder: 
    - The source code you created to load and/or fabricate data (from Task 3).
- /DUMP/folder: 
    - The database dump file (from Task 3).
##### 6. Grading Criteria

Your assignment will be graded based on:

- Correct implementation of the refined schema using CREATE TABLE statements and constraints.
- Successful creation and loading of substantial, joinable data.
- Correctness, complexity, and diversity of the SELECT queries.
- Correctness and complexity of the data modification commands.
- Correct creation of views and correctness of the updatability analysis.
- Overall quality, organization, and completeness of the PDF report and the submitted code archive.
##### 7. Team Collaboration

-- page 4 --

Each group is expected to collaborate and contribute equally to the assignment. You will complete a team evaluation at the end of the next assignment (Assignment 4). If you wish, team members may parallelize completion of this assignment with Assignment 4 (e.g., some members work on back-end while others work on front-end, however all team members should be able to explain any line of code even if they did not work on it themselves).

-- page 5 --
