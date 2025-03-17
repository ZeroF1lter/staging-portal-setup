from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, session, abort, make_response
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps
import csv
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = "./payloads"
DOWNLOAD_LOG = "./download_log.txt"
OBFUSCATED_FOLDER = "./obfuscated"
ALLOWED_EXTENSIONS = {'exe', 'ps1', 'dll', 'bin', 'sh', 'py', 'txt', 'cs', 'c', 'cpp', 'json', 'xml', 'yaml', 'yml'}
USERNAME = "redteam"
PASSWORD = "hunter2"
TOKEN_EXPIRY_MINUTES = 10

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OBFUSCATED_FOLDER, exist_ok=True)

tokens = {}

def cleanup_expired_tokens():
    expired = [t for t, (f, e) in tokens.items() if datetime.utcnow() > e]
    for t in expired:
        tokens.pop(t)

login_template = """
<html><head><title>Login</title></head><body style="background:#111;color:#ccc;font-family:sans-serif;text-align:center;padding:50px;">
<h2>🔐 Login</h2>
<form method="POST">
  Username: <input name="username"><br><br>
  Password: <input name="password" type="password"><br><br>
  <input type="submit" value="Login">
</form>
</body></html>
"""

portal_template = """
<html><head><title>Payload Portal</title></head><body style="background:#1a1a1a;color:#eee;font-family:sans-serif;padding:40px;">
<h2>💣 Private Payload Portal</h2>
<p>Welcome, {{ user }} | <a href="/logout" style="color:lime;">Logout</a></p>
<hr>
<h3>⬆ Upload New Payload</h3>
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="file">
  <input type="submit" value="Upload">
</form>
<hr>
<h3>📂 Available Payloads</h3>
<ul>
{% for f in files %}
  <li>{{ f }} - <a href="/generate/{{ f }}" style="color:cyan;">[Generate Expiring Link]</a>
  | <a href="/obfuscate/{{ f }}" style="color:orange;">[Obfuscate]</a></li>
{% endfor %}
</ul>
<hr>
<h3>📈 Stats Dashboard</h3>
<ul>
  <li>Total payloads uploaded: {{ stats.total_files }}</li>
  <li>Total downloads logged: {{ stats.total_downloads }}</li>
  <li>Active tokens: {{ stats.active_tokens }}</li>
  <li>Most downloaded file: {{ stats.top_file }}</li>
</ul>
<p><a href="/export" style="color:orange;">📤 Export Logs (CSV)</a></p>
<hr>
<h3>📜 Download Log</h3>
<pre style="background:#222;padding:10px;border-radius:10px;max-height:300px;overflow:auto;">{{ logs }}</pre>
</body></html>
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/portal')
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == USERNAME and pw == PASSWORD:
            session['user'] = user
            return redirect('/portal')
    return render_template_string(login_template)

@app.route('/portal', methods=['GET', 'POST'])
@login_required
def portal():
    cleanup_expired_tokens()
    if request.method == 'POST':
        f = request.files.get('file')
        if f and allowed_file(f.filename):
            f.save(os.path.join(UPLOAD_FOLDER, f.filename))
    files = os.listdir(UPLOAD_FOLDER)
    logs = ""
    log_entries = []
    if os.path.exists(DOWNLOAD_LOG):
        with open(DOWNLOAD_LOG, 'r') as lf:
            logs = lf.read()
            log_entries = lf.readlines()
    stats = {
        "total_files": len(files),
        "total_downloads": len(log_entries),
        "active_tokens": len(tokens),
        "top_file": "n/a"
    }
    counter = {}
    for entry in log_entries:
        if "downloaded" in entry:
            fname = entry.strip().split(" downloaded ")[-1]
            counter[fname] = counter.get(fname, 0) + 1
    if counter:
        stats["top_file"] = max(counter, key=counter.get)
    return render_template_string(portal_template, user=session['user'], files=files, logs=logs, stats=stats)

@app.route('/generate/<filename>')
@login_required
def generate(filename):
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return "File not found.", 404
    token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    tokens[token] = (filename, expiry)
    link = url_for('download_token', token=token, _external=True)
    return f"<html><body style='background:#000;color:#fff;text-align:center;padding:50px;'><h3>🔗 Your Expiring Link:</h3><p><a href='{link}' style='color:lime;font-size:18px'>{link}</a><br><br>Valid until {expiry} UTC</p></body></html>"

@app.route('/dl/<token>')
def download_token(token):
    cleanup_expired_tokens()
    ua = request.headers.get('User-Agent', '')
    if not ua.lower().startswith("mozilla"):
        abort(403)
    if token not in tokens:
        return "Invalid or expired link.", 403
    filename, expiry = tokens[token]
    if datetime.utcnow() > expiry:
        tokens.pop(token)
        return "Link expired.", 403
    with open(DOWNLOAD_LOG, 'a') as lf:
        lf.write(f"{datetime.utcnow()} - {request.remote_addr} downloaded {filename}\n")
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/export')
@login_required
def export_logs():
    if not os.path.exists(DOWNLOAD_LOG):
        return "No logs available."
    response = make_response()
    response.headers['Content-Disposition'] = 'attachment; filename=download_log.csv'
    response.headers['Content-Type'] = 'text/csv'
    output = []
    with open(DOWNLOAD_LOG, 'r') as lf:
        for line in lf:
            parts = line.strip().split(' - ')
            if len(parts) == 2 and 'downloaded' in parts[1]:
                ip, file = parts[1].split(' downloaded ')
                output.append([parts[0], ip.strip(), file.strip()])
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'IP', 'Filename'])
    writer.writerows(output)
    return response

@app.route('/obfuscate/<filename>')
@login_required
def obfuscate(filename):
    full_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(full_path):
        return "File not found.", 404
    with open(full_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    obf_file = os.path.join(OBFUSCATED_FOLDER, filename + ".b64.txt")
    with open(obf_file, 'w') as outf:
        outf.write(encoded)
    return f"<html><body style='background:#111;color:#0f0;padding:40px;text-align:center;'><h3>✅ Obfuscation Complete</h3><p>Your obfuscated payload is saved as:<br><code>{obf_file}</code></p><p>Contents:<br><textarea style='width:90%;height:300px;background:#000;color:#0f0;'>{encoded}</textarea></p></body></html>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
