# UHA API Service

**Organization:** All Your Baseline LLC
**Domain:** api.aybllc.org
**Server:** 01u.aybllc.org
**Patent:** US 63/902,536

---

## Overview

Hosted API service for secure access to Universal Hierarchical Aggregation (UHA) merge functionality. This is a research organization's API for processing cosmological dataset mergers.

## Quick Start for Server Setup

**On 01u.aybllc.org, run:**

```bash
# Clone this repo
git clone https://github.com/aybllc/uha-api-service.git
cd uha-api-service

# Read setup instructions
cat 01U_SERVER_SETUP_GUIDE.md

# Or view in your editor
```

## Documentation Files

### For Server Administrator (01u.aybllc.org)
1. **[01U_SERVER_SETUP_GUIDE.md](01U_SERVER_SETUP_GUIDE.md)** - Complete dependency installation
   - Python 3.11 + FastAPI
   - Nginx + SSL
   - SELinux configuration
   - ~30-40 minutes

2. **[GITHUB_ACCESS_SETUP.md](GITHUB_ACCESS_SETUP.md)** - GitHub authentication
   - gh CLI setup
   - SSH keys
   - Token management

3. **[DNS_NAMESERVER_SETUP.md](DNS_NAMESERVER_SETUP.md)** - DNS configuration
   - Quick registrar setup
   - OR full nameserver setup

4. **[SERVER_COLLABORATION_SSOT.md](SERVER_COLLABORATION_SSOT.md)** - Task coordination
   - Communication protocol
   - Status tracking
   - Blocker reporting

### For Researchers
5. **[UHA_API_SERVICE_SSOT.md](UHA_API_SERVICE_SSOT.md)** - API specification
   - Endpoints
   - Authentication
   - Rate limiting
   - Client SDK usage

## Architecture

```
api.aybllc.org (HTTPS)
       ↓
01u.aybllc.org (Server)
       ↓
Nginx → FastAPI → UHA Engine
```

## Installation Timeline

1. **Server Setup** (30-40 min) - Follow 01U_SERVER_SETUP_GUIDE.md
2. **DNS Configuration** (10 min) - Follow DNS_NAMESERVER_SETUP.md
3. **Application Deploy** (20 min) - Automated via scripts
4. **SSL Certificate** (5 min) - Automated via Certbot
5. **Testing** (10 min) - Verify endpoints

**Total:** ~1.5-2 hours

---

## Deployment Instructions

### Prerequisites
✅ Server setup complete (01U_SERVER_SETUP_GUIDE.md followed)
✅ DNS configured (api.aybllc.org points to server)
✅ Ports 80/443 open

### Quick Deploy

```bash
# On 01u.aybllc.org, as root:
cd /opt
sudo ./uha-api-service/deploy/deploy.sh
```

This script will:
1. Clone/update repository to `/opt/uha-api`
2. Install Python dependencies
3. Initialize database
4. Install systemd service
5. Configure Nginx
6. Start services

### SSL Certificate

```bash
# Obtain Let's Encrypt certificate
sudo certbot --nginx -d api.aybllc.org

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Create API Keys

```bash
# Create admin key
cd /opt/uha-api
python3.11 scripts/manage_keys.py admin

# Create researcher key
python3.11 scripts/manage_keys.py create "Jane Doe" jane@mit.edu "MIT"

# List all keys
python3.11 scripts/manage_keys.py list

# View key statistics
python3.11 scripts/manage_keys.py stats key_jane_abc123
```

### Test API

```bash
# Health check (no auth required)
curl https://api.aybllc.org/v1/health

# Test merge endpoint (requires API key)
curl -X POST https://api.aybllc.org/v1/merge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: uha_live_your_key_here" \
  -d '{
    "datasets": {
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
  }'
```

### Monitoring

```bash
# View service status
sudo systemctl status uha-api

# View logs (real-time)
sudo journalctl -u uha-api -f

# View Nginx logs
sudo tail -f /var/log/nginx/uha-api-access.log

# Check API metrics
python3.11 scripts/manage_keys.py stats <key_id>
```

### Troubleshooting

```bash
# Restart service
sudo systemctl restart uha-api

# Check service errors
sudo journalctl -u uha-api -n 50 --no-pager

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check SELinux denials
sudo ausearch -m avc -ts recent | grep uha
```

## Status

- [x] Documentation complete
- [x] Architecture designed
- [ ] Dependencies installed on 01u
- [ ] DNS configured
- [ ] Application deployed
- [ ] SSL certificate obtained
- [ ] API live

## Support

- **Support:** support@aybllc.org
- **Issues:** Create issue in this repo
- **Docs:** See markdown files in this repo

## License

Proprietary - All Your Baseline LLC
Patent: US 63/902,536

---

**Last Updated:** 2025-10-24
