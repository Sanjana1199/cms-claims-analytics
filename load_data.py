"""
Load CMS data into Snowflake.

This script:
1. Connects to Snowflake
2. Creates raw tables
3. Uploads CSV files using PUT (stages the file)
4. Loads data using COPY INTO (loads from stage to table)

This is how data loading works in production Snowflake environments.
"""

import snowflake.connector
import os

# Connect to Snowflake
conn = snowflake.connector.connect(
    user='Sanjana1199',
    password=os.environ['SNOWFLAKE_PASSWORD'],
    account='WP59143.ca-central-1.aws',
    warehouse='COMPUTE_WH',
    database='CMS_ANALYTICS',
    role='ACCOUNTADMIN'
)

cursor = conn.cursor()

print("Connected to Snowflake!")

# Use the RAW schema — this is our bronze/raw layer
cursor.execute("USE SCHEMA raw")

# --- Create file format ---
# This tells Snowflake how to read our CSV files
print("Creating file format...")
cursor.execute("""
    CREATE OR REPLACE FILE FORMAT csv_format
        TYPE = CSV
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        NULL_IF = ('', 'NULL', 'null')
        EMPTY_FIELD_AS_NULL = TRUE
""")

# --- Load Inpatient Hospitals Data (smaller file first) ---
print("\n--- Loading Inpatient Hospitals Data ---")

cursor.execute("""
    CREATE OR REPLACE TABLE raw.inpatient_hospitals (
        Rndrng_Prvdr_CCN VARCHAR,
        Rndrng_Prvdr_Org_Name VARCHAR,
        Rndrng_Prvdr_City VARCHAR,
        Rndrng_Prvdr_St VARCHAR,
        Rndrng_Prvdr_State_FIPS VARCHAR,
        Rndrng_Prvdr_Zip5 VARCHAR,
        Rndrng_Prvdr_State_Abrvtn VARCHAR,
        Rndrng_Prvdr_RUCA VARCHAR,
        Rndrng_Prvdr_RUCA_Desc VARCHAR,
        DRG_Cd VARCHAR,
        DRG_Desc VARCHAR,
        Tot_Dschrgs NUMBER,
        Avg_Submtd_Cvrd_Chrg FLOAT,
        Avg_Tot_Pymt_Amt FLOAT,
        Avg_Mdcr_Pymt_Amt FLOAT
    )
""")
print("  Table created.")

# PUT uploads the file to Snowflake's internal stage
print("  Uploading file to stage...")
cursor.execute(
    "PUT file:///Users/sanjanareddy/Desktop/Portfolio Projects/Project1-Healthcare-Claims-Analytics/data/inpatient_hospitals.csv @%inpatient_hospitals AUTO_COMPRESS=TRUE"
)
print("  File staged.")

# COPY INTO loads from stage into the table
print("  Loading into table...")
cursor.execute("""
    COPY INTO raw.inpatient_hospitals
    FROM @%inpatient_hospitals
    FILE_FORMAT = csv_format
    ON_ERROR = 'CONTINUE'
""")
result = cursor.fetchone()
print(f"  Loaded! Status: {result[0]}, Rows: {result[3]}, Errors: {result[5]}")

# --- Load Physician Utilization Data (large file) ---
print("\n--- Loading Physician Utilization Data ---")
print("  This is a 2.9GB file with 9.6M rows — it will take a few minutes...")

cursor.execute("""
    CREATE OR REPLACE TABLE raw.physician_utilization (
        Rndrng_NPI VARCHAR,
        Rndrng_Prvdr_Last_Org_Name VARCHAR,
        Rndrng_Prvdr_First_Name VARCHAR,
        Rndrng_Prvdr_MI VARCHAR,
        Rndrng_Prvdr_Crdntls VARCHAR,
        Rndrng_Prvdr_Ent_Cd VARCHAR,
        Rndrng_Prvdr_St1 VARCHAR,
        Rndrng_Prvdr_St2 VARCHAR,
        Rndrng_Prvdr_City VARCHAR,
        Rndrng_Prvdr_State_Abrvtn VARCHAR,
        Rndrng_Prvdr_State_FIPS VARCHAR,
        Rndrng_Prvdr_Zip5 VARCHAR,
        Rndrng_Prvdr_RUCA VARCHAR,
        Rndrng_Prvdr_RUCA_Desc VARCHAR,
        Rndrng_Prvdr_Cntry VARCHAR,
        Rndrng_Prvdr_Type VARCHAR,
        Rndrng_Prvdr_Mdcr_Prtcptg_Ind VARCHAR,
        HCPCS_Cd VARCHAR,
        HCPCS_Desc VARCHAR,
        HCPCS_Drug_Ind VARCHAR,
        Place_Of_Srvc VARCHAR,
        Tot_Benes NUMBER,
        Tot_Srvcs NUMBER,
        Tot_Bene_Day_Srvcs NUMBER,
        Avg_Sbmtd_Chrg FLOAT,
        Avg_Mdcr_Alowd_Amt FLOAT,
        Avg_Mdcr_Pymt_Amt FLOAT,
        Avg_Mdcr_Stdzd_Amt FLOAT
    )
""")
print("  Table created.")

print("  Uploading file to stage (this will take a few minutes)...")
cursor.execute(
    "PUT file:///Users/sanjanareddy/Desktop/Portfolio Projects/Project1-Healthcare-Claims-Analytics/data/physician_utilization.csv @%physician_utilization AUTO_COMPRESS=TRUE"
)
print("  File staged.")

print("  Loading into table...")
cursor.execute("""
    COPY INTO raw.physician_utilization
    FROM @%physician_utilization
    FILE_FORMAT = csv_format
    ON_ERROR = 'CONTINUE'
""")
result = cursor.fetchone()
print(f"  Loaded! Status: {result[0]}, Rows: {result[3]}, Errors: {result[5]}")

# --- Verify ---
print("\n--- Verification ---")
cursor.execute("SELECT COUNT(*) FROM raw.inpatient_hospitals")
print(f"  Inpatient rows: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT COUNT(*) FROM raw.physician_utilization")
print(f"  Physician rows: {cursor.fetchone()[0]:,}")

print("\nAll data loaded successfully!")

cursor.close()
conn.close()
