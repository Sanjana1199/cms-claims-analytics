# Healthcare Claims Analytics — Complete Knowledge Guide

Everything you learned building this project, organized for interview prep and future reference.

---

## Part 1: Core Concepts

### Why Data Engineering Exists

Companies generate data across many different systems — apps, payment systems, sensors, databases. A data analyst who wants to answer a question that spans multiple systems can't query all of them at once.

**Data Engineering exists to:**
1. Extract data from different sources
2. Transform it into a clean, unified format
3. Load it into a single place (Data Warehouse) where analysts can query it

---

### ETL vs ELT

**ETL (Extract → Transform → Load)**
- Old school approach
- Clean/transform data BEFORE putting it in the warehouse
- Used when warehouses had limited compute (Oracle, Teradata)

**ELT (Extract → Load → Transform)**
- Modern approach
- Dump raw data into warehouse FIRST, transform inside
- Works because modern warehouses (Snowflake) have massive compute power

**The analogy:**
- ETL = Washing groceries in the parking lot before bringing them inside
- ELT = Bringing everything inside first, washing in the kitchen where you have a sink, counter space, and running water

**Interview answer:** "ELT is preferred with modern cloud warehouses because the warehouse has the compute power to handle transformations. It also preserves the raw data, so you can always reprocess if business logic changes."

---

### What is Snowflake?

A cloud data warehouse — a giant, powerful database in the cloud.

**Key difference from Oracle/Teradata:** Separation of Storage and Compute
- Oracle: Data and processing power on the same machine. Need more power? Buy a bigger machine.
- Snowflake: Data sits in cheap cloud storage (S3). Spin up compute when you need it, shut it off when you don't. Pay per second.

**Key Snowflake concepts:**
- **Database** — a folder that groups related data
- **Schema** — sub-folders within a database
- **Virtual Warehouse** — compute power (not a data warehouse, confusingly). You can have multiple sizes (X-Small to 4X-Large)
- **Stage** — temporary holding area for files being loaded

---

### What is dbt (data build tool)?

dbt is the "T" in ELT — it handles transformations inside your warehouse.

**A dbt model is just a SQL SELECT statement.** You write SELECT, dbt handles CREATE TABLE/INSERT.

**What dbt adds on top of SQL:**
- Automatic dependency ordering (if B depends on A, dbt runs A first)
- Version control (everything in Git)
- Built-in testing (unique, not_null, etc.)
- Auto-generated documentation with lineage graphs
- Jinja templating ({{ ref() }}, {{ source() }})

**Two versions:**
- **dbt Cloud** — paid, web-based, needs an account
- **dbt Core** — free, open-source, runs locally (what we used)

**Interview answer:** "I use dbt Core locally and manage the project through Git. It gives me full control over the pipeline and CI/CD integration."

**Important dbt functions:**
- `{{ source('schema', 'table') }}` — references a raw source table
- `{{ ref('model_name') }}` — references another dbt model (creates dependency tracking)

---

### Medallion Architecture (Staging → Intermediate → Marts)

How you organize data as it goes from messy to clean. Like a water purification plant.

**Layer 1: Raw / Bronze / Staging**
- Dirty water straight from the river
- Data as-is from source — just rename columns, cast types, remove junk
- NO joins, NO business logic
- Example: `stg_claims`, `stg_providers`

**Layer 2: Intermediate / Silver**
- Filtered water — impurities removed
- Join tables, deduplicate, apply business logic
- Not for analysts — it's a stepping stone
- Example: `int_claims_with_provider_details`

**Layer 3: Marts / Gold**
- Bottled water — clean, labeled, ready to drink
- Final tables that analysts and dashboards query
- Example: `fct_provider_claims`, `dim_providers`

**Why layers?** When something breaks, you can pinpoint WHERE. One giant SQL query = impossible to debug. Layers = "staging looks fine, problem is in the intermediate join."

**Interview tip:** Companies also call this "Bronze → Silver → Gold." Same concept, different names.

---

### Dimensional Modeling (Fact Tables vs Dimension Tables)

**Fact Tables** — Store measurements/events (things that happened)
- Claims submitted, payments made, services rendered
- Have numbers you can add up (amount, count, duration)
- Grow very large (millions/billions of rows)
- Named with `fct_` prefix

**Dimension Tables** — Store descriptions/context (things that describe facts)
- Who is the provider? What is the procedure? Where did it happen?
- Change slowly, much smaller
- Named with `dim_` prefix

**The analogy:**
- Fact table = A receipt (date, items, amounts)
- Dimension tables = The menu (item descriptions), staff list (who served you), location directory (which branch)

**Interview answer:** "Fact tables store measurable events — transactions, claims, clicks. Dimension tables store the descriptive context — who, what, where. Facts are large and grow fast, dimensions are smaller and change slowly."

---

### Data Quality Testing

What separates junior from senior engineers. Anyone can move data — the question is: how do you know it's correct?

**dbt built-in tests:**
- `unique` — no duplicate values
- `not_null` — no missing values
- `accepted_values` — only valid values
- `relationships` — foreign keys exist

**Why it matters:** Bad data costs money. Wrong enrollment count, overpaid hospital, incorrect dashboard. Tests catch problems BEFORE they reach the dashboard.

---

### What is CMS?

**CMS = Centers for Medicare & Medicaid Services**

Federal agency that runs:
- **Medicare** — health insurance for 65+ and disabled
- **Medicaid** — health insurance for low-income (what you work with at Illinois HFS)
- **CHIP** — Children's Health Insurance Program

CMS collects data on every claim from every provider/hospital billing Medicare/Medicaid. They publish some publicly for transparency.

**Analogy:** CMS is like the IRS but for healthcare. IRS collects tax records from everyone, CMS collects billing records from every doctor and hospital.

---

### Payment Variance

The difference between what a doctor CHARGES and what Medicare PAYS.

Formula: `(submitted_charge - medicare_payment) / submitted_charge * 100`

A doctor might charge $300 for a visit, but Medicare only pays $120. That's a 60% payment variance. This is a huge metric in healthcare analytics.

---

## Part 2: Step-by-Step — What We Built and Why

### Step 1: Set Up Snowflake
**What:** Created a free Snowflake trial account
**Why:** This is our cloud data warehouse where all data lives
**What we ran in Snowflake:**
```sql
CREATE DATABASE cms_analytics;
CREATE SCHEMA cms_analytics.raw;
CREATE SCHEMA cms_analytics.staging;
CREATE SCHEMA cms_analytics.intermediate;
CREATE SCHEMA cms_analytics.marts;
```
**What it means:** Created the database and one schema for each layer of our medallion architecture.

---

### Step 2: Install dbt
**What:** Ran `pip3 install dbt-snowflake` in terminal
**Why:** Installs dbt Core + the Snowflake connector
**Key files created:**
- `~/.dbt/profiles.yml` — Snowflake connection credentials (lives OUTSIDE the project so it never gets pushed to GitHub)
- `dbt_project.yml` — Project configuration (model paths, materialization settings)

**Materialization:**
- `view` — a saved SQL query, no data stored, runs on the fly (used for staging — lightweight)
- `table` — actual table with data stored, faster to query (used for intermediate and marts)

---

### Step 3: Download CMS Data
**What:** Downloaded two datasets from data.cms.gov
- Medicare Physician Utilization (9.6M rows, 2.9GB)
- Medicare Inpatient Hospitals (146K rows, 36MB)

**Why:** Real production-scale healthcare data for our pipeline

---

### Step 4: Load Data into Snowflake
**What:** Ran `load_data.py` which uses Snowflake's PUT + COPY INTO pattern
**How it works:**
1. `PUT` — uploads CSV from local machine to Snowflake's internal stage (compressed automatically)
2. `COPY INTO` — bulk loads from stage into the actual table

**Why PUT + COPY:** This is the production-standard way to load data into Snowflake. It handles compression, parallelism, and error tracking automatically.

---

### Step 5: Test dbt Connection
**What:** Ran `dbt debug` in terminal
**Why:** Verifies that dbt can connect to Snowflake using the credentials in profiles.yml
**Expected output:** "All checks passed!"

---

### Step 6: Create Source Configuration
**What:** Created `models/staging/_sources.yml`
**Why:** Tells dbt where the raw tables live. Enables lineage tracking and documentation. Single place to change if raw table names change.

---

### Step 7: Build Staging Models
**What:** Created SQL files in `models/staging/`:
- `stg_physician_utilization.sql`
- `stg_inpatient_hospitals.sql`

**What they do:**
- Rename cryptic CMS column names to readable names (e.g., `Rndrng_NPI` → `provider_npi`)
- Cast data types (strings to numbers)
- Filter out rows missing critical fields
- NO joins, NO business logic

**Command:** `dbt run --select staging`
**Result:** Creates views in Snowflake's staging schema

---

### Step 8: Build Intermediate Models
**What:** Created SQL files in `models/intermediate/`:
- `int_provider_specialty_metrics.sql` — aggregates by specialty and state
- `int_hospital_drg_metrics.sql` — aggregates by state and DRG

**What they do:**
- GROUP BY to aggregate data
- Calculate metrics like payment variance percentage
- Use `NULLIF()` to avoid divide-by-zero errors
- Use `COUNT(DISTINCT ...)` for unique counts

**Command:** `dbt run --select model_name`
**Result:** Creates tables in Snowflake's intermediate schema

---

### Step 9: Build Marts Models
**What:** Created SQL files in `models/marts/`:
- `fct_provider_claims.sql` — fact table (one row per provider per service)
- `dim_providers.sql` — dimension table (one row per unique provider)
- `dim_procedures.sql` — dimension table (one row per unique procedure)

**Command:** `dbt run --select marts`
**Result:** Creates tables in Snowflake's marts schema

---

### Step 10: Add Data Quality Tests
**What:** Created `models/marts/_schema.yml` with test definitions
**Tests added:** unique, not_null on critical columns
**Command:** `dbt test`
**Result:** 8 tests, all passed

---

### Step 11: Generate Documentation
**What:** Ran `dbt docs generate` then `dbt docs serve`
**Why:** Auto-generates a website with every model documented, plus a lineage graph showing data flow
**The lineage graph:** Visual map of raw → staging → intermediate → marts

---

### Step 12: Push to GitHub
**What:** Initialized git, created `.gitignore` (to exclude data/ folder), pushed to GitHub
**Key:** The `.gitignore` prevents the 3GB CSV files from being pushed. GitHub has a 100MB file limit.

---

## Part 3: Questions I Asked & Lessons Learned

### Q: "dbt model is just a SQL statement to create tables. But what if I want to look at an already existing table?"
**A:** dbt models CREATE new tables from existing data. They don't replace regular SQL queries. Use regular SQL in Snowflake UI to explore data (`SELECT * FROM table LIMIT 10`). dbt automates the creation of transformed tables.
- Regular SQL = looking inside your fridge
- dbt model = a recipe that takes ingredients and creates a finished dish

### Q: "I didn't create a dbt account. How were you able to connect dbt with Snowflake?"
**A:** There are two versions of dbt:
- dbt Cloud — paid, web-based, needs an account
- dbt Core — free, open-source, runs locally (what we installed with `pip install dbt-snowflake`)
dbt Core needs no account. It reads credentials from `~/.dbt/profiles.yml` and connects directly to Snowflake.

### Q: "Why are intermediate and marts combined in the lineage graph?"
**A:** Because both layers reference staging models directly — they're siblings, not parent-child. The marts models don't read FROM intermediate models. In a more complex project, marts would reference intermediate, creating a clear 3-level chain.

---

## Part 4: Errors I Hit & How to Fix Them

### Error: `ROWS` is a reserved keyword
**Query:** `SELECT 'physician' AS dataset, COUNT(*) AS rows FROM ...`
**Fix:** Rename the column: `COUNT(*) AS row_count`
**Lesson:** Snowflake has reserved words you can't use as column names. Common ones: `rows`, `order`, `group`, `table`, `column`.

### Error: YAML syntax error in `_schema.yml`
**Error:** `mapping values are not allowed in this context`
**Cause:** Extra spaces before `models:` — YAML is strict about indentation
**Fix:** Make sure `version` and `models` start at the very left edge (no leading spaces)
**Lesson:** YAML uses spaces for structure (like Python). Wrong indentation = broken file. Never use tabs in YAML.

### Error: Schema does not exist
**Query:** `SELECT * FROM cms_analytics.intermediate_intermediate.int_provider_specialty_metrics`
**Cause:** dbt names schemas as `<default_schema>_<custom_schema>`. Default schema in profiles.yml was `staging`, custom was `intermediate`, so actual schema = `staging_intermediate`
**Fix:** Use `staging_intermediate` instead of `intermediate_intermediate`
**Lesson:** Check actual schema names in Snowflake's Database Explorer sidebar.

### Note: `cd` path with spaces
**Problem:** Terminal breaks the path at the space in "Portfolio Projects"
**Fix:** Always wrap paths with spaces in double quotes: `cd "/path/with spaces/here"`
**Alternative:** Use backslash: `cd /path/with\ spaces/here`
**Pro tip:** Type `cd ` then drag the folder from Finder into Terminal.

---

## Part 5: Key dbt Commands Reference

```bash
# Test connection
dbt debug

# Run all models
dbt run

# Run specific folder
dbt run --select staging
dbt run --select marts

# Run one model
dbt run --select int_provider_specialty_metrics

# Run tests
dbt test

# Generate docs
dbt docs generate

# View docs in browser
dbt docs serve

# Check version
dbt --version
```

---

## Part 6: Key Snowflake Commands Reference

```sql
-- Check your account info
SELECT current_account(), current_region(), current_role(), current_warehouse();

-- Create database and schemas
CREATE DATABASE cms_analytics;
CREATE SCHEMA cms_analytics.raw;

-- Count rows
SELECT COUNT(*) AS row_count FROM cms_analytics.raw.physician_utilization;

-- Preview data
SELECT * FROM cms_analytics.raw.physician_utilization LIMIT 10;

-- Create file format for CSV loading
CREATE FILE FORMAT csv_format
    TYPE = CSV
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1;
```

---

## Part 7: Project File Structure

```
Project1-Healthcare-Claims-Analytics/
├── models/
│   ├── staging/                          ← Layer 1: Clean raw data
│   │   ├── _sources.yml                  ← Defines where raw tables live
│   │   ├── stg_physician_utilization.sql ← Clean physician data
│   │   └── stg_inpatient_hospitals.sql   ← Clean hospital data
│   ├── intermediate/                     ← Layer 2: Aggregate & enrich
│   │   ├── int_provider_specialty_metrics.sql
│   │   └── int_hospital_drg_metrics.sql
│   └── marts/                            ← Layer 3: Final analytics tables
│       ├── _schema.yml                   ← Data quality test definitions
│       ├── fct_provider_claims.sql       ← Fact table
│       ├── dim_providers.sql             ← Dimension: who
│       └── dim_procedures.sql            ← Dimension: what
├── tests/                                ← Custom test SQL files
├── macros/                               ← Reusable SQL snippets
├── seeds/                                ← Small reference CSVs
├── data/                                 ← Raw CMS CSVs (gitignored)
├── dbt_project.yml                       ← Project configuration
├── load_data.py                          ← Python script to load data into Snowflake
├── lineage_graph.png                     ← Screenshot of dbt lineage
├── .gitignore                            ← Excludes data/, logs/, target/
└── README.md                             ← Project documentation
```

**Files NOT in the project (by design):**
- `~/.dbt/profiles.yml` — Snowflake credentials. Lives in home directory so passwords never go to GitHub.
