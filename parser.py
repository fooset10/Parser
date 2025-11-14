import logging
import asyncio
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

# === НАСТРОЙКИ ===
API_TOKEN = '8288944295:AAFgN0cYP2Hz1qZVVSsBguQ2tul3p4oES80'
OWNER_ID = 123456789  # 🔑 ЗАМЕНИТЕ на ваш Telegram user_id!

# === ЛОГГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
user_games = {}
game_stats = {"total_games": 0, "total_guesses": 0}

# === СПИСОК МЕМОВ ===
MEME_URLS = [
    "https://i.imgur.com/4QbL9yA.jpg",
    "https://i.imgur.com/JXe9eDf.jpg",
    "https://i.imgur.com/3Vv4iKQ.jpg",
    "https://i.imgur.com/5B7Tq6m.jpg",
    "https://i.imgur.com/7sK4vJz.jpg",
]

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def get_main_keyboard(user_id: int = None):
    keyboard = [
        [
            InlineKeyboardButton(text="👋 Приветствие", callback_data="greet"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        ],
        [
            InlineKeyboardButton(text="🎲 Случайное число", callback_data="random_number"),
            InlineKeyboardButton(text="🎭 Случайный мем", callback_data="random_meme"),
        ],
        [
            InlineKeyboardButton(text="🎮 Начать игру", callback_data="start_game"),
        ],
        [
            InlineKeyboardButton(text="🗞 Habr", callback_data="latest_habr"),
            InlineKeyboardButton(text="🔥 Топ-3 Habr", callback_data="top3_habr"),
        ],
        [
            InlineKeyboardButton(text="📰 Свежие новости", callback_data="news_menu"),
            InlineKeyboardButton(text="📅 Дата и время", callback_data="datetime"),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        ]
    ]

    if user_id == OWNER_ID:
        keyboard.append([
            InlineKeyboardButton(text="🔒 Секрет", callback_data="secret")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_news_sources_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Lenta.ru", callback_data="news_lenta"),
            InlineKeyboardButton(text="📰 Meduza", callback_data="news_meduza"),
        ],
        [
            InlineKeyboardButton(text="🌍 BBC", callback_data="news_bbc"),
            InlineKeyboardButton(text="🌐 Reuters", callback_data="news_reuters"),
        ],
        [
            InlineKeyboardButton(text="💡 VC.ru", callback_data="news_vc"),
            InlineKeyboardButton(text="👨‍💻 TProger", callback_data="news_tproger"),
        ],
        [
            InlineKeyboardButton(text="📰 RIA", callback_data="news_ria"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"),
        ]
    ])


def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in str(text))


# === ПАРСИНГ СТАТЕЙ И НОВОСТЕЙ ===

# --- Habr (оставляем как есть) ---
def get_latest_habr_article():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://habr.com/ru/articles/", headers=headers, timeout=10)
        response.raise_for_status()
        if "captcha" in response.url or "cloudflare" in response.text.lower():
            return None
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.find("div", {"data-test-id": "article-snippet"})
        if not article: return None
        title_tag = article.find("a", {"data-test-id": "article-title-link"})
        if not title_tag: return None
        title = title_tag.get_text(strip=True)
        link = "https://habr.com" + title_tag["href"] if title_tag["href"].startswith("/") else title_tag["href"]
        author_tag = article.find("a", {"data-test-id": "article-author-link"})
        author = author_tag.get_text(strip=True) if author_tag else "Аноним"
        lead_tag = article.find("p", {"data-test-id": "article-lead"})
        lead = (lead_tag.get_text(strip=True) if lead_tag else "")[:300]
        if lead_tag and len(lead_tag.get_text()) > 300: lead += "..."
        time_tag = article.find("time")
        published = time_tag["datetime"][:10] if time_tag and time_tag.get("datetime") else ""
        img_tag = article.find("img")
        image_url = None
        if img_tag and img_tag.get("src"):
            image_url = img_tag["src"]
            if image_url.startswith("//"): image_url = "https:" + image_url
            elif image_url.startswith("/"): image_url = "https://habr.com" + image_url
        return {"title": title, "link": link, "author": author, "lead": lead, "published": published, "image_url": image_url}
    except Exception as e:
        logging.error(f"Ошибка Habr: {e}")
        return None


def get_top3_habr_articles():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://habr.com/ru/articles/", headers=headers, timeout=10)
        response.raise_for_status()
        if "captcha" in response.url or "cloudflare" in response.text.lower():
            return None
        soup = BeautifulSoup(response.text, "lxml")
        articles = soup.find_all("div", {"data-test-id": "article-snippet"}, limit=3)
        result = []
        for art in articles:
            title_tag = art.find("a", {"data-test-id": "article-title-link"})
            if not title_tag: continue
            title = title_tag.get_text(strip=True)
            link = "https://habr.com" + title_tag["href"] if title_tag["href"].startswith("/") else title_tag["href"]
            img_tag = art.find("img")
            image_url = None
            if img_tag and img_tag.get("src"):
                image_url = img_tag["src"]
                if image_url.startswith("//"): image_url = "https:" + image_url
                elif image_url.startswith("/"): image_url = "https://habr.com" + image_url
            result.append({"title": title, "link": link, "image_url": image_url})
        return result
    except Exception as e:
        logging.error(f"Ошибка топ-3 Habr: {e}")
        return None


# --- Новые источники ---

def get_vc_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://vc.ru/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("div.l-entry__content a") or soup.select_one("a.l-card")
        if not article: return None
        title = article.get_text(strip=True)
        link = article["href"] if article.has_attr("href") else ""
        if link.startswith("/"): link = "https://vc.ru" + link
        return {"title": title, "link": link, "source": "VC.ru"}
    except Exception as e:
        logging.error(f"Ошибка VC.ru: {e}")
        return None


def get_tproger_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://tproger.ru/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("h2.entry-title a") or soup.select_one("a.post-title")
        if not article: return None
        title = article.get_text(strip=True)
        link = article["href"]
        return {"title": title, "link": link, "source": "TProger"}
    except Exception as e:
        logging.error(f"Ошибка TProger: {e}")
        return None


def get_ria_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://ria.ru/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a.cell-list__item-link") or soup.select_one("a[slot='text']")
        if not article: return None
        title = article.get_text(strip=True)
        link = article["href"]
        if link.startswith("/"): link = "https://ria.ru" + link
        return {"title": title, "link": link, "source": "РИА Новости"}
    except Exception as e:
        logging.error(f"Ошибка RIA: {e}")
        return None


def get_reuters_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://www.reuters.com/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a[data-testid='Heading']") or soup.select_one("a[href^='/world/']")
        if not article: return None
        title = article.get_text(strip=True)
        link = article["href"]
        if link.startswith("/"): link = "https://www.reuters.com" + link
        return {"title": title, "link": link, "source": "Reuters"}
    except Exception as e:
        logging.error(f"Ошибка Reuters: {e}")
        return None


# --- Старые источники (оставляем) ---
def get_lenta_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://lenta.ru/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("div.top-item a") or soup.select_one("div.item a")
        if not article: return None
        title = article.get_text(strip=True)
        link = "https://lenta.ru" + article["href"] if article["href"].startswith("/") else article["href"]
        return {"title": title, "link": link, "source": "Lenta.ru"}
    except Exception as e:
        logging.error(f"Ошибка Lenta.ru: {e}")
        return None


def get_meduza_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://meduza.io/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a[rel='noopener']") or soup.select_one("a.SimpleBlock-article__link")
        if not article: return None
        title = article.get_text(strip=True)
        link = "https://meduza.io" + article["href"] if article["href"].startswith("/") else article["href"]
        return {"title": title, "link": link, "source": "Meduza"}
    except Exception as e:
        logging.error(f"Ошибка Meduza: {e}")
        return None


def get_bbc_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://www.bbc.com/news", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a[data-testid='internal-link'] h2")
        if not article: article = soup.select_one("a h3")
        if not article or not article.parent: return None
        title = article.get_text(strip=True)
        link = article.parent["href"]
        if link.startswith("/"): link = "https://www.bbc.com" + link
        return {"title": title, "link": link, "source": "BBC News"}
    except Exception as e:
        logging.error(f"Ошибка BBC: {e}")
        return None


# === ОБРАБОТЧИКИ ===

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    welcome_text = (
        f"Привет, {message.from_user.full_name}!\n"
        f"Я — умный бот с новостями, мемами и играми!\n\n"
        f"Выберите действие:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id))


@dp.message(Command("menu"))
async def send_menu(message: types.Message):
    await message.answer("Меню:", reply_markup=get_main_keyboard(message.from_user.id))


@dp.callback_query(lambda c: c.data == 'help')
async def process_help_callback(callback: types.CallbackQuery):
    await callback.answer()
    help_text = (
        "🔹 **Приветствие** — поздороваться\n"
        "🔹 **Случайное число** — от 1 до 100\n"
        "🔹 **🎭 Мем** — получить мем\n"
        "🔹 **Игра** — угадай число\n"
        "🔹 **Habr** — свежие IT-статьи\n"
        "🔹 **📰 Новости** — Lenta, Meduza, BBC, Reuters,\n"
        "   VC.ru, TProger, RIA\n"
        "🔹 **Дата/время** — текущие\n"
        "🔹 **Статистика** — по играм"
    )
    if callback.from_user.id == OWNER_ID:
        help_text += "\n🔹 **Секрет** — для владельца"
    try:
        await callback.message.edit_text(help_text, reply_markup=get_main_keyboard(callback.from_user.id))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e): raise


# ... остальные обработчики (greet, random_number, random_meme, start_game, latest_habr, top3_habr, datetime, stats, secret, handle_message) остаются БЕЗ ИЗМЕНЕНИЙ ...

# === Обновлённый обработчик новостей ===

@dp.callback_query(lambda c: c.data == 'news_menu')
async def process_news_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите источник:", reply_markup=get_news_sources_keyboard())


@dp.callback_query(lambda c: c.data.startswith('news_'))
async def process_news_callback(callback: types.CallbackQuery):
    source = callback.data
    await callback.answer("Загружаю...", show_alert=False)

    article = None
    if source == "news_lenta": article = get_lenta_news()
    elif source == "news_meduza": article = get_meduza_news()
    elif source == "news_bbc": article = get_bbc_news()
    elif source == "news_reuters": article = get_reuters_news()
    elif source == "news_vc": article = get_vc_news()
    elif source == "news_tproger": article = get_tproger_news()
    elif source == "news_ria": article = get_ria_news()

    if not article:
        await callback.message.edit_text(
            "❌ Не удалось загрузить. Попробуйте позже.",
            reply_markup=get_news_sources_keyboard()
        )
        return

    title = escape_markdown_v2(article["title"])
    link = article["link"]
    source_name = article["source"]
    caption = f"📰 **{source_name}**\n\n[{title}]({link})"

    try:
        await callback.message.edit_text(caption, parse_mode="MarkdownV2", reply_markup=get_news_sources_keyboard())
    except TelegramBadRequest:
        fallback = f"📰 {source_name}\n\n{article['title']}\n\nЧитать: {link}"
        await callback.message.edit_text(fallback, reply_markup=get_news_sources_keyboard())


@dp.callback_query(lambda c: c.data == 'back_to_main')
async def process_back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите действие:", reply_markup=get_main_keyboard(callback.from_user.id))


# === ОСТАЛЬНЫЕ ОБРАБОТЧИКИ БЕЗ ИЗМЕНЕНИЙ ===
# (greet, random_number, random_meme, start_game, latest_habr, top3_habr, datetime, stats, secret, handle_message)
# → они уже в вашем коде, просто оставьте их как есть!

# Для краткости не дублирую их здесь, но в финальном файле они ДОЛЖНЫ БЫТЬ!

# === ЗАПУСК ===

async def main():
    logging.info("✅ Бот с расширенными новостями запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())