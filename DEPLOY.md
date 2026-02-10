# 🌐 Deploying Jeeves Website

This guide explains how to deploy the Jeeves documentation website to a server running Caddy.

## Overview

- **Source**: Sphinx documentation in `docs/`
- **Build**: Static HTML files
- **Server**: Caddy web server
- **Domain**: jeevesmcp.com
- **Auto-deploy**: GitHub Actions on push to main

---

## 📋 Prerequisites

### Server Requirements

- Ubuntu 22.04+ (or similar Linux distribution)
- Root or sudo access
- Domain pointing to server IP
- Ports 80 and 443 open

### Install Caddy

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Verify installation
caddy version
```

---

## 🚀 Quick Start

### Option 1: Manual Deployment

```bash
# 1. Clone the repository
git clone https://github.com/marchon/jeevesmcp.com.git
cd jeevesmcp.com

# 2. Deploy to your server
./deploy.sh user@your-server.com
```

### Option 2: Automatic Deployment (GitHub Actions)

1. Fork/push this repo to GitHub
2. Add these secrets to your GitHub repository:
   - `SSH_PRIVATE_KEY`: Your server's SSH private key
   - `SERVER_HOST`: Your server IP or domain
   - `SERVER_USER`: SSH username (usually `root` or `caddy`)

3. Push to `main` branch - deployment happens automatically!

---

## 🔧 Server Setup

### 1. Create Web Root

```bash
sudo mkdir -p /var/www/jeevesmcp.com
sudo chown -R caddy:caddy /var/www/jeevesmcp.com
```

### 2. Configure Caddy

Copy the Caddyfile to your server:

```bash
sudo cp Caddyfile /etc/caddy/Caddyfile
```

Edit as needed:
```bash
sudo nano /etc/caddy/Caddyfile
```

### 3. Start Caddy

```bash
# Reload Caddy configuration
sudo systemctl reload caddy

# Or restart if needed
sudo systemctl restart caddy

# Check status
sudo systemctl status caddy
```

### 4. Enable HTTPS

Caddy automatically obtains Let's Encrypt certificates. Just ensure:
- Domain DNS points to server
- Ports 80/443 are open
- Caddy can bind to those ports

---

## 📁 Directory Structure

On the server:
```
/var/www/jeevesmcp.com/     # Website files
├── index.html              # Homepage
├── installation.html       # Docs pages
├── api.html
├── _static/                # CSS, JS, images
└── ...

/etc/caddy/Caddyfile        # Caddy configuration
/var/log/caddy/             # Access logs
```

---

## 🔐 Security

### File Permissions

```bash
# Set proper ownership
sudo chown -R caddy:caddy /var/www/jeevesmcp.com

# Set proper permissions
sudo chmod -R 755 /var/www/jeevesmcp.com
```

### SSH Key for Deployment

Generate a deploy key:
```bash
ssh-keygen -t ed25519 -C "deploy@jeevesmcp.com" -f deploy_key

# Add public key to server
cat deploy_key.pub >> ~/.ssh/authorized_keys

# Add private key to GitHub secrets
cat deploy_key  # Copy to GitHub -> Settings -> Secrets
```

---

## 🔄 Updating the Website

### Manual Update

```bash
# Build docs locally
cd docs && make html

# Deploy
./deploy.sh user@server
```

### Automatic Update

Just push to the `main` branch:
```bash
git add .
git commit -m "Update documentation"
git push origin main
# GitHub Actions handles the rest!
```

---

## 🐛 Troubleshooting

### Caddy Won't Start

```bash
# Check configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Check logs
sudo journalctl -u caddy -f

# Test configuration
sudo caddy run --config /etc/caddy/Caddyfile
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R caddy:caddy /var/www/jeevesmcp.com
sudo chmod -R 755 /var/www/jeevesmcp.com

# Ensure Caddy can read
sudo -u caddy ls -la /var/www/jeevesmcp.com
```

### HTTPS Not Working

```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check DNS
dig jeevesmcp.com

# Force Caddy to renew
caddy reload --config /etc/caddy/Caddyfile --force
```

### 404 Errors

Check that files exist:
```bash
ls -la /var/www/jeevesmcp.com/
```

---

## 📝 Local Development

Build and preview locally:

```bash
cd docs
make html

# Serve locally (Python 3)
cd _build/html
python -m http.server 8000

# Or with Caddy
caddy file-server --root . --listen :8000
```

Visit: http://localhost:8000

---

## 🎯 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. **Trigger**: Push to `main` branch
2. **Build**: Install Sphinx, build docs
3. **Test**: Verify build succeeded
4. **Deploy**: rsync to server via SSH
5. **Verify**: Check HTTP 200 response

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `SSH_PRIVATE_KEY` | SSH private key for server access |
| `SERVER_HOST` | Server IP or domain |
| `SERVER_USER` | SSH username |

Add secrets at: Settings → Secrets and variables → Actions

---

## 📊 Monitoring

### View Logs

```bash
# Caddy access logs
sudo tail -f /var/log/caddy/jeevesmcp.com.access.log

# Caddy error logs
sudo journalctl -u caddy -f

# Nginx-style combined log
sudo tail -f /var/log/caddy/access.log
```

### Health Check

```bash
# Test website
curl -I https://jeevesmcp.com

# Check certificate
echo | openssl s_client -servername jeevesmcp.com -connect jeevesmcp.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## 🎨 Customization

### Modify Caddy Behavior

Edit `/etc/caddy/Caddyfile`:

```caddy
jeevesmcp.com {
    # Change web root
    root * /path/to/your/html
    
    # Add redirects
    redir /old-page /new-page permanent
    
    # Add headers
    header X-Custom-Header "My Value"
    
    # Enable basic auth for staging
    basicauth /staging/* {
        admin $2a$14$...  # bcrypt hash
    }
}
```

### Add Custom Domain

```caddy
docs.jeevesmcp.com {
    root * /var/www/jeevesmcp.com
    file_server
}
```

---

## 🆘 Support

- **Caddy Docs**: https://caddyserver.com/docs/
- **GitHub Issues**: https://github.com/marchon/jeevesmcp.com/issues
- **Sphinx Docs**: https://www.sphinx-doc.org/

---

<p align="center">🎩 Happy Deploying!</p>
