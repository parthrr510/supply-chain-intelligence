#!/usr/bin/env bash
set -e

# Validate Config
echo "Validating config..."
: "${DATABASE_PATH:?Environment variable DATABASE_PATH must be set}"
: "${MODEL_PATH:?Environment variable MODEL_PATH must be set}"

# Ensure artifacts
if [ ! -f "data_engineering/data/reports/dq_report.json" ]; then
    echo "DQ report not found. Generating DQ report..."
    python -m data_engineering.dq.run --input data_engineering/data-files
fi

if [ ! -f "$DATABASE_PATH" ]; then
    echo "Curated DB not found at $DATABASE_PATH. Running ingestion..."
    python -m data_engineering.pipeline.ingest --db-path "$DATABASE_PATH"
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Model artifact not found at $MODEL_PATH. Running ML pipeline..."
    python -m machine_learning.ml.train
fi

echo "Starting FastAPI..."
exec uvicorn api_interface.api.main:app --host 0.0.0.0 --port 8000
