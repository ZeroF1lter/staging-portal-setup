#  Red Team Staging Portal Setup

A lightweight, Flask-based staging portal designed for red team engagements and payload delivery. This portal supports upload, expiring download links, file obfuscation, logging, and more.

##  Features
- (Basic-ass) Login-protected portal
- Upload & serve payloads
- Expiring download links
- Download log and CSV export
- Stats dashboard
- Base64 file obfuscator
- Auto-clean expired tokens
- Easy deployment with one-liner installer
- Optional systemd service auto-start

 
 ⚠ Note for Windows Users: If cloning this repo on Windows, line endings may break Linux scripts. Run "dos2unix install.sh" inside WSL before executing.


## Installation (Manual)
```bash
git clone https://github.com/zerof1lter/staging-portal-setup.git
cd staging-portal-setup
chmod +x install.sh
./install.sh
source venv/bin/activate
python3 staging_portal.py
```

## One-liner Deploy:
```bash
curl -sSL https://raw.githubusercontent.com/zerof1lter/staging-portal-setup/main/install.sh | bash
```

##  Default Credentials
- **Username:** `redteam`
- **Password:** `hunter2`

##  Systemd Auto-Start Setup (Optional)
1. Copy the service file:
```bash
sudo cp staging_portal.service /etc/systemd/system/staging_portal@yourusername.service
```

2. Enable and start:
```bash
sudo systemctl enable staging_portal@yourusername
sudo systemctl start staging_portal@yourusername
```

3. Check status:
```bash
sudo systemctl status staging_portal@yourusername
```

## Directory Structure
```
staging-portal-setup/
├── install.sh
├── staging_portal.py
├── payloads/
└── obfuscated/
```

##  Export Logs
Visit the portal and click **Export Logs (CSV)** to download IP + timestamp + file download history.

##  OPSEC Notes
- Only serves files to Mozilla-based User-Agents by default
- Easily hide the portal behind NGINX reverse proxy + basic auth
- Optional subdomain stealth deployment via `portal.domain.com`

---

Crafted with haste by `ZeroF1lter`
