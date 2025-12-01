```bash
# Stop containers (from ~/airflow directory)
    cd ~/airflow
    docker compose down

# Disconnect SSH
    exit

# Stop EC2
    Instance state → Stop instance

# To restart:
    # 1. AWS Console → EC2 → Start instance
    # 2. Copy the new public IP
    # 3. Connect with tunnel:
        ssh -i C:\Users\Admin\.ssh\medtech-key-luke.pem -L 8080:localhost:8080 ubuntu@<NEW_IP>
    # 4. Start Airflow:
        cd ~/airflow
        docker compose up -d

# View file content
    cat filename.ext 

# Creating files on EC2
    cat > filename.ext << 'EOF' # cat > - write output to a file (overwrites if exists)
    "...content goes here..."
    EOF


'''