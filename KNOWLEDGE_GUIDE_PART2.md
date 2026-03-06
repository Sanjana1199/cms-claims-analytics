# Healthcare Claims Analytics — Part 2: Orchestration with Airflow

Everything you learned adding pipeline orchestration to the project.

---

## Part 1: Core Concepts

### What is Orchestration?

Orchestration is telling your pipeline **when to run, in what order, and what to do when something breaks.**

Without orchestration, YOU are the orchestrator — you open terminal, type `dbt run`, check if it worked. If you go on vacation, nothing runs.

**The analogy:**
- **Without orchestration:** A chef personally walks to the pantry, grabs ingredients, chops vegetables, fires up the stove, cooks, plates, and serves. One person doing everything manually.
- **With orchestration:** A kitchen manager has the full recipe card. They tell the prep cook "chop onions first." When that's done, they tell the line cook "start the sauce." If the sauce burns, they don't let the food go out — they alert the head chef.

**Airflow is your kitchen manager.**

**Interview answer:** "Orchestration automates the scheduling, dependency management, and error handling of data pipelines. I use Airflow to define DAGs that run my dbt models on a schedule, with retry logic and alerting so failures don't go unnoticed."

---

### What Does an Orchestrator Do?

| Capability | Example |
|---|---|
| **Scheduling** | "Run this pipeline every day at 6 AM" |
| **Dependency ordering** | "Don't run dbt until the data load finishes" |
| **Retry on failure** | "If Snowflake times out, try again 3 times" |
| **Alerting** | "If dbt test fails, send me a Slack message" |
| **Logging** | "Show me exactly which step failed and why" |
| **Backfilling** | "We missed Monday's run — go back and run it for Monday" |

---

### What is Apache Airflow?

The most popular orchestrator in data engineering. You write your pipeline as a **DAG** (Directed Acyclic Graph).

**DAG = Steps in order, no loops.** That's it. Forget the fancy name.

```
dbt_run  →  dbt_test  →  log_success
```

Each box is a **task**. The arrows are **dependencies**. Airflow runs them in order, tracks success/failure, and gives you a web UI to monitor everything.

**Two versions:**
- **Airflow 2.x** — stable, widely used in production (what we used)
- **Airflow 3.x** — newest release, requires Python 3.10+

---

### Key Airflow Concepts

- **DAG** — A Python file that defines your pipeline steps and their order
- **Task** — A single step in the pipeline (e.g., "run dbt")
- **Operator** — The type of task (BashOperator runs shell commands, PythonOperator runs Python functions)
- **Schedule** — When the DAG runs (`@daily`, `@hourly`, cron expressions)
- **Web UI** — Browser dashboard at `localhost:8080` to monitor runs
- **Scheduler** — Background process that triggers DAGs on schedule
- **`>>` operator** — Defines task dependencies (`task_a >> task_b` means "run A before B")

---

### What is Snowflake's Role?

Snowflake is NOT a front end. It's the **brain** — the place where all data lives and gets processed.

```
Your project is a factory:

CSV files (raw materials)     → sitting on your laptop
Snowflake (the factory floor) → where materials get stored AND processed
dbt (the machines)            → transforms raw materials into finished products
Airflow (the factory manager) → schedules when machines run
Power BI (the showroom)       → the front end, where people see results
```

Snowflake does two jobs:
1. **Storage** — holds all 9.8 million rows
2. **Compute** — when dbt runs SQL, Snowflake executes it

**Interview answer:** "Snowflake serves as both the storage and compute layer. Raw data is loaded into Snowflake, and dbt sends transformation SQL to Snowflake's compute engine. The separation of storage and compute means I can scale processing power independently of data volume."

---

## Part 2: Step-by-Step — What We Built

### Step 1: Install Airflow

**What:** Installed Apache Airflow via pip
**Why:** Airflow is our orchestrator — the kitchen manager for our pipeline

**What happened:**
- First installed Airflow 3.0.6 but it didn't work with Python 3.9 (needed Python 3.10+)
- Uninstalled Airflow 3, installed Airflow 2.10.5 with constraints file
- Had to fix `typing_extensions` version conflict left behind by Airflow 3

**Command:** `pip3 install "apache-airflow==2.10.5" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.9.txt"`

**Lesson:** Always check Python version compatibility before installing. Use constraints files for complex packages like Airflow.

---

### Step 2: Initialize Airflow

**What:** Set up Airflow's internal database and created admin user
**Commands:**
```bash
airflow db init          # Creates Airflow's internal SQLite database
airflow standalone       # Starts everything + creates admin user automatically
```

**Key files created:**
- `~/airflow/airflow.cfg` — Airflow configuration (like dbt's profiles.yml)
- `~/airflow/airflow.db` — SQLite database tracking all DAG runs

---

### Step 3: Configure Airflow

**What:** Pointed Airflow to our project's dags folder and turned off example DAGs

**Changes in `~/airflow/airflow.cfg`:**
1. `dags_folder` → set to our project's `/dags` directory
2. `load_examples` → changed from `True` to `False`

**Why:** By default, Airflow loads 30+ example DAGs and looks in `~/airflow/dags`. We want it to only show our DAGs from our project folder.

---

### Step 4: Write the DAG

**What:** Created `dags/cms_claims_pipeline.py`
**Why:** This is our recipe card — tells Airflow what to run and in what order

**The DAG does three things in order:**
1. `dbt_run` — Runs all dbt models (staging → intermediate → marts)
2. `dbt_test` — Runs all 8 data quality tests
3. `log_success` — Logs a success message

**Key code explained:**
```python
# This line defines the order
dbt_run >> dbt_test >> log_success
```
The `>>` means "run left side first, then right side." If dbt_run fails, dbt_test and log_success won't run.

**Schedule:** `@daily` means Airflow runs this pipeline once per day automatically.

---

### Step 5: Run the Pipeline

**What:** Triggered the DAG from Airflow's web UI
**How:**
1. Toggled the DAG on (unpause)
2. Clicked play button → "Trigger DAG"
3. Watched tasks go from queued → running → success (green)

**First run failed** because of a `protobuf` version conflict between Airflow and dbt.
**Fix:** `pip3 install "protobuf>=6.0"`
**Second run:** All 3 tasks succeeded (green).

---

## Part 3: Errors & Troubleshooting

### Error: Python 3.9 incompatible with Airflow 3
**Error:** `TypeError: StringConstraints() takes no arguments`
**Cause:** Airflow 3.0 requires Python 3.10+. Our Mac has Python 3.9.
**Fix:** Uninstalled Airflow 3, installed Airflow 2.10.5 which supports Python 3.9.
**Lesson:** Always check version requirements. `python3 --version` tells you what you have.

### Error: google-re2 compilation failure
**Error:** `fatal error: 'absl/strings/string_view.h' file not found`
**Cause:** The `google-re2` package tried to compile from source and failed.
**Fix:** Upgraded pip (`pip3 install --upgrade pip`) so it could find pre-built binary packages.
**Lesson:** Older pip versions can't find pre-built wheels. Keep pip updated.

### Error: typing_extensions too old
**Error:** `ImportError: cannot import name 'Sentinel' from 'typing_extensions'`
**Cause:** Airflow 3 left behind packages that needed newer `typing_extensions`.
**Fix:** `pip3 install --upgrade typing_extensions`
**Lesson:** When switching between major versions of a package, leftover dependencies can cause conflicts. Clean uninstall first.

### Error: Cannot use SQLite with LocalExecutor
**Error:** `AirflowConfigException: error: cannot use SQLite with the LocalExecutor`
**Cause:** Airflow 3's config set the executor to LocalExecutor, but SQLite only supports SequentialExecutor.
**Fix:** Deleted `~/airflow` folder and re-initialized with Airflow 2's defaults.
**Lesson:** When downgrading, delete old config files to avoid conflicts.

### Error: DAG IndentationError
**Error:** `IndentationError: unexpected indent` on line 9
**Cause:** Extra spaces in the Python file from copy-paste.
**Fix:** Ensured all top-level code starts at column 1 (no leading spaces), and code inside `with DAG` block is indented by exactly 4 spaces.
**Lesson:** Python is strict about indentation (like YAML). Use a code editor like Cursor that shows spaces.

### Error: EOL while scanning string literal
**Error:** `SyntaxError: EOL while scanning string literal` on line 32
**Cause:** A string got split across two lines when pasting.
**Fix:** Kept the entire string on one line.
**Lesson:** Python strings cannot span multiple lines unless you use triple quotes (`"""..."""`).

### Error: protobuf version conflict
**Error:** `TypeError: MessageToJson() got an unexpected keyword argument 'always_print_fields_with_no_presence'`
**Cause:** Airflow's constraints file installed protobuf 4.25, but dbt needs protobuf 6+.
**Fix:** `pip3 install "protobuf>=6.0"`
**Lesson:** When two tools share a Python environment, their dependencies can conflict. In production, you'd use separate virtual environments or Docker.

### Error: URL split across lines
**Error:** `Failed to establish a new connection: raw.githubusercont ent.com`
**Cause:** Long pip install command wrapped to the next line in terminal, breaking the URL.
**Fix:** Pasted the command as one continuous line.
**Lesson:** Long commands must be pasted as a single line. If you need to break a command, use `\` at the end of each line.

---

## Part 4: Key Airflow Commands Reference

```bash
# Check version
airflow version

# Initialize database
airflow db init

# Start everything (dev mode)
airflow standalone

# List your DAGs
airflow dags list

# Check for DAG errors
airflow dags list-import-errors

# Trigger a DAG manually
airflow dags trigger cms_claims_pipeline
```

---

## Part 5: Updated Project File Structure

```
Project1-Healthcare-Claims-Analytics/
├── models/                              (dbt models - Part 1)
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── dags/                                (Airflow DAGs - Part 2)
│   └── cms_claims_pipeline.py           ← The orchestration pipeline
├── data/                                (Raw CSVs - gitignored)
├── tests/
├── macros/
├── seeds/
├── dbt_project.yml
├── load_data.py
├── lineage_graph.png
├── DAG_Graph.png                        ← Airflow DAG screenshot
├── .gitignore
├── README.md
├── KNOWLEDGE_GUIDE.md                   ← Part 1 concepts & steps
└── KNOWLEDGE_GUIDE_PART2.md             ← Part 2 concepts & steps (this file)
```

**Files NOT in the project (by design):**
- `~/.dbt/profiles.yml` — Snowflake credentials
- `~/airflow/airflow.cfg` — Airflow configuration (contains local paths)
- `~/airflow/airflow.db` — Airflow's internal database
