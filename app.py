from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os, json, uuid, hashlib
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'studio_secret_key_change_me_12345'
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_FILE = 'database.json'

ADMIN_USER = 'admin'
ADMIN_PASS_HASH = hashlib.sha256('admin123'.encode()).hexdigest()
ALLOWED = {'png','jpg','jpeg','gif','webp','mp4','mov','webm','avi'}

def load_db():
    if not os.path.exists(DB_FILE):
        default = {
            "works": [],
            "settings": {
                "studioName": "MY STUDIO",
                "tagline": "Capturing Moments That Last Forever",
                "about": "We are a professional photography & videography studio. We capture your precious moments and turn them into timeless memories.",
                "phone": "+91 9999999999",
                "whatsapp": "919999999999",
                "instagram": "https://instagram.com/",
                "facebook": "https://facebook.com/",
                "email": "hello@studio.com",
                "address": "Your City, India",
                "heroImage": "",
                # NEW THEME FIELDS
                "accentColor": "#c9a96a",
                "themeMode": "dark",
                "headingFont": "Cormorant Garamond",
                "bodyFont": "Inter",
                "navbarStyle": "glass",
                "borderRadius": "0"
            }
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default, f, indent=2)
        return default
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/uploads/<path:filename>')
def uploaded(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/settings')
def api_settings():
    return jsonify(load_db()['settings'])

@app.route('/api/works')
def api_works():
    return jsonify(load_db()['works'])

def logged_in():
    return session.get('logged_in') is True

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json or {}
    u = d.get('username', '')
    p = hashlib.sha256(d.get('password', '').encode()).hexdigest()
    if u == ADMIN_USER and p == ADMIN_PASS_HASH:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Galat username ya password"}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/check-auth')
def api_check():
    return jsonify({"loggedIn": logged_in()})

@app.route('/api/work', methods=['POST'])
def add_work():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    title = request.form.get('title', '').strip()
    caption = request.form.get('caption', '').strip()
    if 'file' not in request.files or not title:
        return jsonify({"error": "Title aur file dono zaroori hai"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "File select karo"}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": "Sirf photo/video allowed hai"}), 400
    category = 'video' if ext in {'mp4','mov','webm','avi'} else 'photo'
    fname = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, fname))
    db = load_db()
    work = {
        "id": uuid.uuid4().hex,
        "title": title,
        "caption": caption,
        "category": category,
        "fileUrl": f"/uploads/{fname}",
        "date": datetime.now().strftime("%d %b %Y")
    }
    db['works'].insert(0, work)
    save_db(db)
    return jsonify(work)

@app.route('/api/work/<wid>', methods=['DELETE'])
def del_work(wid):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    db = load_db()
    w = next((x for x in db['works'] if x['id'] == wid), None)
    if w:
        try: os.remove(os.path.join('.', w['fileUrl'].lstrip('/')))
        except: pass
    db['works'] = [x for x in db['works'] if x['id'] != wid]
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/work/<wid>', methods=['PUT'])
def edit_work(wid):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json or {}
    db = load_db()
    for w in db['works']:
        if w['id'] == wid:
            w['title'] = d.get('title', w['title'])
            w['caption'] = d.get('caption', w['caption'])
            break
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    db = load_db()
    # Text fields
    for k in ['studioName','tagline','about','phone','whatsapp',
              'instagram','facebook','email','address',
              'accentColor','themeMode','headingFont','bodyFont',
              'navbarStyle','borderRadius']:
        if k in request.form:
            db['settings'][k] = request.form[k]
    # Hero image
    if 'heroImage' in request.files:
        f = request.files['heroImage']
        if f.filename:
            ext = f.filename.rsplit('.', 1)[-1].lower()
            fname = f"hero-{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_FOLDER, fname))
            db['settings']['heroImage'] = f"/uploads/{fname}"
    save_db(db)
    return jsonify(db['settings'])

if __name__ == '__main__':
    print("\n🔥 STUDIO WEBSITE STARTED")
    print("🌐 Website : http://localhost:5000")
    print("🔐 Admin   : http://localhost:5000/#studio-admin-2024")
    print("👤 Login   : admin / admin123\n")
    app.run(debug=True, host='0.0.0.0', port=5000)