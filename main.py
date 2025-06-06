from flask import Flask, request
import json
import random
import os
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Serveur actif", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form
    email = data.get('email')

    if not email:
        return "❌ Email non fourni", 400

    code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

    try:
        with open("codes_valides.json", "r") as f:
            codes = json.load(f)
    except:
        codes = {}

    codes[code] = True

    with open("codes_valides.json", "w") as f:
        json.dump(codes, f)

    print(f"✅ Code généré pour {email} : {code}")
    return "OK", 200

@app.route('/activate', methods=['POST'])
def activate():
    data = request.form
    user_id = data.get("user_id")
    code = data.get("code")

    if not user_id or not code:
        return "❌ user_id ou code manquant", 400

    try:
        with open("codes_valides.json", "r") as f:
            codes = json.load(f)
    except:
        return "❌ Fichier codes_valides.json manquant", 500

    if code not in codes:
        return "❌ Code invalide", 400

    del codes[code]
    with open("codes_valides.json", "w") as f:
        json.dump(codes, f)

    try:
        with open("users_actifs.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

    expire_time = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    users[user_id] = expire_time

    with open("users_actifs.json", "w") as f:
        json.dump(users, f)

    print(f"✅ Utilisateur {user_id} activé jusqu’à {expire_time}")
    return "✅ Accès activé 24h", 200

@app.route('/actifs', methods=['GET'])
def actifs():
    try:
        with open("users_actifs.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

    now = datetime.utcnow()
    actifs = {}

    for user_id, expiration in users.items():
        try:
            expire_time = datetime.fromisoformat(expiration)
            if expire_time > now:
                reste = expire_time - now
                actifs[user_id] = str(reste)
        except:
            continue

    return json.dumps(actifs), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
