from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

DBT_PROJECT_DIR = "/Users/sanjanareddy/Desktop/Portfolio Projects/Project1-Healthcare-Claims-Analytics"

with DAG(
    dag_id="cms_claims_pipeline",
    description="ELT pipeline: runs dbt models and tests for CMS claims data",
    schedule_interval="@daily",
    start_date=datetime(2026, 3, 1),
    catchup=False,
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd '{DBT_PROJECT_DIR}' && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd '{DBT_PROJECT_DIR}' && dbt test",
    )

    log_success = BashOperator(
        task_id="log_success",
        bash_command="echo 'CMS Claims pipeline completed successfully'",
    )

    dbt_run >> dbt_test >> log_success
