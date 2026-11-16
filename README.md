Multimodal AI Training Data Pipeline — Sample Project

A working, from-scratch sample of the Centific production project: automated

pipelines that turn raw participant camera-session data into clean,

validated, model-ready training datasets for an AI human-activity

detection model.

What it does

Live collection sessions produce multimodal data — several forms of data

about the same event:

Mode

File

Contents

Video info

video\_info.json

recording size, frame rate, duration

Metadata

metadata.json

participant, guided task, device, timestamp

Motion

motion.csv

motion samples captured during the task

Calibration

calibration.json

device/camera calibration record

The pipeline ingests all four modes together, audits every session against

automated quality gates, quarantines bad captures with a recorded

reason, and delivers only validated data as the training dataset.

Run it

python3 src/generate\_sample\_data.py   # creates 40 sample sessions (6 deliberately defective)

python3 src/pipeline.py               # ingest → validate → transform → load

Sample run results

40 sessions ingested

34 passed all quality gates → data/clean/training\_dataset.csv

6 quarantined → data/quarantine/quarantine\_log.csv, one per defect type:

&#x20; empty/corrupt video · low frame rate (10 fps) · missing metadata ·

&#x20; calibration device mismatch · empty motion file · duplicate session ID

100% of delivered rows passed every gate — the sample-scale version of

&#x20; the production pipeline's 98%+ accuracy standard

Quality gate rules

A session is quarantined if any of these fail:

Metadata complete (session, participant, task, device all present)

Video file not empty/corrupt (size ≥ 1 MB)

Frame rate ≥ 24 fps

Recording duration ≥ 4 seconds

Calibration device matches the session's device

Motion data present (≥ 100 samples)

Session ID not a duplicate

Quarantined data is isolated, never deleted and never loaded — it can be

reviewed or recollected, and it can never reach model training.

Project structure

src/

&#x20; generate\_sample\_data.py   # builds the raw sample sessions

&#x20; pipeline.py               # ingest → quality gates → transform → load

&#x20; airflow\_dag.py            # Airflow orchestration (production scheduling form)

data/

&#x20; raw/sessions/             # one folder per session, four files per session

&#x20; clean/                    # training\_dataset.csv + manifest.json

&#x20; quarantine/               # quarantine\_log.csv with failure reasons

How this maps to the production project

Sample project

Production (Centific)

Local session folders

Raw video + metadata streams from live sessions on AWS \& Azure

pipeline.py stages

Cross-cloud ETL pipelines in Python + dbt

airflow\_dag.py

Airflow DAGs scheduling and monitoring multi-stage workflows

Quality gates in code

Programmatic validation rules holding 98%+ data accuracy

training\_dataset.csv

Clean, structured datasets loaded into OneForma

Manual steps: none

Standardized automation cut manual prep time by 40%

Stack: Python · Apache Airflow · dbt (production transforms) · AWS ·

Microsoft Azure · OneForma · SQL

