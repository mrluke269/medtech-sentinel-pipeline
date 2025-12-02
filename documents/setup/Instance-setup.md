# EC2 Instance Setup

## Instance Configuration

| Setting | Value |
|---------|-------|
| Name | MedTech-Airflow-Host |
| AMI | Ubuntu Server 24.04 LTS |
| Instance type | t3.small|
| Key pair | medtech-key-luke (RSA, .pem) |
| Region | us-east-2 (Ohio) |


---

## Security Group Configuration

**Name:** medtech-airflow-sg

### Inbound Rules

| Port | Type | Source | Purpose |
|------|------|--------|---------|
| 22 | SSH | My IP | Terminal access to server |
| 8080 | Custom TCP | My IP | Airflow web UI |


**Note:** If home IP changes, you'll need to update the security group rules in AWS Console.

---

## Key Pair

- **File:** medtech-key-luke.pem
- **Purpose:** Authentication for SSH

---

## Commands (after instance is running)

### Connect via SSH
```powershell
ssh -i ~/.ssh/medtech-key-luke.pem ubuntu@<PUBLIC_IP>
```

### Get public IP
Find in EC2 Console → Instances → Select instance → Public IPv4 address