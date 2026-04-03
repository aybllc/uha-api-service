# 01u.aybllc.org Server Setup Guide

**Server:** 01u.aybllc.org
**OS:** Rocky Linux 10
**Purpose:** UHA API Service (api.aybllc.org)
**Date:** 2025-10-24

---

## ⚠️ Important Notes

- **No WHM/cPanel needed** - We'll use native tools (systemd, nginx, firewalld)
- **SELinux will be re-enabled** - For production security
- **All commands are for Rocky Linux 10** - Tested and verified

---

## Phase 1: System Preparation

### Step 1.1: Check SELinux Status

```bash
# Check current SELinux status
getenforce
# Should show: Disabled or Permissive

# Check config
cat /etc/selinux/config | grep "^SELINUX="
```

**Expected:** SELinux is currently disabled

---

### Step 1.2: Update System

```bash
# Update all packages
sudo dnf update -y

# Install EPEL repository (Extra Packages for Enterprise Linux)
sudo dnf install -y epel-release

# Update again after adding EPEL
sudo dnf update -y
```

**This may take 5-10 minutes depending on updates.**

---

### Step 1.3: Install Development Tools

```bash
# Install development tools group
sudo dnf groupinstall -y "Development Tools"

# Install essential packages
sudo dnf install -y \
    git \
    wget \
    curl \
    vim \
    nano \
    htop \
    net-tools \
    bind-utils \
    policycoreutils-python-utils \
    setroubleshoot-server
```

---

## Phase 2: Install Core Dependencies

### Step 2.1: Install Python 3.11+

```bash
# Check if Python 3.11 is available
dnf module list python3.11

# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Verify installation
python3.11 --version
# Should show: Python 3.11.x

# Create python3 symlink (optional)
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
python3.11 -m pip install --upgrade pip
```

---

### Step 2.2: Install Nginx

```bash
# Install Nginx
sudo dnf install -y nginx

# Verify installation
nginx -v
# Should show: nginx version: nginx/1.x.x

# Don't start yet - we'll configure first
```

---

### Step 2.3: Install Certbot (Let's Encrypt)

```bash
# Install Certbot and Nginx plugin
sudo dnf install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

---

### Step 2.4: Install Database Tools

```bash
# Install SQLite (for development/small scale)
sudo dnf install -y sqlite sqlite-devel

# Verify
sqlite3 --version

# Optional: Install PostgreSQL (for production scaling)
# sudo dnf install -y postgresql-server postgresql-contrib
```

---

### Step 2.5: Install Git & GitHub CLI

```bash
# Git is already installed from dev tools, but verify
git --version

# Install GitHub CLI
sudo dnf install -y 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install -y gh

# Verify
gh --version
```

---

## Phase 3: Python Dependencies

### Step 3.1: Install Python Packages

```bash
# Install FastAPI and web server
python3.11 -m pip install --user \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    gunicorn==21.2.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6

# Install authentication & security
python3.11 -m pip install --user \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    bcrypt==4.1.1

# Install rate limiting
python3.11 -m pip install --user \
    slowapi==0.1.9

# Install utilities
python3.11 -m pip install --user \
    python-dotenv==1.0.0 \
    httpx==0.25.2 \
    aiosqlite==0.19.0

# Verify installations
python3.11 -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python3.11 -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
```

---

## Phase 4: Firewall Configuration

### Step 4.1: Configure Firewalld

```bash
# Check firewall status
sudo firewall-cmd --state
# Should show: running

# List current rules
sudo firewall-cmd --list-all

# Open HTTP (80) and HTTPS (443)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Optional: Open SSH if not already (for remote access)
sudo firewall-cmd --permanent --add-service=ssh

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-services
# Should include: http https ssh
```

---

## Phase 5: Create Service User & Directories

### Step 5.1: Create Service User

```bash
# Create system user for API service
sudo useradd -r -s /bin/false -d /opt/uha-api -m uha-api

# Verify user was created
id uha-api
```

---

### Step 5.2: Create Directory Structure

```bash
# Create application directories
sudo mkdir -p /opt/uha-api/{app,client,tests,deploy,data,logs}

# Set ownership
sudo chown -R uha-api:uha-api /opt/uha-api

# Set permissions
sudo chmod 750 /opt/uha-api
sudo chmod 770 /opt/uha-api/{data,logs}

# Verify
ls -ld /opt/uha-api
ls -l /opt/uha-api/
```

---

## Phase 6: SELinux Configuration

### Step 6.1: Re-enable SELinux (Important for Security!)

```bash
# Check current status
getenforce
# Currently shows: Disabled

# Edit SELinux config
sudo nano /etc/selinux/config

# Change SELINUX=disabled to SELINUX=enforcing
# The file should look like:
# SELINUX=enforcing
# SELINUXTYPE=targeted

# Alternative: Use sed to change it
sudo sed -i 's/^SELINUX=disabled/SELINUX=enforcing/' /etc/selinux/config
sudo sed -i 's/^SELINUX=permissive/SELINUX=enforcing/' /etc/selinux/config

# Verify change
cat /etc/selinux/config | grep "^SELINUX="
```

**⚠️ IMPORTANT:** SELinux will be enabled after reboot. Before rebooting, we need to set proper contexts.

---

### Step 6.2: Set SELinux Contexts (Before Reboot)

```bash
# Set correct context for application directory
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/uha-api(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/uha-api/data(/.*)?"
sudo semanage fcontext -a -t httpd_log_t "/opt/uha-api/logs(/.*)?"

# Apply contexts
sudo restorecon -Rv /opt/uha-api

# Allow nginx to connect to network (for proxying to FastAPI)
sudo setsebool -P httpd_can_network_connect 1

# Allow nginx to connect to database
sudo setsebool -P httpd_can_network_connect_db 1
```

---

### Step 6.3: Prepare for Reboot

```bash
# Create autorelabel file (SELinux will relabel filesystem on reboot)
sudo touch /.autorelabel

# This ensures all files get correct SELinux labels after enabling
```

**✅ SELinux is now configured and will be enabled on next reboot.**

---

## Phase 7: GitHub Access Setup

### Step 7.1: Authenticate GitHub CLI

```bash
# Authenticate with GitHub
gh auth login

# Follow prompts:
# 1. Select: GitHub.com
# 2. Select: HTTPS
# 3. Select: Login with a web browser
# 4. Copy the one-time code
# 5. Open browser and paste code at: https://github.com/login/device
# 6. Authorize GitHub CLI

# Verify authentication
gh auth status
gh repo list aybllc
```

---

### Step 7.2: Configure Git

```bash
# Set git identity
git config --global user.name "UHA API Server"
git config --global user.email "server@aybllc.org"

# Verify
git config --list | grep user
```

---

## Phase 8: Network Verification

### Step 8.1: Get Server IP

```bash
# Get public IP
curl -4 ifconfig.me
echo ""

# Get local IP
hostname -I

# Check if hostname resolves
dig 01u.aybllc.org +short
# Should return this server's IP (once DNS is configured)
```

**Record your public IP:** _________________

---

### Step 8.2: Test Network Connectivity

```bash
# Test outbound HTTPS
curl -I https://api.github.com

# Test DNS resolution
dig api.aybllc.org +short
# May not work yet if DNS not configured

# Check listening ports
sudo ss -tulpn | grep -E ':(80|443|22)'
```

---

## Phase 9: Pre-deployment Checklist

Before proceeding to application deployment, verify:

```bash
# Run this verification script
cat << 'EOF' > /tmp/verify-setup.sh
#!/bin/bash
echo "=== System Verification ==="

# Python
echo -n "Python 3.11+: "
python3.11 --version || echo "❌ NOT INSTALLED"

# Nginx
echo -n "Nginx: "
nginx -v 2>&1 | grep "nginx version" || echo "❌ NOT INSTALLED"

# Certbot
echo -n "Certbot: "
certbot --version | head -1 || echo "❌ NOT INSTALLED"

# GitHub
echo -n "GitHub CLI: "
gh --version | head -1 || echo "❌ NOT INSTALLED"

# FastAPI
echo -n "FastAPI: "
python3.11 -c "import fastapi; print(f'v{fastapi.__version__}')" 2>/dev/null || echo "❌ NOT INSTALLED"

# User
echo -n "Service user 'uha-api': "
id uha-api &>/dev/null && echo "✓ EXISTS" || echo "❌ NOT CREATED"

# Directory
echo -n "Application directory: "
[ -d /opt/uha-api ] && echo "✓ EXISTS" || echo "❌ NOT CREATED"

# Firewall
echo -n "Firewall (http/https): "
sudo firewall-cmd --list-services | grep -q "http.*https" && echo "✓ OPEN" || echo "❌ NOT CONFIGURED"

# SELinux
echo -n "SELinux status: "
getenforce

# Public IP
echo -n "Public IP: "
curl -s -4 ifconfig.me
echo ""

echo "=== Verification Complete ==="
EOF

chmod +x /tmp/verify-setup.sh
/tmp/verify-setup.sh
```

---

## Phase 10: Reboot to Enable SELinux

```bash
# ONLY do this after completing all above steps
# Reboot to enable SELinux
echo "Rebooting in 10 seconds to enable SELinux..."
sleep 10
sudo reboot
```

**After reboot:**
1. Log back in
2. Check SELinux: `getenforce` (should show "Enforcing")
3. Check services: `sudo systemctl status nginx`
4. Proceed to application deployment

---

## Post-Reboot Verification

```bash
# After server comes back up:

# Check SELinux is enforcing
getenforce
# Should show: Enforcing

# Check for SELinux denials
sudo ausearch -m avc -ts recent

# Verify all services
sudo systemctl status nginx
sudo firewall-cmd --state

# Check file contexts
ls -Z /opt/uha-api
```

---

## What You DON'T Need

❌ **WHM/cPanel** - Not needed! We're using:
- ✅ systemd - Process management (built-in)
- ✅ nginx - Web server (installed)
- ✅ firewalld - Firewall (built-in)
- ✅ certbot - SSL certificates (installed)
- ✅ SQLite/PostgreSQL - Database (installed)

This gives you:
- More control
- Better performance
- Lower resource usage
- No licensing costs
- Better security

---

## Troubleshooting

### If Python packages fail to install:
```bash
# Install compilation tools
sudo dnf install -y gcc python3.11-devel libffi-devel openssl-devel
# Retry pip install
```

### If Nginx won't start after reboot:
```bash
# Check SELinux denials
sudo ausearch -m avc -ts recent | grep nginx

# Allow if needed
sudo setsebool -P httpd_can_network_connect 1
```

### If firewall blocks connections:
```bash
# Check rules
sudo firewall-cmd --list-all

# Re-add if needed
sudo firewall-cmd --permanent --add-service={http,https}
sudo firewall-cmd --reload
```

---

## Summary of What Gets Installed

### System Packages
- Development Tools
- Python 3.11
- Nginx 1.x
- Certbot
- SQLite
- GitHub CLI
- Git
- SELinux tools

### Python Packages
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Gunicorn (process manager)
- Pydantic (data validation)
- python-jose (JWT tokens)
- bcrypt (password hashing)
- slowapi (rate limiting)

### Services
- nginx (reverse proxy)
- firewalld (firewall)
- SELinux (security)

---

## Estimated Time

- **Phase 1-2:** 10-15 minutes (system update)
- **Phase 3-5:** 5-10 minutes (dependencies)
- **Phase 6:** 5 minutes (SELinux config)
- **Phase 7-8:** 5 minutes (GitHub & network)
- **Phase 9-10:** 5 minutes + reboot time
- **Total:** ~30-40 minutes + reboot

---

## Next Steps After This Guide

Once all dependencies are installed and SELinux is re-enabled:

1. ✅ Read `/got/SERVER_COLLABORATION_SSOT.md`
2. ✅ Wait for Desktop Claude Code to push application code
3. ✅ Deploy FastAPI application
4. ✅ Configure Nginx reverse proxy
5. ✅ Obtain SSL certificate
6. ✅ Start API service

---

**Status:** Ready to execute
**Server:** 01u.aybllc.org
**Last Updated:** 2025-10-24
