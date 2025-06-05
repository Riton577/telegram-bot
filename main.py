import random
import requests
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "7563269635:AAH1pbs4x605GevyPcUDViDFpnZVHBfnPP0"
OCR_SPACE_API_KEY = "helloworld"  # clé gratuite par défaut
# Codes d’activation valides (à vendre)
try:
    with open("codes_valides.json", "r") as f:
        CODES_VALIDES = json.load(f)
except FileNotFoundError:
    CODES_VALIDES = {}

try:
    with open("access.json", "r") as f:
        ACCESS_EXPIRATIONS = json.load(f)
except FileNotFoundError:
    ACCESS_EXPIRATIONS = {}

# Liste des utilisateurs autorisés
# Charger les utilisateurs autorisés depuis un fichier
try:
    with open("whitelist.json", "r") as f:
        WHITELIST = json.load(f)
except FileNotFoundError:
    WHITELIST = []
    
ADMIN_ID = 1125669088


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Envoie une capture d'écran d'un graphique BTC, je vais analyser le prix réel et te donner un conseil !"
    )

def extract_price_from_text(text):
    numbers = [float(word.replace(',', '.')) for word in text.split() if word.replace(',', '.').replace('.', '', 1).isdigit()]
    # On suppose que le prix BTC est souvent entre 10000 et 1000000
    prix_probables = [n for n in numbers if 10000 < n < 1000000]
    return prix_probables[0] if prix_probables else None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in WHITELIST:
        await update.message.reply_text("🚫 Accès refusé. Active ton accès avec /activer MONCODE.")
        return

    user_id_str = str(update.effective_user.id)
    if user_id_str in ACCESS_EXPIRATIONS:
        from datetime import datetime
        expiration = datetime.fromisoformat(ACCESS_EXPIRATIONS[user_id_str])
        if datetime.now() > expiration:
            await update.message.reply_text("⛔ Ton accès a expiré. Réactive ton accès avec un nouveau code.")
            return
        else:
            now = datetime.now()
            restants = expiration - now
            heures = restants.seconds // 3600
            minutes = (restants.seconds % 3600) // 60
            await update.message.reply_text(
                f"⏳ Accès actif. Temps restant : {restants.days}j {heures}h{minutes}m"
            )

        
    await update.message.reply_text("📸 Image reçue, je lis les chiffres...")

    # Télécharger la photo envoyée
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_path = "graph.png"
    await file.download_to_drive(img_path)

    # Envoyer à OCR.space
    with open(img_path, 'rb') as f:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": f},
            data={"apikey": OCR_SPACE_API_KEY, "language": "eng"},
        )

    try:
        result_text = response.json()["ParsedResults"][0]["ParsedText"]
        print("📄 Texte OCR :", result_text)
        prix = extract_price_from_text(result_text)

        if prix:
            action = random.choice(["🔼 Achat", "🔽 Vente"])
            tp = round(prix + random.randint(50, 200), 2)
            sl = round(prix - random.randint(50, 200), 2)

            message = f"{action}\n🎯 TP : {tp}\n🛑 SL : {sl}\n📊 (Prix détecté : {prix})"
        else:
            message = "❌ Impossible de détecter un prix sur cette image."

    except Exception as e:
        print("❌ Erreur OCR :", e)
        message = "❌ Erreur pendant la lecture de l'image."

    await update.message.reply_text(f"🤖 Recommandation :\n{message}")

async def activer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Utilise : /activer TONCODE")
        return

    code = context.args[0]
    user_id = update.effective_user.id

    if code in CODES_VALIDES and CODES_VALIDES[code]:
        CODES_VALIDES[code] = False  # désactive le code
        
        with open("codes_valides.json", "w") as f:
            json.dump(CODES_VALIDES, f)
        
        WHITELIST.append(user_id)
        from datetime import datetime, timedelta

        # Définir l'expiration dans 24 heures
        expiration = (datetime.now() + timedelta(hours=24)).isoformat()
        ACCESS_EXPIRATIONS[str(user_id)] = expiration

        # Sauvegarder dans access.json
        with open("access.json", "w") as f:
            json.dump(ACCESS_EXPIRATIONS, f)


        # 🔐 Sauvegarde dans le fichier JSON
        with open("whitelist.json", "w") as f:
            json.dump(WHITELIST, f)

        await update.message.reply_text("✅ Accès activé ! Tu peux maintenant utiliser le bot.")

    else:
        await update.message.reply_text("🚫 Code invalide ou déjà utilisé.")
        
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Accès réservé à l'administrateur.")
        return

    if not WHITELIST:
        await update.message.reply_text("📭 Aucun utilisateur activé pour le moment.")
        return

    message = f"👤 Utilisateurs autorisés ({len(WHITELIST)} total) :\n"
    for uid in WHITELIST:
        message += f"• {uid}\n"

    await update.message.reply_text(message)

async def etat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_str = str(update.effective_user.id)

    if user_id_str not in ACCESS_EXPIRATIONS:
        await update.message.reply_text("ℹ️ Tu n’as pas d’accès actif.")
        return

    from datetime import datetime
    expiration = datetime.fromisoformat(ACCESS_EXPIRATIONS[user_id_str])
    now = datetime.now()
    if now > expiration:
        await update.message.reply_text("⛔ Ton accès a expiré.")
    else:
        remaining = expiration - now
        heures, reste = divmod(remaining.seconds, 3600)
        minutes = reste // 60
        await update.message.reply_text(
            f"🕒 Accès actif pour encore {remaining.days} jours, {heures}h{minutes}min."
        )

async def codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Accès réservé à l'administrateur.")
        return

    actifs = [code for code, dispo in CODES_VALIDES.items() if dispo]

    if not actifs:
        await update.message.reply_text("📭 Tous les codes ont été utilisés.")
        return

    message = f"🔑 Codes encore valides ({len(actifs)}) :\n"
    for code in actifs:
        message += f"• {code}\n"

    await update.message.reply_text(message)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès refusé. Admin uniquement.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗ Utilise : /reset TONCODE")
        return

    code = context.args[0]

    # Supprimer l’utilisateur associé à ce code (si trouvé)
    for uid in WHITELIST:
        if code in CODES_VALIDES and not CODES_VALIDES[code]:
            WHITELIST.remove(uid)
            break

    # Réactiver le code
    if code in CODES_VALIDES:
        CODES_VALIDES[code] = True
        with open("codes_valides.json", "w") as f:
            json.dump(CODES_VALIDES, f)
        with open("whitelist.json", "w") as f:
            json.dump(WHITELIST, f)
        await update.message.reply_text(f"🔄 Code {code} réinitialisé.")
    else:
        await update.message.reply_text("❌ Code non reconnu.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès refusé.")
        return

    from datetime import datetime

    now = datetime.now()
    actifs = []
    for uid, date_str in ACCESS_EXPIRATIONS.items():
        expiration = datetime.fromisoformat(date_str)
        if now < expiration:
            restants = expiration - now
            heures = restants.seconds // 3600
            minutes = (restants.seconds % 3600) // 60
            actifs.append(f"🟢 {uid} — expire dans {restants.days}j {heures}h{minutes}m")

    if not actifs:
        await update.message.reply_text("❌ Aucun utilisateur actif.")
    else:
        message = f"👥 Utilisateurs actifs ({len(actifs)}) :\n" + "\n".join(actifs)
        await update.message.reply_text(message)

async def actifs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return

    from datetime import datetime
    actifs = []

    for uid, date_str in ACCESS_EXPIRATIONS.items():
        expiration = datetime.fromisoformat(date_str)
        now = datetime.now()
        if now < expiration:
            restants = expiration - now
            heures = restants.seconds // 3600
            minutes = (restants.seconds % 3600) // 60
            actifs.append(f"🟢 {uid} – expire dans {restants.days}j {heures}h{minutes}m")

    if not actifs:
        await update.message.reply_text("❌ Aucun utilisateur actif.")
    else:
        message = f"👥 Utilisateurs actifs ({len(actifs)}) :\n" + "\n".join(actifs)
        await update.message.reply_text(message)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("activer", activer))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("codes", codes))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("etat", etat))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("actifs", actifs))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("✅ Bot OCR actif")
app.run_polling()
