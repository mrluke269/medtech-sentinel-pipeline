# Docker Installation on Ubuntu

## Overview
Docker lets you run applications in containers - isolated environments with all their dependencies bundled together. Airflow runs in Docker containers, which is why we need this.

---

## Prerequisites Installation
```bash
sudo apt install -y ca-certificates curl gnupg
```

| Part | Meaning |
|------|---------|
| `sudo` | "Super user do" - run as administrator (like "Run as Admin" on Windows) |
| `apt` | Ubuntu's package manager (like an app store for the command line) |
| `install` | Install these packages |
| `-y` | Auto-answer "yes" to prompts |
| `ca-certificates` | Security certificates for HTTPS connections |
| `curl` | Tool to download files from URLs |
| `gnupg` | Encryption tool for verifying downloads are legitimate |

**Why:** These tools are needed to securely download Docker from the internet.

---

## Add Docker's GPG Key
```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

| Command | Meaning |
|---------|---------|
| `install -m 0755 -d /etc/apt/keyrings` | Create a folder for security keys with proper permissions |
| `curl -fsSL https://...` | Download Docker's public key from their website |
| `| sudo gpg --dearmor -o ...` | Pipe: convert the key to Ubuntu's format and save it |
| `chmod a+r` | Make the key readable by all users |

**Why:** GPG keys verify that software actually comes from Docker, not a hacker pretending to be Docker.

---

## Add Docker Repository
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Breaking this down:
- `echo "deb [...]"` - Output a line of text
- `arch=$(dpkg --print-architecture)` - Your CPU type (amd64)
- `$(lsb_release -cs)` - Your Ubuntu version name (noble for 24.04)
- `signed-by=...` - Verify downloads using the GPG key we added
- `| sudo tee ...` - Pipe: write that text to a file with admin rights
- `> /dev/null` - Suppress output to terminal

**Why:** Docker isn't in Ubuntu's default app store. We're adding Docker's official repository so `apt` knows where to find it.

---

## Install Docker
```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

| Package | Purpose |
|---------|---------|
| `docker-ce` | Docker Community Edition - the main engine |
| `docker-ce-cli` | Command line tools for Docker |
| `containerd.io` | The underlying container runtime |
| `docker-compose-plugin` | Tool for running multi-container apps (needed for Airflow) |

---

## Add User to Docker Group
```bash
sudo usermod -aG docker $USER
```

| Part | Meaning |
|------|---------|
| `usermod` | Modify a user account |
| `-aG docker` | Append to the "docker" group |
| `$USER` | Variable containing your username (ubuntu) |

**Why:** By default, only root can run Docker. This lets your normal user run Docker commands without typing `sudo` every time.

---

## Apply Group Change
```bash
newgrp docker
```

Refreshes your session to recognize you're now in the docker group. Otherwise you'd have to log out and back in.

---

## Verify Installation
```bash
docker --version
```

Expected output: `Docker version 27.x.x` (or similar)

---

## Quick Reference - All Commands
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