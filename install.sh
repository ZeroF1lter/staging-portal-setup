#!/bin/bash
set -e
echo "[+] Updating system and installing dependencies..."
sudo apt update && sudo apt install -y python3 python3-venv python3-pip curl unzip
echo "[+] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install flask
echo "[+] Creating payload directories..."
mkdir -p payloads obfuscated
echo "[+] Setup complete. Run the portal using: source venv/bin/activate && python3 staging_portal.py"
