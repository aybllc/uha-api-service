# UHA API Service - Single Source of Truth

**Version:** 1.0.0
**Date:** 2025-10-24
**Organization:** All Your Baseline LLC (Research Organization)
**Purpose:** Hosted API service for secure access to UHA merge functionality
**Patent:** US 63/902,536
**Domain:** api.aybllc.org
**Type:** Research organization (.org) with selective commercial licensing

---

## Architecture Overview

```
┌─────────────────┐
│   Researcher    │
│   (Client SDK)  │
└────────┬────────┘
         │ HTTPS + API Key
         ▼
┌─────────────────────────────────┐
│  Nginx Reverse Proxy            │
│  - SSL/TLS Termination          │
│  - Rate Limiting (IP-based)     │
│  - Request Logging              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  FastAPI Application             │
│  - API Key Validation           │
│  - Request Authentication       │
│  - Usage Tracking               │
│  - Rate Limiting (Key-based)    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  UHA Merge Engine               │
│  - Proprietary Implementation   │
│  - Binary-only (No source)      │
│  - Patent Protected             │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Response + Usage Log           │
└─────────────────────────────────┘
```

---

## System Requirements

### Server Specifications
- **OS:** Rocky Linux 10
- **CPU:** 4+ cores (8+ recommended for production)
- **RAM:** 8GB minimum (16GB+ recommended)
- **Storage:** 50GB+ SSD
- **Network:** Static IP with public access
- **Python:** 3.11 or 3.12

### Software Stack
- **Web Framework:** FastAPI 0.104+
- **ASGI Server:** Uvicorn with Gunicorn
- **Reverse Proxy:** Nginx 1.24+
- **SSL:** Let's Encrypt (certbot)
- **Database:** SQLite (for API keys & logs) or PostgreSQL (production)
- **Process Manager:** systemd

---

## API Endpoints Specification

### Base URL
```
Production: https://api.aybllc.org/v1
Development: http://localhost:8000/v1
```

### Authentication
All requests require header:
```
X-API-Key: <researcher-api-key>
```

### Endpoints

#### 1. Health Check
```
GET /v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-24T14:30:00Z"
}
```

---

#### 2. Merge Datasets (Primary Endpoint)
```
POST /v1/merge
Content-Type: application/json
X-API-Key: <key>
```

**Request Body:**
```json
{
  "datasets": {
    "planck": {
      "H0": 67.4,
      "Omega_m": 0.315,
      "Omega_Lambda": 0.685,
      "sigma": {
        "H0": 0.5,
        "Omega_m": 0.007
      }
    },
    "shoes": {
      "H0": 73.04,
      "sigma_H0": 1.04
    }
  },
  "options": {
    "coordinate_system": "ICRS2016",
    "epoch": "J2000.0",
    "validate_only": false
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "result": {
    "merged_H0": 69.8,
    "uncertainty": 0.8,
    "chi_squared": 1.2,
    "p_value": 0.27,
    "method": "UHA",
    "coordinate_encoding": true
  },
  "metadata": {
    "request_id": "req_abc123xyz",
    "timestamp": "2025-10-24T14:30:00Z",
    "processing_time_ms": 45
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Dataset 'planck' missing required field 'H0'",
    "details": {}
  },
  "metadata": {
    "request_id": "req_abc123xyz",
    "timestamp": "2025-10-24T14:30:00Z"
  }
}
```

---

#### 3. Validate Input
```
POST /v1/validate
Content-Type: application/json
X-API-Key: <key>
```

**Request Body:** Same as `/merge`

**Response:**
```json
{
  "valid": true,
  "warnings": [],
  "suggestions": []
}
```

---

#### 4. API Key Info
```
GET /v1/key/info
X-API-Key: <key>
```

**Response:**
```json
{
  "key_id": "key_researcher_001",
  "owner": "Jane Doe",
  "institution": "MIT",
  "created": "2025-10-01T00:00:00Z",
  "expires": "2026-10-01T00:00:00Z",
  "usage": {
    "requests_today": 45,
    "requests_month": 1250,
    "limit_daily": 1000,
    "limit_monthly": 50000
  },
  "rate_limit": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000
  }
}
```

---

## API Key Management

### Key Format
```
Format: uha_live_<32-char-hex>
Example: uha_live_a1b2c3d4e5f6789012345678901234ab
```

### Key Storage (SQLite Schema)
```sql
CREATE TABLE api_keys (
    key_id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,  -- bcrypt hash
    owner_name TEXT NOT NULL,
    owner_email TEXT NOT NULL,
    institution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    daily_limit INTEGER DEFAULT 1000,
    monthly_limit INTEGER DEFAULT 50000,
    notes TEXT
);

CREATE TABLE request_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT,
    endpoint TEXT,
    method TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    status_code INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    FOREIGN KEY (key_id) REFERENCES api_keys(key_id)
);

CREATE INDEX idx_logs_key_timestamp ON request_logs(key_id, timestamp);
CREATE INDEX idx_logs_timestamp ON request_logs(timestamp);
```

---

## Rate Limiting Strategy

### Layer 1: Nginx (IP-based)
```nginx
limit_req_zone $binary_remote_addr zone=api_ip:10m rate=100r/m;
limit_req zone=api_ip burst=20 nodelay;
```

### Layer 2: FastAPI (API Key-based)
- **Per-minute:** 60 requests
- **Per-hour:** 1000 requests
- **Per-day:** 10000 requests (configurable per key)
- **Per-month:** 50000 requests (configurable per key)

---

## Security Features

### 1. API Key Security
- Keys stored as bcrypt hashes (never plaintext)
- Keys transmitted only via HTTPS headers
- Keys can be revoked instantly
- Automatic expiration support

### 2. Request Validation
- JSON schema validation on all inputs
- Size limits: 1MB max request body
- Timeout: 30 seconds max processing time

### 3. Logging & Monitoring
- All requests logged with timestamps
- Failed authentication attempts tracked
- Suspicious activity alerts (100+ failed auths in 1 hour)

### 4. DDoS Protection
- Nginx rate limiting
- Application-level rate limiting
- IP blocking for abuse

---

## Deployment Architecture

### Directory Structure
```
/opt/uha-api/
├── app/
│   ├── main.py              # FastAPI app
│   ├── auth.py              # API key auth
│   ├── merge.py             # UHA merge wrapper
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLite/Postgres
│   └── config.py            # Configuration
├── client/
│   ├── uha_client/          # Python client SDK
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── models.py
│   └── setup.py
├── tests/
│   ├── test_api.py
│   └── test_auth.py
├── deploy/
│   ├── nginx.conf
│   ├── uha-api.service      # systemd unit
│   └── gunicorn.conf.py
├── data/
│   └── uha_api.db           # SQLite database
├── logs/
│   ├── api.log
│   └── nginx_access.log
├── requirements.txt
└── README.md
```

---

## Installation Steps

### 1. System Preparation
```bash
# Update system
sudo dnf update -y

# Install dependencies
sudo dnf install -y python3.11 python3.11-pip nginx certbot python3-certbot-nginx

# Install Python packages
pip3.11 install fastapi uvicorn gunicorn slowapi pydantic bcrypt python-jose python-multipart
```

### 2. Create Service User
```bash
sudo useradd -r -s /bin/false uha-api
sudo mkdir -p /opt/uha-api/{app,data,logs}
sudo chown -R uha-api:uha-api /opt/uha-api
```

### 3. Deploy Application
```bash
# Copy application files to /opt/uha-api/app/
# Set permissions
sudo chmod 750 /opt/uha-api/app
sudo chmod 640 /opt/uha-api/app/*.py
```

### 4. Configure systemd Service
```ini
# /etc/systemd/system/uha-api.service
[Unit]
Description=UHA API Service
After=network.target

[Service]
Type=notify
User=uha-api
Group=uha-api
WorkingDirectory=/opt/uha-api
Environment="PATH=/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/gunicorn -c /opt/uha-api/deploy/gunicorn.conf.py app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Configure Nginx
```nginx
# /etc/nginx/conf.d/uha-api.conf
upstream uha_api {
    server 127.0.0.1:8000;
}

limit_req_zone $binary_remote_addr zone=api_ip:10m rate=100r/m;

server {
    listen 80;
    server_name api.aybllc.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.aybllc.org;

    ssl_certificate /etc/letsencrypt/live/api.aybllc.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.aybllc.org/privkey.pem;

    client_max_body_size 1M;

    location / {
        limit_req zone=api_ip burst=20 nodelay;

        proxy_pass http://uha_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

### 6. SSL Setup
```bash
sudo certbot --nginx -d api.aybllc.org
```

### 7. Firewall Configuration
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 8. Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable uha-api nginx
sudo systemctl start uha-api nginx
```

---

## Client SDK (Python)

### Installation
```bash
pip install uha-client
```

### Usage
```python
from uha_client import UHAClient

# Initialize client
client = UHAClient(
    api_key="uha_live_a1b2c3d4e5f6789012345678901234ab",
    base_url="https://api.aybllc.org/v1"
)

# Merge datasets
result = client.merge(
    datasets={
        "planck": {
            "H0": 67.4,
            "Omega_m": 0.315,
            "Omega_Lambda": 0.685,
            "sigma": {"H0": 0.5, "Omega_m": 0.007}
        },
        "shoes": {
            "H0": 73.04,
            "sigma_H0": 1.04
        }
    }
)

print(f"Merged H0: {result.merged_H0} ± {result.uncertainty}")
print(f"Chi-squared: {result.chi_squared}")
print(f"p-value: {result.p_value}")

# Check API key status
info = client.key_info()
print(f"Requests today: {info.usage.requests_today}/{info.usage.limit_daily}")
```

---

## Domain Setup Checklist

### DNS Configuration
Set up the following DNS records:

```
Type    Name    Value                       TTL
A       api     <your-server-ip>            300
AAAA    api     <your-server-ipv6>          300  (if available)
```

### Domain Registrar Settings
- Enable DNSSEC (recommended)
- Disable domain auto-renewal grace period (prevent hijacking)
- Enable registry lock (for .org domains)

---

## Monitoring & Maintenance

### Health Checks
```bash
# Check API status
curl -f https://api.aybllc.org/v1/health || alert

# Check SSL expiry
echo | openssl s_client -connect api.aybllc.org:443 2>/dev/null | openssl x509 -noout -dates
```

### Log Rotation
```bash
# /etc/logrotate.d/uha-api
/opt/uha-api/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 uha-api uha-api
    sharedscripts
    postrotate
        systemctl reload uha-api
    endscript
}
```

### Database Maintenance
```sql
-- Archive old logs (keep 90 days)
DELETE FROM request_logs WHERE timestamp < datetime('now', '-90 days');

-- Vacuum database
VACUUM;
```

---

## Security Incident Response

### Compromised API Key
```bash
# Deactivate key immediately
sqlite3 /opt/uha-api/data/uha_api.db "UPDATE api_keys SET is_active=0 WHERE key_id='key_researcher_001';"

# Review logs for suspicious activity
sqlite3 /opt/uha-api/data/uha_api.db "SELECT * FROM request_logs WHERE key_id='key_researcher_001' ORDER BY timestamp DESC LIMIT 100;"
```

### DDoS Attack
```bash
# Block IP at Nginx level
echo "deny <attacker-ip>;" >> /etc/nginx/conf.d/blocked-ips.conf
nginx -s reload

# Rate limit more aggressively
# Edit /etc/nginx/conf.d/uha-api.conf and reduce rate
```

---

## Costs & Scaling

### Estimated Costs (Monthly)
- **VPS:** $10-40 (DigitalOcean, Linode, Vultr)
- **Domain:** $1-2/month (.org TLD)
- **SSL:** $0 (Let's Encrypt)
- **Total:** ~$15-50/month

### Scaling Strategy
- **< 1000 req/day:** Single server sufficient
- **1000-10000 req/day:** Add Redis caching
- **10000+ req/day:** Load balancer + multiple app servers
- **100000+ req/day:** Consider CDN + database replication

---

## Support & Documentation

### For Researchers
- API Documentation: https://docs.aybllc.org
- Client SDK: https://github.com/aybllc/uha-client
- Support Email: support@aybllc.org

### Citation
```
@software{uha_api_2025,
  title = {Universal Hierarchical Aggregation (UHA) API},
  author = {All Your Baseline LLC},
  year = {2025},
  patent = {US 63/902,536},
  url = {https://api.aybllc.org}
}
```

---

## Implementation Timeline

| Task | Duration | Owner |
|------|----------|-------|
| Domain registration & DNS | 1 hour | You |
| VPS setup + OS install | 2 hours | You |
| Application development | 8 hours | Claude Code |
| SSL + Nginx configuration | 1 hour | Both |
| API key generation system | 2 hours | Claude Code |
| Client SDK development | 4 hours | Claude Code |
| Testing & validation | 4 hours | Both |
| Documentation | 2 hours | Claude Code |
| **Total** | **24 hours** | |

---

## Next Steps

### Your Tasks:
1. Add DNS A record for aybllc.org: api → server IP
2. Ensure ports 80/443 are publicly accessible
3. Verify DNS propagation (may take 5-60 minutes)
4. Ready to run deployment commands on Rocky Linux 10 server

### Claude Code Tasks:
1. Build FastAPI application
2. Implement authentication & rate limiting
3. Create database schema & management
4. Build Python client SDK
5. Write deployment scripts
6. Generate API documentation

---

**Status:** Ready to build
**Contact:** All Your Baseline LLC
**Last Updated:** 2025-10-24
