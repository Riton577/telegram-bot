from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import json
from datetime import datetime, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")

users = {}

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Envoie ton code pour activer ton accès.\nExemple : /activer BTCVIP123")

# ✅ /activer <code>
async def activer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Utilise : /activer <ton_code>")
        return

    code = context.args[0]
    try:
        with open("codes_valides.json", "r") as f:
            codes = json.load(f)
    except:
        codes = {}

    if code in codes:
        user_id = str(update.message.chat_id)
        expiration = (datetime.now() + timedelta(hours=24)).timestamp()

        try:
            with open("users_actifs.json", "r") as f:
                users = json.load(f)
        except:
            users = {}

        users[user_id] = expiration
        with open("users_actifs.json", "w") as f:
            json.dump(users, f)

        del codes[code]
        with open("codes_valides.json", "w") as f:
            json.dump(codes, f)

        await update.message.reply_text("✅ Accès activé pour 24h !")
    else:
        await update.message.reply_text("❌ Code invalide ou déjà utilisé.")

# ✅ /actifs
async def actifs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("users_actifs.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

    now = datetime.now().timestamp()
    actifs = {k: v for k, v in users.items() if v > now}
    txt = "\n".join([f"🟢 {uid} – expire dans {(v - now)//3600:.1f}h" for uid, v in actifs.items()])
    await update.message.reply_text(f"Utilisateurs actifs :\n{txt}" if txt else "❌ Aucun utilisateur actif.")

# ✅ Lancer le bot
def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activer", activer))
    app.add_handler(CommandHandler("actifs", actifs))

    app.run_polling()

if __name__ == "__main__":
    run_bot()
