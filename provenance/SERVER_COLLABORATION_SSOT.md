# Server Collaboration SSOT

**Purpose:** Coordination document between Claude Code instances
**Project:** UHA API Service for api.aybllc.org
**API Server:** 01u.aybllc.org
**Date:** 2025-10-24
**Status:** 🟡 In Progress

---

## Infrastructure

- **API Endpoint:** https://api.aybllc.org/v1
- **API Server:** 01u.aybllc.org (Rocky Linux 10)
- **Desktop/Development:** Current machine (where you're reading this)

---

## Communication Protocol

This file serves as a shared workspace between:
- **Claude Code (Desktop)** - Planning, design, client SDK development (this machine)
- **Claude Code (Server at 01u.aybllc.org)** - Deployment, system configuration, API implementation

**Update this file** after completing tasks or encountering blockers.

---

## Current Status

### Infrastructure
- ✅ Domain: aybllc.org (owned)
- 🟡 DNS: Needs A record: `api.aybllc.org` → server IP
- 🟡 Server: Rocky Linux 10 ready
- 🟡 GitHub Access: Pending setup (see `/got/GITHUB_ACCESS_SETUP.md`)
- ⭕ SSL Certificate: Pending (after DNS)
- ⭕ Firewall: Ports 80/443 need opening

### Code Status
- ✅ Architecture designed (see `/got/UHA_API_SERVICE_SSOT.md`)
- ⭕ FastAPI application: Not yet created
- ⭕ Client SDK: Not yet created
- ⭕ Deployment scripts: Not yet created

### Repositories
- ✅ `aybllc/uha-blackbox` - Exists (blackbox build system)
- ⭕ `aybllc/uha-api-service` - Needs creation (private)
- ⭕ `aybllc/uha-client` - Needs creation (public)

**Legend:**
- ✅ Complete
- 🟡 In Progress
- ⭕ Not Started
- ❌ Blocked

---

## Server Claude Code: Your Tasks

### Phase 1: Environment Setup

#### Task 1.1: Configure GitHub Access
**Status:** ⭕ Not Started
**File:** `/got/GITHUB_ACCESS_SETUP.md`

```bash
# Follow guide to set up gh CLI
# When complete, verify:
gh auth status
gh repo list aybllc
```

**Completion criteria:**
- [ ] `gh auth status` shows "Logged in"
- [ ] Can view `aybllc/uha-blackbox` repo
- [ ] Git identity configured

**Update here when done:**
```
Status: [PENDING|COMPLETE|BLOCKED]
Date completed: YYYY-MM-DD HH:MM
Notes: <any issues or notes>
```

---

#### Task 1.2: Install System Dependencies
**Status:** ⭕ Not Started

```bash
# Update system
sudo dnf update -y

# Install core dependencies
sudo dnf install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    sqlite

# Verify installations
python3.11 --version
nginx -v
certbot --version
```

**Completion criteria:**
- [ ] Python 3.11+ installed
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] All commands exit successfully

**Update here when done:**
```
Status: [PENDING|COMPLETE|BLOCKED]
Python version: X.Y.Z
Nginx version: X.Y.Z
Notes: <any issues>
```

---

#### Task 1.3: Get Server IP Address
**Status:** ⭕ Not Started

```bash
# Get public IP
curl -4 ifconfig.me

# Or if that doesn't work:
curl -4 icanhazip.com
```

**Report back:**
```
Server Public IP: XXX.XXX.XXX.XXX
IPv6 (if available): XXXX:XXXX:...
```

---

### Phase 2: DNS & SSL Setup

#### Task 2.1: Wait for DNS Configuration
**Status:** ⭕ Not Started
**Blocker:** User needs to add DNS A record

**Required DNS records:**
```
Domain: aybllc.org

Record 1 (API endpoint):
Type: A
Name: api
Value: <IP of 01u.aybllc.org>
TTL: 300

Record 2 (Server hostname - if not already set):
Type: A
Name: 01u
Value: <server-public-ip>
TTL: 300
```

**To check if DNS is ready:**
```bash
# Check if DNS is propagated
dig api.aybllc.org +short
# Should return 01u.aybllc.org's IP

dig 01u.aybllc.org +short
# Should return server IP

# Or:
nslookup api.aybllc.org
nslookup 01u.aybllc.org
```

**Update here when DNS is ready:**
```
Status: [WAITING|READY]
DNS resolves to: XXX.XXX.XXX.XXX
Date ready: YYYY-MM-DD HH:MM
```

---

#### Task 2.2: Configure Firewall
**Status:** ⭕ Not Started

```bash
# Check current firewall status
sudo firewall-cmd --list-all

# Open HTTP (80) and HTTPS (443)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-services
```

**Completion criteria:**
- [ ] Port 80 open
- [ ] Port 443 open
- [ ] Services persistent (--permanent)

**Update here when done:**
```
Status: [PENDING|COMPLETE|BLOCKED]
Open ports: <list>
```

---

### Phase 3: Application Deployment

#### Task 3.1: Create Application Directory
**Status:** ⭕ Not Started

```bash
# Create service user
sudo useradd -r -s /bin/false uha-api

# Create directory structure
sudo mkdir -p /opt/uha-api/{app,client,tests,deploy,data,logs}

# Set ownership
sudo chown -R uha-api:uha-api /opt/uha-api

# Allow current user to work in directory (optional)
sudo usermod -a -G uha-api $USER
```

**Completion criteria:**
- [ ] User `uha-api` created
- [ ] Directory `/opt/uha-api` exists
- [ ] Correct permissions set

---

#### Task 3.2: Wait for Application Code
**Status:** ⭕ Not Started
**Blocker:** Desktop Claude Code will provide code

Desktop Claude Code will create:
- `/opt/uha-api/app/` - FastAPI application
- `/opt/uha-api/deploy/` - systemd service, nginx config, gunicorn config
- `/opt/uha-api/requirements.txt` - Python dependencies

**When code is ready, you'll receive notification here.**

**Installation steps will be:**
```bash
cd /opt/uha-api
pip3.11 install -r requirements.txt
sudo systemctl daemon-reload
sudo systemctl enable uha-api
sudo systemctl start uha-api
```

---

### Phase 4: Nginx & SSL Configuration

#### Task 4.1: Configure Nginx
**Status:** ⭕ Not Started
**Blocker:** Needs application code and DNS

```bash
# Nginx config will be provided at:
# /opt/uha-api/deploy/nginx.conf

# Copy to Nginx config directory
sudo cp /opt/uha-api/deploy/nginx.conf /etc/nginx/conf.d/uha-api.conf

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

#### Task 4.2: Obtain SSL Certificate
**Status:** ⭕ Not Started
**Requires:** DNS configured, Nginx running, ports 80/443 open

```bash
# Obtain Let's Encrypt certificate
sudo certbot --nginx -d api.aybllc.org

# Verify auto-renewal works
sudo certbot renew --dry-run
```

**Update when complete:**
```
Status: [PENDING|COMPLETE|BLOCKED]
Certificate issued: [YES|NO]
Expiry date: YYYY-MM-DD
```

---

## Desktop Claude Code: Your Tasks

### Phase 1: Code Development

#### Task 1.1: Create FastAPI Application
**Status:** ⭕ Not Started
**Target:** `/opt/uha-api/app/`

**Files to create:**
- `main.py` - FastAPI app entry point
- `auth.py` - API key authentication
- `merge.py` - UHA merge endpoint (with placeholder)
- `models.py` - Pydantic models
- `database.py` - SQLite setup and queries
- `config.py` - Configuration management
- `__init__.py` - Package init

**When complete, update:**
```
Status: [PENDING|COMPLETE]
Commit: <git commit hash>
Location: <path or repo URL>
```

---

#### Task 1.2: Create Deployment Configs
**Status:** ⭕ Not Started
**Target:** `/opt/uha-api/deploy/`

**Files to create:**
- `nginx.conf` - Nginx reverse proxy config
- `uha-api.service` - systemd unit file
- `gunicorn.conf.py` - Gunicorn configuration

---

#### Task 1.3: Create Client SDK
**Status:** ⭕ Not Started
**Target:** `/opt/uha-api/client/` or separate repo

**Files to create:**
- `uha_client/client.py` - Main client class
- `uha_client/models.py` - Response models
- `uha_client/__init__.py` - Package exports
- `setup.py` - Package configuration
- `README.md` - Usage documentation

---

### Phase 2: Testing & Documentation

#### Task 2.1: Create Tests
**Status:** ⭕ Not Started

- Unit tests for API endpoints
- Integration tests
- Client SDK tests

#### Task 2.2: Write Documentation
**Status:** ⭕ Not Started

- API documentation (OpenAPI/Swagger auto-generated)
- Client SDK usage guide
- Deployment guide

---

## Blockers & Issues

### Current Blockers

| ID | Issue | Blocking | Owner | Status |
|----|-------|----------|-------|--------|
| B001 | DNS A record not configured | Phase 2 | User | Open |
| B002 | GitHub access not set up | All git operations | Server Claude | Open |
| B003 | Application code not written | Phase 3 | Desktop Claude | Open |

**Add new blockers here:**
```
[BXXX] Description of blocker
Blocking: <what tasks>
Status: [OPEN|RESOLVED]
Resolution: <how it was resolved>
```

---

## Communication Log

### 2025-10-24 (Initial Setup)

**Desktop Claude:**
- ✅ Created UHA_API_SERVICE_SSOT.md with full architecture
- ✅ Updated for api.aybllc.org domain
- ✅ Created GITHUB_ACCESS_SETUP.md
- ✅ Created this collaboration SSOT
- 🟡 Awaiting server setup completion

**Server Claude:**
- Status: Not yet started
- Next action: Review this SSOT and begin Phase 1

**User:**
- Needs to: Add DNS A record for api.aybllc.org
- Domain: aybllc.org already owned

---

### [Add new log entries here]

**YYYY-MM-DD HH:MM - [Desktop|Server] Claude:**
```
- Completed: <task>
- Status: <current state>
- Next: <next action>
- Notes: <any relevant info>
```

---

## Handoff Checklist

### Server → Desktop
When server Claude needs input:
- [ ] Update "Status" fields above
- [ ] Document any errors/issues encountered
- [ ] List blockers in Blockers section
- [ ] Add entry to Communication Log
- [ ] Notify via this file

### Desktop → Server
When desktop Claude provides code:
- [ ] Push code to appropriate location
- [ ] Update task status
- [ ] Provide installation commands
- [ ] Document any special requirements
- [ ] Add entry to Communication Log

---

## Quick Reference

### Key Files
- `/got/UHA_API_SERVICE_SSOT.md` - Main architecture & API spec
- `/got/GITHUB_ACCESS_SETUP.md` - GitHub setup guide
- `/got/SERVER_COLLABORATION_SSOT.md` - This file

### Key URLs
- API Endpoint: https://api.aybllc.org/v1
- GitHub Org: https://github.com/aybllc
- Domain: aybllc.org

### Key Directories
- Application: `/opt/uha-api/`
- Logs: `/opt/uha-api/logs/`
- Database: `/opt/uha-api/data/uha_api.db`
- Nginx Config: `/etc/nginx/conf.d/uha-api.conf`
- Systemd Unit: `/etc/systemd/system/uha-api.service`

### Key Commands
```bash
# Check service status
sudo systemctl status uha-api

# View logs
sudo journalctl -u uha-api -f

# Restart service
sudo systemctl restart uha-api

# Check API health
curl https://api.aybllc.org/v1/health

# View nginx logs
sudo tail -f /var/log/nginx/access.log
```

---

## Success Criteria

Project is complete when:
- ✅ DNS resolves api.aybllc.org to server
- ✅ SSL certificate installed and working
- ✅ API responds at https://api.aybllc.org/v1/health
- ✅ API key authentication working
- ✅ /merge endpoint functional (with placeholder logic)
- ✅ Rate limiting active
- ✅ Request logging operational
- ✅ Client SDK published and usable
- ✅ Documentation complete

---

**Status:** 🟡 Waiting for server setup
**Next Action:** Server Claude to begin Phase 1, Task 1.1
**Last Updated:** 2025-10-24
**Maintained by:** Both Claude Code instances
