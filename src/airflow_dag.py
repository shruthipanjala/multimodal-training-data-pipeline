"""Airflow DAG - how this pipeline is scheduled in production form.
The stage logic lives in pipeline.py; this file is the orchestration layer.
"""
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import generate_sample_data
import pipeline

with DAG(
    dag_id="multimodal_training_data_pipeline",
    description="Ingest sessions, run quality gates, quarantine bad captures, deliver model-ready datasets",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False,
    tags=["training-data", "quality-gates"],
) as dag:
    generate = PythonOperator(task_id="generate_sample_sessions",
                              python_callable=generate_sample_data.main)
    run = PythonOperator(task_id="ingest_validate_transform_load",
                         python_callable=pipeline.main)
    generate >> run
