#!/bin/bash
# Deployment script for jeevesmcp.com
# Usage: ./deploy.sh [user@server]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER=${1:-"root@jeevesmcp.com"}
WEBROOT="/var/www/jeevesmcp.com"
CADDYFILE="/etc/caddy/Caddyfile"

echo -e "${BLUE}🎩 Jeeves Website Deployment${NC}"
echo ""

# Step 1: Build documentation
echo -e "${BLUE}📚 Building Sphinx documentation...${NC}"
cd docs
make clean
make html
cd ..

if [ ! -d "docs/_build/html" ]; then
    echo -e "${RED}❌ Build failed - docs/_build/html not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Documentation built successfully${NC}"

# Step 2: Create deployment package
echo -e "${BLUE}📦 Creating deployment package...${NC}"
DEPLOY_DIR=$(mktemp -d)
cp -r docs/_build/html/* "$DEPLOY_DIR/"

# Add custom 404 page if not exists
if [ ! -f "$DEPLOY_DIR/404.html" ]; then
    cat > "$DEPLOY_DIR/404.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found | Jeeves</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            padding: 20px;
            text-align: center;
        }
        .emoji { font-size: 64px; }
        h1 { color: #333; }
        p { color: #666; line-height: 1.6; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="emoji">🎩</div>
    <h1>404 - Page Not Found</h1>
    <p>Sorry, the page you're looking for doesn't exist.</p>
    <p><a href="/">← Back to Jeeves Documentation</a></p>
</body>
</html>
EOF
fi

echo -e "${GREEN}✅ Package ready${NC}"

# Step 3: Deploy to server
echo -e "${BLUE}🚀 Deploying to $SERVER...${NC}"

# Create webroot if doesn't exist
ssh "$SERVER" "mkdir -p $WEBROOT"

# Sync files to server (using rsync if available, otherwise scp)
if command -v rsync &> /dev/null; then
    rsync -avz --delete "$DEPLOY_DIR/" "$SERVER:$WEBROOT/"
else
    # Fallback to scp (remove old files first)
    ssh "$SERVER" "rm -rf $WEBROOT/*"
    scp -r "$DEPLOY_DIR/"* "$SERVER:$WEBROOT/"
fi

# Cleanup temp directory
rm -rf "$DEPLOY_DIR"

echo -e "${GREEN}✅ Files deployed${NC}"

# Step 4: Update Caddy configuration if needed
echo -e "${BLUE}🔧 Checking Caddy configuration...${NC}"

# Check if Caddyfile needs updating
if ssh "$SERVER" "[ -f $CADDYFILE ]"; then
    echo -e "${BLUE}   Caddyfile exists, checking for updates...${NC}"
    # You can add diff logic here to compare local vs remote Caddyfile
else
    echo -e "${YELLOW}⚠️  Caddyfile not found on server, uploading...${NC}"
    scp Caddyfile "$SERVER:$CADDYFILE"
    ssh "$SERVER" "systemctl reload caddy"
fi

# Step 5: Verify deployment
echo -e "${BLUE}🔍 Verifying deployment...${NC}"
sleep 2

if curl -s -o /dev/null -w "%{http_code}" https://jeevesmcp.com | grep -q "200"; then
    echo -e "${GREEN}✅ Website is live!${NC}"
    echo ""
    echo -e "${BLUE}🌐 https://jeevesmcp.com${NC}"
else
    echo -e "${YELLOW}⚠️  Website returned non-200 status${NC}"
    echo "   Check server logs: ssh $SERVER 'tail -f /var/log/caddy/*.log'"
fi

echo ""
echo -e "${GREEN}🎩 Deployment complete!${NC}"
