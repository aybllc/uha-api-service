# GitHub Access Setup for Server

**Purpose:** Configure GitHub access for Claude Code on Rocky Linux 10 server
**Organization:** aybllc (All Your Baseline LLC)
**Date:** 2025-10-24

---

## Overview

This guide sets up GitHub access so Claude Code on the server can:
- Clone/push to aybllc repositories
- Create releases
- Manage repositories via GitHub CLI

---

## Method 1: GitHub CLI (Recommended)

### Step 1: Install GitHub CLI
```bash
# Install gh CLI on Rocky Linux 10
sudo dnf install -y 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install -y gh
```

### Step 2: Authenticate
```bash
# Option A: Interactive login (requires browser)
gh auth login

# Option B: Token-based (non-interactive)
echo "ghp_YOUR_TOKEN_HERE" | gh auth login --with-token
```

**Interactive login steps:**
1. Select: "GitHub.com"
2. Select: "HTTPS" (recommended) or "SSH"
3. Select: "Login with a web browser"
4. Copy the one-time code
5. Open browser and paste code
6. Authorize GitHub CLI

### Step 3: Verify Access
```bash
# Test authentication
gh auth status

# List your repos
gh repo list aybllc

# Test creating a repo (dry-run)
gh repo view aybllc/uha-blackbox
```

---

## Method 2: SSH Keys

### Step 1: Generate SSH Key
```bash
# Generate new SSH key for GitHub
ssh-keygen -t ed25519 -C "server@aybllc.org" -f ~/.ssh/github_aybllc

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/github_aybllc
```

### Step 2: Add Public Key to GitHub
```bash
# Display public key
cat ~/.ssh/github_aybllc.pub
```

**Manual steps:**
1. Copy the public key output
2. Go to https://github.com/settings/keys
3. Click "New SSH key"
4. Title: "Rocky Linux 10 Server - Claude Code"
5. Paste the public key
6. Click "Add SSH key"

### Step 3: Configure SSH
```bash
# Create/edit SSH config
cat >> ~/.ssh/config <<'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_aybllc
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
```

### Step 4: Test SSH Connection
```bash
ssh -T git@github.com
# Should see: "Hi <username>! You've successfully authenticated..."
```

---

## Method 3: Personal Access Token (PAT)

### Step 1: Generate Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Rocky Linux 10 Server - Claude Code"
4. Expiration: 90 days (or custom)
5. Select scopes:
   - ✅ `repo` (full control of private repos)
   - ✅ `workflow` (update GitHub Actions)
   - ✅ `admin:org` (if managing org repos)
   - ✅ `delete_repo` (if needed)
6. Click "Generate token"
7. **COPY TOKEN IMMEDIATELY** (won't be shown again)

### Step 2: Configure Git Credential Helper
```bash
# Store credentials in Git
git config --global credential.helper store

# Set up GitHub token
cat > ~/.git-credentials <<EOF
https://YOUR_GITHUB_USERNAME:ghp_YOUR_TOKEN_HERE@github.com
EOF

chmod 600 ~/.git-credentials
```

### Step 3: Test Token
```bash
# Clone a private repo to test
git clone https://github.com/aybllc/uha-blackbox.git /tmp/test-clone
```

---

## Configuring Git Identity

```bash
# Set global git config
git config --global user.name "All Your Baseline LLC"
git config --global user.email "claude@aybllc.org"

# Or use a specific identity for this project
cd /opt/uha-api
git config user.name "Claude Code Server"
git config user.email "server@aybllc.org"
```

---

## Creating GitHub Organization Repos

### Using gh CLI
```bash
# Create new repo in aybllc org
gh repo create aybllc/uha-api-service \
  --private \
  --description "UHA API Service - Hosted API for Universal Hierarchical Aggregation" \
  --clone

# Create public repo
gh repo create aybllc/uha-client \
  --public \
  --description "Python client library for UHA API" \
  --clone
```

### Using Git + GitHub
```bash
# Initialize local repo
cd /opt/uha-api
git init
git add .
git commit -m "Initial commit: UHA API Service

Hosted API service for secure access to UHA merge functionality.
Patent: US 63/902,536

🤖 Generated with Claude Code"

# Create remote repo via gh
gh repo create aybllc/uha-api-service --private --source=. --remote=origin --push
```

---

## Security Best Practices

### 1. Token Security
```bash
# Never commit tokens to repos
echo "*.token" >> ~/.gitignore_global
echo ".env" >> ~/.gitignore_global
echo "credentials*" >> ~/.gitignore_global
git config --global core.excludesfile ~/.gitignore_global
```

### 2. Key Permissions
```bash
# Ensure proper permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_aybllc
chmod 644 ~/.ssh/github_aybllc.pub
chmod 600 ~/.ssh/config
```

### 3. Token Rotation
- Rotate tokens every 90 days
- Revoke immediately if compromised
- Use different tokens for different servers/purposes

### 4. Audit Access
```bash
# View current authentication
gh auth status

# List authorized apps
gh auth status --show-token  # View current token (be careful!)
```

---

## Common Operations for Claude Code

### Clone Existing Repo
```bash
# HTTPS (with token)
git clone https://github.com/aybllc/uha-blackbox.git

# SSH
git clone git@github.com:aybllc/uha-blackbox.git
```

### Create New Repo
```bash
# Using gh CLI (easiest)
gh repo create aybllc/repo-name --private

# Manual
curl -H "Authorization: token ghp_YOUR_TOKEN" \
  https://api.github.com/orgs/aybllc/repos \
  -d '{"name":"repo-name","private":true}'
```

### Push Code
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### Create Release
```bash
# Using gh CLI
gh release create v1.0.0 \
  --title "UHA API v1.0.0" \
  --notes "Initial release" \
  ./build/*.whl

# List releases
gh release list
```

### Manage Issues
```bash
# Create issue
gh issue create --title "Bug: API returns 500" --body "Description..."

# List issues
gh issue list

# Close issue
gh issue close 123
```

---

## Testing GitHub Access

Run this test script to verify everything works:

```bash
#!/bin/bash
# test-github-access.sh

echo "=== Testing GitHub Access ==="

echo -e "\n1. Testing gh CLI authentication..."
if gh auth status 2>&1 | grep -q "Logged in"; then
    echo "✅ gh CLI authenticated"
else
    echo "❌ gh CLI not authenticated"
    exit 1
fi

echo -e "\n2. Testing repo access..."
if gh repo view aybllc/uha-blackbox &>/dev/null; then
    echo "✅ Can access aybllc repos"
else
    echo "❌ Cannot access aybllc repos"
    exit 1
fi

echo -e "\n3. Testing git config..."
if git config user.name &>/dev/null; then
    echo "✅ Git identity configured: $(git config user.name) <$(git config user.email)>"
else
    echo "⚠️  Git identity not configured"
fi

echo -e "\n4. Testing SSH (if configured)..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH authentication works"
else
    echo "⚠️  SSH not configured (HTTPS is fine)"
fi

echo -e "\n=== All tests passed! ==="
```

Save and run:
```bash
chmod +x test-github-access.sh
./test-github-access.sh
```

---

## Troubleshooting

### Error: "Authentication failed"
```bash
# Re-authenticate gh CLI
gh auth logout
gh auth login

# Or refresh token
gh auth refresh
```

### Error: "Permission denied (publickey)"
```bash
# Check SSH agent
ssh-add -l

# Re-add key
ssh-add ~/.ssh/github_aybllc

# Test connection
ssh -vT git@github.com
```

### Error: "Repository not found"
```bash
# Check if repo exists
gh repo view aybllc/repo-name

# Check permissions
gh api user/repos | jq '.[] | .full_name'
```

### Error: "Remote already exists"
```bash
# Remove and re-add
git remote remove origin
git remote add origin git@github.com:aybllc/repo-name.git
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Authenticate gh CLI | `gh auth login` |
| Check auth status | `gh auth status` |
| Clone repo | `gh repo clone aybllc/repo-name` |
| Create repo | `gh repo create aybllc/repo-name --private` |
| List repos | `gh repo list aybllc` |
| Create release | `gh release create v1.0.0` |
| View repo | `gh repo view aybllc/repo-name` |
| Push code | `git push origin main` |
| Create PR | `gh pr create` |

---

## Next Steps After Setup

Once GitHub access is configured:

1. **Clone existing repos:**
   ```bash
   cd /got
   gh repo clone aybllc/uha-blackbox
   ```

2. **Create new repo for API service:**
   ```bash
   gh repo create aybllc/uha-api-service --private
   ```

3. **Inform me (Claude Code) that setup is complete:**
   - Update `/got/SERVER_STATUS.md` with GitHub access status
   - I can then begin pushing code to repos

---

**Status:** Ready for implementation
**Last Updated:** 2025-10-24
**Maintained by:** Claude Code
