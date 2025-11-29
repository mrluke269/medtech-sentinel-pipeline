# EC2 Instance Setup

## Instance Configuration

| Setting | Value |
|---------|-------|
| Name | MedTech-Airflow-Host |
| AMI | Ubuntu Server 24.04 LTS |
| Instance type | t3.micro (free tier) |
| Key pair | medtech-key-luke (RSA, .pem) |
| Region | us-east-2 (Ohio) |

---

## Network Concepts Explained

### VPC (Virtual Private Cloud)
Your own private network inside AWS. Think of it like your house's internal network - devices inside can talk to each other, and you control what gets in or out. AWS gives you a default VPC so you don't have to build one from scratch.

### Subnet
A subdivision of your VPC. Like rooms in your house. Your EC2 instance lives in one subnet. "No preference" means AWS picks one for you.

### Auto-assign public IP
Your EC2 instance needs a public IP address so you can reach it from your home computer over the internet. Without this, the instance would only have a private IP and you couldn't SSH into it.

### Security Group
The firewall for your EC2 instance. Controls what traffic is allowed in (inbound) and out (outbound). By default, **everything inbound is blocked** - you must explicitly open ports.

---

## Security Group Configuration

**Name:** medtech-airflow-sg

### Inbound Rules

| Port | Type | Source | Purpose |
|------|------|--------|---------|
| 22 | SSH | My IP | Terminal access to server |
| 8080 | Custom TCP | My IP | Airflow web UI |

### Why "My IP" instead of "Anywhere"?
Restricting to your IP address means only your computer can connect. Much safer than opening to the entire internet (0.0.0.0/0).

**Note:** If your home IP changes, you'll need to update the security group rules in AWS Console.

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