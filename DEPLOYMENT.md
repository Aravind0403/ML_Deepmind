# Private 24/7 Deployment Guide (Ubuntu 24.04 LTS + Tailscale)

This setup runs your **ML Command Center & Interview Studio** 24/7 on your local home server (`aravind04`) and allows secure, encrypted access from your Mac, iPad, or phone via **Tailscale** with **$0 cloud fees and 100% privacy**.

---

## 1. Quick Start with Docker (Recommended)

### Prerequisites on Ubuntu:
Ensure Docker & Docker Compose are installed:
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
newgrp docker
```

### Run the App:
```bash
# 1. Clone your repository
git clone <your-repo-url> ml-command-center
cd ml-command-center

# 2. (Optional) Add your API keys for live LLM grading
cp .env.example .env
# nano .env

# 3. Start everything in detached mode (auto-restarts on reboot)
docker compose up -d --build
```

To view logs or stop:
```bash
docker compose logs -f
docker compose down
```

---

## 2. Remote Access via Tailscale

1. **Install Tailscale on Ubuntu**:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. **Install Tailscale on your Mac / iPad / iPhone**:
   - Download the Tailscale app from the App Store and log into the same account.
3. **Open the App**:
   - From any device connected to your Tailscale tailnet:
     ```
     http://<tailscale-ip>:3000
     # or using MagicDNS:
     http://aravind04:3000
     ```
   - All API requests are proxied internally through port 3000 — no CORS configuration or extra open ports needed.

---

## 3. Alternative: Running Natively with Systemd (No Docker)

If you prefer running directly on Ubuntu without Docker containers:

### Setup Backend:
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nodejs npm

# Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Setup Frontend:
```bash
cd frontend
npm ci
npm run build
cd ..
```

### Systemd Services:
Create `/etc/systemd/system/ml-backend.service`:
```ini
[Unit]
Description=ML Command Center FastAPI Backend
After=network.target

[Service]
Type=simple
User=aravindsundaresan
WorkingDirectory=/home/aravindsundaresan/ml-command-center
ExecStart=/home/aravindsundaresan/ml-command-center/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/ml-frontend.service`:
```ini
[Unit]
Description=ML Command Center Next.js Frontend
After=network.target ml-backend.service

[Service]
Type=simple
User=aravindsundaresan
WorkingDirectory=/home/aravindsundaresan/ml-command-center/frontend
Environment=INTERNAL_API_URL=http://127.0.0.1:8000
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start on boot:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ml-backend ml-frontend
```
