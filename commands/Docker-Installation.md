# Docker Installation on Ubuntu

## Overview
Docker lets you run applications in containers - isolated environments with all their dependencies bundled together. Airflow runs in Docker containers, which is why we need this.

---


```bash
# Prerequisites
sudo apt install -y ca-certificates curl gnupg

# GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# User permissions
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```