#!/bin/bash
# UHA API Service Deployment Script

set -e  # Exit on error

echo "=== UHA API Service Deployment ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Configuration
APP_DIR="/opt/uha-api"
APP_USER="uha-api"
REPO_URL="https://github.com/aybllc/uha-api-service.git"

echo "📁 Application directory: $APP_DIR"
echo "👤 Service user: $APP_USER"
echo ""

# Step 1: Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo "📥 Updating existing repository..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull
else
    echo "📥 Cloning repository..."
    if [ -d "$APP_DIR" ]; then
        echo "⚠️  Directory exists but is not a git repository"
        echo "Please remove it manually: rm -rf $APP_DIR"
        exit 1
    fi
    git clone "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

cd "$APP_DIR"

# Step 2: Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u "$APP_USER" python3.11 -m pip install --user -r requirements.txt

# Step 3: Ensure directories exist
echo "📂 Creating data and log directories..."
sudo -u "$APP_USER" mkdir -p data logs
chmod 770 data logs

# Step 4: Initialize database
echo "💾 Initializing database..."
sudo -u "$APP_USER" python3.11 -c "from app.database import db; print('Database initialized')"

# Step 5: Install systemd service
echo "⚙️  Installing systemd service..."
cp deploy/uha-api.service /etc/systemd/system/
systemctl daemon-reload

# Step 6: Install Nginx configuration
if [ -f /etc/nginx/conf.d/uha-api.conf ]; then
    echo "⚠️  Nginx config already exists, backing up..."
    cp /etc/nginx/conf.d/uha-api.conf /etc/nginx/conf.d/uha-api.conf.backup.$(date +%Y%m%d_%H%M%S)
fi

echo "🌐 Installing Nginx configuration..."
cp deploy/nginx.conf /etc/nginx/conf.d/uha-api.conf

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

# Step 7: Start services
echo "🚀 Starting services..."
systemctl enable uha-api
systemctl restart uha-api
systemctl reload nginx

# Step 8: Check status
echo ""
echo "📊 Service status:"
systemctl status uha-api --no-pager -l

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Obtain SSL certificate: sudo certbot --nginx -d api.aybllc.org"
echo "2. Create API keys: python3.11 scripts/manage_keys.py create <name> <email>"
echo "3. Test API: curl https://api.aybllc.org/v1/health"
echo ""
echo "View logs: sudo journalctl -u uha-api -f"
