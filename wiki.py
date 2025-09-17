import os
import asyncio
import logging
import httpx
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters
import wikipediaapi
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_URL = os.getenv("RENDER_EXTERNAL_URL")
KEEPALIVE_SECONDS = int(os.getenv("KEEPALIVE_SECONDS", "600"))

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан")

application: Application = ApplicationBuilder().token(TOKEN).build()

wiki = wikipediaapi.Wikipedia(
    language="ru",
    user_agent="WikiBot/1.0 (https://wikibot.onrender.com; kimdaniel2204@gmail.com)"
)

def normalize_query(text: str) -> str:
    text = text.lower().strip()
    prefixes = [
        "что такое",
        "кто такой",
        "кто такая",
        "кто такие",
        "расскажи про",
        "расскажи о",
        "определи",
        "дай определение",
        "что значит",
    ]
    for p in prefixes:
        if text.startswith(p):
            text = text[len(p):].strip()
            break
    return text.capitalize()

async def get_first_page_image(title: str):
    url = "https://ru.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "images",
        "format": "json"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            images = page.get("images", [])
            for img in images:
                img_title = img.get("title")
                # Получаем URL изображения
                params_file = {
                    "action": "query",
                    "titles": img_title,
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "format": "json"
                }
                r_file = await client.get(url, params=params_file)
                file_data = r_file.json()
                file_pages = file_data.get("query", {}).get("pages", {})
                for _, f in file_pages.items():
                    image_url = f.get("imageinfo", [{}])[0].get("url")
                    if image_url and image_url.lower().endswith((".jpg", ".jpeg", ".png")):
                        return image_url
    return None

async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Я бот Википедии \n"
        "Отправь слово или словосочетание — я пришлю краткое описание и картинку."
    )

async def search(update: Update, context):
    query = normalize_query(update.message.text)

    page = wiki.page(query)
    if not page.exists():
        url = "https://ru.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 1,
            "namespace": 0,
            "format": "json"
        }
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params)
            data = r.json()
            if data[1]:
                page = wiki.page(data[1][0])
            else:
                await update.message.reply_text("Не удалось найти статью. Попробуйте другой запрос.")
                return

    summary = page.summary[0:800] + "..." if len(page.summary) > 800 else page.summary
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("Читать в Википедии", url=page.fullurl)
    )

    image_url = await get_first_page_image(page.title)
    if image_url:
        await update.message.reply_photo(photo=image_url, caption=summary, reply_markup=keyboard)
    else:
        await update.message.reply_text(summary, reply_markup=keyboard)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

async def keepalive():
    if not APP_URL:
        return
    url = APP_URL.rstrip("/") + "/"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(url, timeout=10)
                logger.info(f"Keepalive ping {url}")
            except Exception as e:
                logger.warning(f"Keepalive error: {e}")
            await asyncio.sleep(KEEPALIVE_SECONDS)

async def on_startup():
    if APP_URL:
        webhook_url = APP_URL.rstrip("/") + "/webhook"
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")
    asyncio.create_task(keepalive())
    await application.initialize()
    await application.start()

async def on_shutdown():
    await application.stop()
    await application.shutdown()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def index():
    return {"status": "ok", "message": "Wikibot is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}