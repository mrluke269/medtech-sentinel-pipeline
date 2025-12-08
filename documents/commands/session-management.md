
```bash
# EC2 / Docker Commands
# SSH to EC2
ssh -i <key.pem> ubuntu@<public-ip>
# tunneling
ssh -i "key.pem" -L 8080:localhost:8080 ubuntu@<public-ip>

# Run Docker
docker-compose up -d

# Enter Airflow container
docker exec -it airflow_airflow-scheduler_1 bash

# View container logs
docker logs airflow_airflow-scheduler_1 --tail 50

# Check container health
docker ps

# Create files on EC2 (overwrite if exists)
cat > filename.ext << 'EOF'
...content goes here...
EOF

# Airflow Commands (inside container)
# Run backfill
airflow dags backfill -s 2024-01-01 -e 2025-12-05 extract_fda_events_v2

# List DAG runs
airflow dags list-runs -d extract_fda_events_v2

#dbt Commands (inside container)
cd /opt/airflow/dbt

# Full refresh all models
dbt run --full-refresh --target prod

# Run specific model
dbt run --select fct_adverse_events --target prod

# Run tests
dbt test --target prod

# S3 Commands (from local Windows)
# List files
aws s3 ls s3://medtech-sentinel-raw-luke/data/heart-valves/

# Check bucket contents
aws s3 ls s3://medtech-sentinel-raw-luke/data/ --recursive