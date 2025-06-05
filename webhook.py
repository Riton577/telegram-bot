import os
from main import app

WEBHOOK_URL = "https://telegram-bot-79kl.onrender.com"  # ← Ton lien Render ici

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=WEBHOOK_URL
    )
