# DNS Nameserver Setup for aybllc.org

**Domain:** aybllc.org
**Server:** 01u.aybllc.org
**Nameservers:** ns1.aybllc.org, ns2.aybllc.org
**Date:** 2025-10-24

---

## Overview

You have two options for DNS:

1. **Option A:** Use your domain registrar's DNS (easiest)
2. **Option B:** Run your own DNS server on 01u.aybllc.org (advanced)

---

## Option A: Use Registrar DNS (Recommended for Start)

### Step 1: Get Server IP

On 01u.aybllc.org:
```bash
# Get public IP address
curl -4 ifconfig.me
```

**Server IP:** _________________ (write this down)

---

### Step 2: Configure DNS at Registrar

Log into your domain registrar (where you bought aybllc.org) and add these A records:

```
Host/Name        Type    Value (Points To)           TTL
---------------------------------------------------------
@                A       <01u-server-ip>             300
01u              A       <01u-server-ip>             300
api              A       <01u-server-ip>             300
www              A       <01u-server-ip>             300  (optional)
```

**Example** (if server IP is 203.0.113.10):
```
@                A       203.0.113.10                300
01u              A       203.0.113.10                300
api              A       203.0.113.10                300
```

### Step 3: Verify DNS Propagation

Wait 5-15 minutes, then test:

```bash
# Check if DNS is working
dig 01u.aybllc.org +short
# Should return: 203.0.113.10 (your server IP)

dig api.aybllc.org +short
# Should return: 203.0.113.10

dig aybllc.org +short
# Should return: 203.0.113.10

# Or use nslookup
nslookup 01u.aybllc.org
nslookup api.aybllc.org
```

---

## Option B: Run Your Own DNS Server (Advanced)

### Why Run Your Own DNS?

- Full control over DNS records
- Faster updates (no waiting for propagation)
- Can run internal DNS for private networks
- Professional setup

### Requirements

- **Primary nameserver:** ns1.aybllc.org (on 01u.aybllc.org)
- **Secondary nameserver:** ns2.aybllc.org (on same or different server)
- Server must have static IP
- Port 53 (UDP/TCP) must be open

---

### Step 1: Install BIND (DNS Server)

On 01u.aybllc.org:

```bash
# Install BIND DNS server
sudo dnf install -y bind bind-utils

# Verify installation
named -v
```

---

### Step 2: Configure BIND

```bash
# Backup original config
sudo cp /etc/named.conf /etc/named.conf.backup

# Edit main configuration
sudo nano /etc/named.conf
```

Add/modify these sections:

```bind
// /etc/named.conf

options {
    listen-on port 53 { any; };
    listen-on-v6 port 53 { any; };
    directory       "/var/named";
    dump-file       "/var/named/data/cache_dump.db";
    statistics-file "/var/named/data/named_stats.txt";
    memstatistics-file "/var/named/data/named_mem_stats.txt";

    recursion no;  // This is an authoritative-only DNS server

    allow-query     { any; };
    allow-transfer  { none; };  // No zone transfers for security

    dnssec-validation yes;
};

// Logging
logging {
    channel default_debug {
        file "data/named.run";
        severity dynamic;
    };
};

// Root zone
zone "." IN {
    type hint;
    file "named.ca";
};

// Your domain zone
zone "aybllc.org" IN {
    type master;
    file "aybllc.org.zone";
    allow-update { none; };
};

// Reverse DNS (optional, replace with your IP range)
zone "113.0.203.in-addr.arpa" IN {
    type master;
    file "203.0.113.rev";
    allow-update { none; };
};
```

---

### Step 3: Create Zone File

```bash
# Create zone file
sudo nano /var/named/aybllc.org.zone
```

**Zone file content** (replace <SERVER_IP> with actual IP):

```bind
$TTL 86400
@   IN  SOA     ns1.aybllc.org. admin.aybllc.org. (
                    2025102401  ; Serial (YYYYMMDDNN)
                    3600        ; Refresh (1 hour)
                    1800        ; Retry (30 minutes)
                    604800      ; Expire (1 week)
                    86400       ; Minimum TTL (1 day)
)

; Nameservers
@               IN  NS      ns1.aybllc.org.
@               IN  NS      ns2.aybllc.org.

; A Records
@               IN  A       <SERVER_IP>
ns1             IN  A       <SERVER_IP>
ns2             IN  A       <SERVER_IP>
01u             IN  A       <SERVER_IP>
api             IN  A       <SERVER_IP>
www             IN  A       <SERVER_IP>

; MX Records (email - optional)
@               IN  MX  10  mail.aybllc.org.
mail            IN  A       <SERVER_IP>

; TXT Records (SPF, DKIM, DMARC - optional for email)
@               IN  TXT     "v=spf1 mx ~all"
```

**Example** (if SERVER_IP is 203.0.113.10):
```bind
$TTL 86400
@   IN  SOA     ns1.aybllc.org. admin.aybllc.org. (
                    2025102401
                    3600
                    1800
                    604800
                    86400
)

@               IN  NS      ns1.aybllc.org.
@               IN  NS      ns2.aybllc.org.

@               IN  A       203.0.113.10
ns1             IN  A       203.0.113.10
ns2             IN  A       203.0.113.10
01u             IN  A       203.0.113.10
api             IN  A       203.0.113.10
www             IN  A       203.0.113.10
```

---

### Step 4: Create Reverse DNS Zone (Optional)

```bash
# Create reverse zone file (adjust for your IP)
sudo nano /var/named/203.0.113.rev
```

```bind
$TTL 86400
@   IN  SOA     ns1.aybllc.org. admin.aybllc.org. (
                    2025102401
                    3600
                    1800
                    604800
                    86400
)

@               IN  NS      ns1.aybllc.org.
@               IN  NS      ns2.aybllc.org.

; PTR Records (replace 10 with last octet of your IP)
10              IN  PTR     01u.aybllc.org.
10              IN  PTR     api.aybllc.org.
10              IN  PTR     ns1.aybllc.org.
```

---

### Step 5: Set File Permissions

```bash
# Set ownership
sudo chown named:named /var/named/aybllc.org.zone
sudo chown named:named /var/named/203.0.113.rev

# Set permissions
sudo chmod 640 /var/named/aybllc.org.zone
sudo chmod 640 /var/named/203.0.113.rev

# Set SELinux context
sudo restorecon -v /var/named/aybllc.org.zone
sudo restorecon -v /var/named/203.0.113.rev
```

---

### Step 6: Verify Configuration

```bash
# Check named.conf syntax
sudo named-checkconf

# Check zone file syntax
sudo named-checkzone aybllc.org /var/named/aybllc.org.zone
# Should show: OK

# Check reverse zone
sudo named-checkzone 113.0.203.in-addr.arpa /var/named/203.0.113.rev
```

---

### Step 7: Open Firewall

```bash
# Open DNS port (53)
sudo firewall-cmd --permanent --add-service=dns
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-services | grep dns
```

---

### Step 8: Start DNS Server

```bash
# Enable and start BIND
sudo systemctl enable named
sudo systemctl start named

# Check status
sudo systemctl status named

# Check logs
sudo journalctl -u named -f
```

---

### Step 9: Test DNS Locally

```bash
# Test queries to localhost
dig @localhost aybllc.org
dig @localhost api.aybllc.org
dig @localhost 01u.aybllc.org
dig @localhost ns1.aybllc.org

# All should return your server IP
```

---

### Step 10: Update Domain Registrar

At your domain registrar:

1. **Register nameservers** (called "Glue Records" or "Child Nameservers"):
   ```
   ns1.aybllc.org → 203.0.113.10 (your server IP)
   ns2.aybllc.org → 203.0.113.10 (same server)
   ```

2. **Change domain nameservers** to:
   ```
   ns1.aybllc.org
   ns2.aybllc.org
   ```

**Note:** This can take 24-48 hours to propagate globally.

---

### Step 11: Verify Public DNS

Wait 1-2 hours, then test from external:

```bash
# Test from public DNS
dig @8.8.8.8 aybllc.org
dig @1.1.1.1 api.aybllc.org

# Check nameservers
dig aybllc.org NS
# Should show: ns1.aybllc.org and ns2.aybllc.org
```

---

## Quick Setup Summary

### For Registrar DNS (Easy):
1. Get server IP: `curl -4 ifconfig.me`
2. Add A records at registrar:
   - `01u.aybllc.org` → server IP
   - `api.aybllc.org` → server IP
3. Wait 5-15 min, test: `dig api.aybllc.org`

### For Own DNS Server (Advanced):
1. Install: `sudo dnf install bind bind-utils`
2. Configure: `/etc/named.conf`
3. Create zone: `/var/named/aybllc.org.zone`
4. Open firewall: `sudo firewall-cmd --add-service=dns`
5. Start: `sudo systemctl start named`
6. Update registrar nameservers

---

## Troubleshooting

### DNS not resolving:
```bash
# Check DNS server is running
sudo systemctl status named

# Check firewall
sudo firewall-cmd --list-services | grep dns

# Check SELinux denials
sudo ausearch -m avc -ts recent | grep named

# Check logs
sudo journalctl -u named -n 50
```

### Zone file errors:
```bash
# Validate zone file
sudo named-checkzone aybllc.org /var/named/aybllc.org.zone

# Common issues:
# - Missing trailing dots (.) on FQDNs
# - Incorrect serial number
# - Wrong file permissions
```

### SELinux blocking:
```bash
# Allow BIND to read zone files
sudo setsebool -P named_write_master_zones 1

# Restore context
sudo restorecon -Rv /var/named
```

---

## Recommendation

**Start with Option A** (registrar DNS) to get the API running quickly.

**Migrate to Option B** later if you need:
- Frequent DNS updates
- Internal DNS resolution
- Full control

You can switch between them anytime without downtime.

---

## What You Need Right Now

**Minimum to proceed:**

1. Get server IP from 01u.aybllc.org
2. Add these A records at your registrar:
   ```
   01u.aybllc.org → <server-ip>
   api.aybllc.org → <server-ip>
   ```
3. Wait 10 minutes
4. Test: `dig api.aybllc.org`
5. Proceed with API deployment

That's it! DNS server setup can wait.

---

**Status:** Ready to implement
**Last Updated:** 2025-10-24
