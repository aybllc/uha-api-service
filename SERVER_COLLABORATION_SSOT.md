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
- ⭕ DNS: Needs A record: `api.aybllc.org` → 146.190.119.6
- ✅ Server: Rocky Linux 10 - Setup complete (pending reboot)
- ✅ GitHub Access: Complete - authenticated as abba-01
- ⭕ SSL Certificate: Pending (after DNS)
- ✅ Firewall: Ports 80/443/22 open

### Server Setup (Phase 1-9 Complete)
- ✅ Python 3.12.9 installed (newer than required 3.11)
- ✅ Nginx 1.26.3 installed
- ✅ Certbot 4.2.0 installed
- ✅ SQLite 3.46.1 installed
- ✅ GitHub CLI 2.82.1 authenticated
- ✅ FastAPI 0.104.1 + all Python packages installed
- ✅ Firewall configured (http/https/ssh)
- ✅ Service user 'uha-api' created (uid=991)
- ✅ Directory structure created at /opt/uha-api
- ✅ SELinux configured (will be enforcing after reboot)
- ✅ Server IP: 146.190.119.6

### Code Status
- ✅ Architecture designed (see `/got/UHA_API_SERVICE_SSOT.md`)
- ⭕ FastAPI application: Not yet created
- ⭕ Client SDK: Not yet created
- ⭕ Deployment scripts: Not yet created

### Repositories
- ✅ `aybllc/uha-blackbox` - Exists (blackbox build system)
- ✅ `aybllc/uha-api-service` - Exists (private, access verified)
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
**Status:** ✅ COMPLETE
**File:** `/got/GITHUB_ACCESS_SETUP.md`

```bash
# Follow guide to set up gh CLI
# When complete, verify:
gh auth status
gh repo list aybllc
```

**Completion criteria:**
- [x] `gh auth status` shows "Logged in"
- [x] Can view `aybllc/uha-blackbox` repo
- [x] Git identity configured

**Update here when done:**
```
Status: COMPLETE
Date completed: 2025-10-24 17:02 UTC
Account: abba-01
Git identity: UHA API Server <server@aybllc.org>
Notes: GitHub CLI already authenticated. Access to aybllc/uha-api-service verified.
```

---

#### Task 1.2: Install System Dependencies
**Status:** ✅ COMPLETE

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
- [x] Python 3.11+ installed
- [x] Nginx installed
- [x] Certbot installed
- [x] All commands exit successfully

**Update here when done:**
```
Status: COMPLETE
Date completed: 2025-10-24 17:00 UTC
Python version: 3.12.9 (newer than required 3.11)
Nginx version: 1.26.3
Certbot version: 4.2.0
SQLite version: 3.46.1
Notes: System fully updated. All packages installed successfully. Python 3.12 is default on Rocky Linux 10.
```

---

#### Task 1.3: Get Server IP Address
**Status:** ✅ COMPLETE

```bash
# Get public IP
curl -4 ifconfig.me

# Or if that doesn't work:
curl -4 icanhazip.com
```

**Report back:**
```
Server Public IP: 146.190.119.6
Local IPs: 146.190.119.6, 10.48.0.7, 10.124.0.8
IPv6: Not configured
Date: 2025-10-24 17:03 UTC
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
**Status:** ✅ COMPLETE

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
- [x] Port 80 open
- [x] Port 443 open
- [x] Services persistent (--permanent)

**Update here when done:**
```
Status: COMPLETE
Date completed: 2025-10-24 17:01 UTC
Open services: cockpit dhcpv6-client http https ssh
Notes: Firewalld installed and configured. All required ports open.
```

---

### Phase 3: Application Deployment

#### Task 3.1: Create Application Directory
**Status:** ✅ COMPLETE

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
- [x] User `uha-api` created
- [x] Directory `/opt/uha-api` exists
- [x] Correct permissions set

**Update:**
```
Status: COMPLETE
Date completed: 2025-10-24 17:01 UTC
User ID: 991 (uha-api)
Directory: /opt/uha-api (drwxr-x---)
Subdirectories: app, client, tests, deploy, data (770), logs (770)
SELinux contexts: Set for httpd operation
Notes: All directory structure created with proper permissions and SELinux contexts.
```

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
| B001 | DNS A record not configured | SSL certificate, deployment | User | Open |
| B002 | GitHub access not set up | All git operations | Server Claude | ✅ RESOLVED |
| B003 | Application code not written | Phase 3-4 | Desktop Claude | Open |

**Resolved Blockers:**
- B002: Resolved 2025-10-24 17:02 UTC - GitHub CLI authenticated as abba-01 with access to aybllc repos

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
- ⭕ Next: Create FastAPI application code

**Server Claude (17:00-17:03 UTC):**
- ✅ Completed full 10-phase server setup (Phases 1-9)
- ✅ Phase 1: System preparation complete
- ✅ Phase 2: All dependencies installed (Python 3.12.9, Nginx 1.26.3, Certbot 4.2.0, SQLite 3.46.1)
- ✅ Phase 3: Python packages installed (FastAPI, Uvicorn, etc.)
- ✅ Phase 4: Firewall configured (ports 80/443/22)
- ✅ Phase 5: Service user and directories created
- ✅ Phase 6: SELinux configured (enforcing mode, will activate after reboot)
- ✅ Phase 7: GitHub authentication verified
- ✅ Phase 8: Network verified (Public IP: 146.190.119.6)
- ✅ Phase 9: All systems verified
- 🟡 Phase 10: Pending - Reboot required to enable SELinux
- ⏸️ Next: Wait for application code from Desktop Claude, then reboot

**User:**
- ⭕ Action required: Add DNS A record for api.aybllc.org → 146.190.119.6
- ⭕ Action required: Add DNS A record for 01u.aybllc.org → 146.190.119.6 (optional)
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
