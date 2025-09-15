import os
import asyncio
import logging
import httpx
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters
import wikipediaapi

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Конфигурация ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_URL = os.getenv("RENDER_EXTERNAL_URL")  # например: https://your-app.onrender.com
KEEPALIVE_SECONDS = int(os.getenv("KEEPALIVE_SECONDS", "600"))

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не задан")

application: Application = ApplicationBuilder().token(TOKEN).build()


wiki = wikipediaapi.Wikipedia("ru")


app = FastAPI()



async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Я бот Википедии 🚀\n"
        "Отправь слово или словосочетание — я пришлю краткое описание и картинку."
    )


async def search(update: Update, context):
    query = update.message.text.strip()
    page = wiki.page(query)

    if not page.exists():
        await update.message.reply_text("❌ Не удалось найти статью. Попробуйте другое слово.")
        return

    summary = page.summary[0:800] + "..." if len(page.summary) > 800 else page.summary

    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("Читать в Википедии 🌍", url=page.fullurl)
    )

    image_sent = False
    if page.images:
        for img_url in page.images.keys():
            if img_url.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    await update.message.reply_photo(photo=img_url, caption=summary, reply_markup=keyboard)
                    image_sent = True
                    break
                except Exception as e:
                    logger.warning(f"Не удалось отправить изображение: {e}")
                    continue

    if not image_sent:
        await update.message.reply_text(summary, reply_markup=keyboard)


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))


@app.get("/")
async def index():
    return {"status": "ok", "message": "Wikibot is running 🚀"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

async def keepalive():
    """Периодически пингуем свой Render URL, чтобы уменьшить шанс засыпания."""
    if not APP_URL:
        logger.warning("⚠️ RENDER_EXTERNAL_URL не задан — keepalive выключен")
        return
    url = APP_URL.rstrip("/") + "/"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(url, timeout=10)
                logger.info(f"✅ Keepalive ping {url}")
            except Exception as e:
                logger.warning(f"Keepalive error: {e}")
            await asyncio.sleep(KEEPALIVE_SECONDS)


async def on_startup():
    if APP_URL:
        webhook_url = APP_URL.rstrip("/") + "/webhook"
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f" Webhook установлен: {webhook_url}")
    else:
        logger.warning("⚠️ RENDER_EXTERNAL_URL не задан — webhook не установлен")


    asyncio.create_task(keepalive())


    asyncio.create_task(application.initialize())
    asyncio.create_task(application.start())


@app.on_event("startup")
async def startup_event():
    await on_startup()


@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()