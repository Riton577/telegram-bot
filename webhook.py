from flask import Flask, request
import json
import random

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form
    email = data.get('email')

    # Générer un code aléatoire
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
    return '', 200

if __name__ == "__main__":
    app.run()
