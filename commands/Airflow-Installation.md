# Airflow Setup on EC2

## What is Airflow?

Apache Airflow is a workflow orchestration tool. It schedules and monitors data pipelines. Think of it as a task scheduler that:
- Runs Python scripts on a schedule (e.g., every Monday)
- Manages dependencies between tasks (Task B waits for Task A)
- Provides a web UI to monitor success/failure
- Retries failed tasks automatically

For this project, Airflow will:
1. Extract data from FDA API weekly
2. Upload JSON files to S3
3. Load data into Snowflake
4. Run dbt transformations

---

## Why Docker for Airflow?

Airflow has many components (web server, scheduler, database). Installing them manually is complex. Docker Compose lets us run all components with one command using pre-configured containers.

---

## Folder Structure
```bash
mkdir -p ~/airflow/{dags,logs,plugins,config}
cd ~/airflow
```

| Folder | Purpose |
|--------|---------|
| `dags/` | Pipeline code (DAG) |
| `logs/` | Execution logs for debugging |
| `plugins/` | Custom extensions (we won't use this) |
| `config/` | Configuration files |

---

## Create Environment File
```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

This tells Docker to run Airflow as user, so file permissions work correctly.

---

## Lightweight Docker Compose Configuration

The official Airflow docker-compose.yaml requires 4GB+ RAM (CeleryExecutor with Redis and workers). t3.small instance only has ~2GB.

**Solution:** Use LocalExecutor instead - removes Redis and worker containers, uses less memory.

### Create the lightweight config:
```bash
cat > docker-compose.yaml << 'EOF'
version: '3.8'
x-airflow-common:
  &airflow-common
  image: apache/airflow:2.10.4
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG: 'true'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_MIGRATE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"
    volumes:
      - .:/sources

volumes:
  postgres-db-volume:
EOF
```

### Key differences from full config:

| Setting | Full Config | Lightweight Config |
|---------|-------------|-------------------|
| Executor | CeleryExecutor | LocalExecutor |
| Redis | Required | Not needed |
| Workers | Separate containers | Scheduler runs tasks |
| RAM needed | 4GB+ | ~1GB |
| Containers | 6+ | 3 |

---

## Initialize and Start Airflow

### Initialize database (one-time setup):
```bash
docker compose up airflow-init
```

Wait for `exited with code 0` (success).

### Start Airflow:
```bash
docker compose up -d
```

| Part | Meaning |
|------|---------|
| `docker compose up` | Start all containers defined in docker-compose.yaml |
| `-d` | Detached mode - runs in background |

### Verify containers are running:
```bash
docker ps
```

3 containers:
- airflow-postgres-1
- airflow-webserver-1
- airflow-scheduler-1

---

## Accessing Airflow Web UI

### The Problem

Accessing `http://<EC2_IP>:8080` directly may be blocked by ISP (AT&T, etc.) as a "phishing page" because it's an unknown IP with a login form.

### The Solution: SSH Tunneling

SSH tunneling creates an encrypted connection that forwards traffic from local machine to the EC2 server.
```
Without tunnel:  Browser → Internet → EC2:8080 (BLOCKED by ISP)
With tunnel:     Browser → localhost:8080 → SSH tunnel → EC2:8080 (WORKS)
```

### Connect with SSH tunnel:
```powershell
ssh -i C:\Users\Admin\.ssh\medtech-key-luke.pem -L 8080:localhost:8080 ubuntu@3.17.208.129
```

| Part | Meaning |
|------|---------|
| `-L 8080:localhost:8080` | Forward local port 8080 through tunnel to EC2's localhost:8080 |
| First `8080` | Port on your Windows machine |
| `localhost:8080` | Where to connect on the EC2 side |

### Access in browser:
```
http://localhost:8080
```

### Login credentials:

- Username: `airflow`
- Password: `airflow`

---

## Useful Commands
```bash
# Check container status
docker ps

# View logs for a specific container
docker compose logs airflow-webserver
docker compose logs airflow-scheduler

# Follow logs in real-time
docker compose logs -f

# Stop all containers
docker compose down

# Restart all containers
docker compose restart

# Stop and remove everything (including database)
docker compose down -v
```

---

## Troubleshooting

**Containers not starting?**
```bash
docker compose logs
```

**Web UI not loading?**
- Make sure using SSH tunnel
- Check webserver is running: `docker ps`
- Check webserver logs: `docker compose logs airflow-webserver`

**"Not enough memory" warning?**
- Use the lightweight docker-compose.yaml (LocalExecutor)
- Don't use the official full config on t3.small

**IP address changed?**
- EC2 public IP changes on reboot
- Check new IP in AWS Console → EC2 → Instances
- Update SSH command with new IP

---

## Current EC2 Instance Details

| Item | Value |
|------|-------|
| Instance ID | i-0246f3c2e8d60d161 |
| Public IP | (changes on reboot) |
| SSH User | ubuntu |
| Key file | C:\Users\Admin\.ssh\medtech-key-luke.pem |

---

## Quick Start (for future sessions)

1. **Connect with tunnel:**
```powershell
ssh -i C:\Users\Admin\.ssh\medtech-key-luke.pem -L 8080:localhost:8080 ubuntu@<CURRENT_PUBLIC_IP>
```

2. **If containers stopped, start them:**
```bash
cd ~/airflow
docker compose up -d
```

3. **Open browser:**
```
http://localhost:8080
```