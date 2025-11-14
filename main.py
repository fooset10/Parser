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
user_games = {}  # {user_id: secret_number}
game_stats = {"total_games": 0, "total_guesses": 0}

# === СПИСОК МЕМОВ (опционально, можно удалить если не нужно) ===
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
            InlineKeyboardButton(text="🗞 Последняя статья Habr", callback_data="latest_habr"),
            InlineKeyboardButton(text="🔥 Топ-3 статьи Habr", callback_data="top3_habr"),
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
            InlineKeyboardButton(text="🔒 Секрет (только для владельца)", callback_data="secret")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_news_sources_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Lenta.ru", callback_data="news_lenta"),
            InlineKeyboardButton(text="📰 Meduza.io", callback_data="news_meduza"),
        ],
        [
            InlineKeyboardButton(text="🌍 BBC News", callback_data="news_bbc"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"),
        ]
    ])


def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in str(text))


# === ПАРСИНГ НОВОСТЕЙ ===

def get_latest_habr_article():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get("https://habr.com/ru/articles/", headers=headers, timeout=10)
        response.raise_for_status()
        if "captcha" in response.url or "cloudflare" in response.text.lower():
            return None
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.find("div", {"data-test-id": "article-snippet"})
        if not article:
            return None

        title_tag = article.find("a", {"data-test-id": "article-title-link"})
        if not title_tag:
            return None
        title = title_tag.get_text(strip=True)
        link = "https://habr.com" + title_tag["href"] if title_tag["href"].startswith("/") else title_tag["href"]

        author_tag = article.find("a", {"data-test-id": "article-author-link"})
        author = author_tag.get_text(strip=True) if author_tag else "Аноним"

        lead_tag = article.find("p", {"data-test-id": "article-lead"})
        lead = (lead_tag.get_text(strip=True) if lead_tag else "")[:300]
        if lead_tag and len(lead_tag.get_text()) > 300:
            lead += "..."

        time_tag = article.find("time")
        published = time_tag["datetime"][:10] if time_tag and time_tag.get("datetime") else ""

        img_tag = article.find("img")
        image_url = None
        if img_tag and img_tag.get("src"):
            image_url = img_tag["src"]
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            elif image_url.startswith("/"):
                image_url = "https://habr.com" + image_url

        return {
            "title": title,
            "link": link,
            "author": author,
            "lead": lead,
            "published": published,
            "image_url": image_url
        }
    except Exception as e:
        logging.error(f"Ошибка парсинга Habr: {e}")
        return None


def get_top3_habr_articles():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get("https://habr.com/ru/articles/", headers=headers, timeout=10)
        response.raise_for_status()
        if "captcha" in response.url or "cloudflare" in response.text.lower():
            return None
        soup = BeautifulSoup(response.text, "lxml")
        articles = soup.find_all("div", {"data-test-id": "article-snippet"}, limit=3)
        result = []
        for art in articles:
            title_tag = art.find("a", {"data-test-id": "article-title-link"})
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = "https://habr.com" + title_tag["href"] if title_tag["href"].startswith("/") else title_tag["href"]

            img_tag = art.find("img")
            image_url = None
            if img_tag and img_tag.get("src"):
                image_url = img_tag["src"]
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = "https://habr.com" + image_url

            result.append({
                "title": title,
                "link": link,
                "image_url": image_url
            })
        return result
    except Exception as e:
        logging.error(f"Ошибка парсинга топ-3 Habr: {e}")
        return None


def get_lenta_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://lenta.ru/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("div.top-item a") or soup.select_one("div.item a")
        if not article:
            return None
        title = article.get_text(strip=True)
        link = "https://lenta.ru" + article["href"] if article["href"].startswith("/") else article["href"]
        return {"title": title, "link": link, "source": "Lenta.ru"}
    except Exception as e:
        logging.error(f"Ошибка парсинга Lenta.ru: {e}")
        return None


def get_meduza_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://meduza.io/", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a[rel='noopener']") or soup.select_one("a.SimpleBlock-article__link")
        if not article:
            return None
        title = article.get_text(strip=True)
        link = "https://meduza.io" + article["href"] if article["href"].startswith("/") else article["href"]
        return {"title": title, "link": link, "source": "Meduza.io"}
    except Exception as e:
        logging.error(f"Ошибка парсинга Meduza.io: {e}")
        return None


def get_bbc_news():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get("https://www.bbc.com/news", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        article = soup.select_one("a[data-testid='internal-link'] h2")
        if not article:
            article = soup.select_one("a h3")
        if not article or not article.parent:
            return None
        title = article.get_text(strip=True)
        link = article.parent["href"]
        if link.startswith("/"):
            link = "https://www.bbc.com" + link
        return {"title": title, "link": link, "source": "BBC News"}
    except Exception as e:
        logging.error(f"Ошибка парсинга BBC News: {e}")
        return None


# === ОБРАБОТЧИКИ ===

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    welcome_text = (
        f"Привет, {message.from_user.full_name}!\n"
        f"Я продвинутый EchoBot с играми, мемами, новостями и секретами!\n\n"
        f"Выберите действие ниже:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id))


@dp.message(Command("menu"))
async def send_menu(message: types.Message):
    await message.answer("Меню:", reply_markup=get_main_keyboard(message.from_user.id))


@dp.callback_query(lambda c: c.data == 'greet')
async def process_greet_callback(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            f"👋 Привет, {callback.from_user.full_name}!",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'help')
async def process_help_callback(callback: types.CallbackQuery):
    await callback.answer()
    help_text = (
        "🔹 **Приветствие** — поздороваться\n"
        "🔹 **Случайное число** — от 1 до 100\n"
        "🔹 **🎭 Случайный мем** — получить мем\n"
        "🔹 **Начать игру** — угадай число\n"
        "🔹 **Последняя статья** — свежая новость с Habr\n"
        "🔹 **Топ-3 статьи** — самые популярные\n"
        "🔹 **📰 Свежие новости** — с Lenta.ru, Meduza.io, BBC\n"
        "🔹 **Дата и время** — текущие\n"
        "🔹 **Статистика** — общая статистика\n"
    )
    if callback.from_user.id == OWNER_ID:
        help_text += "🔹 **Секрет** — только для владельца\n"
    try:
        await callback.message.edit_text(help_text, reply_markup=get_main_keyboard(callback.from_user.id))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'random_number')
async def process_random_number_callback(callback: types.CallbackQuery):
    await callback.answer()
    n = random.randint(1, 100)
    try:
        await callback.message.edit_text(
            f"🎲 Ваше число: **{n}**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'random_meme')
async def process_random_meme_callback(callback: types.CallbackQuery):
    await callback.answer("Загружаю мем...", show_alert=False)
    meme_url = random.choice(MEME_URLS)
    try:
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=meme_url,
            caption="🎭 Случайный мем для тебя!",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except TelegramBadRequest as e:
        logging.error(f"Ошибка отправки мема: {e}")
        await callback.message.edit_text(
            "❌ Не удалось загрузить мем. Попробуйте позже.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )


@dp.callback_query(lambda c: c.data == 'start_game')
async def process_start_game_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user_games[user_id] = random.randint(1, 100)
    game_stats["total_games"] += 1
    try:
        await callback.message.edit_text(
            "🔢 Я загадал число от 1 до 100. Напишите вашу догадку:",
            reply_markup=get_main_keyboard(user_id)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'latest_habr')
async def process_latest_habr_callback(callback: types.CallbackQuery):
    await callback.answer("Загружаю статью...", show_alert=False)
    article = get_latest_habr_article()
    if not article:
        await callback.message.edit_text(
            "❌ Не удалось загрузить статью.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        return

    title = escape_markdown_v2(article["title"])
    author = escape_markdown_v2(article["author"])
    lead = escape_markdown_v2(article["lead"])
    pub = article["published"] or "неизвестно"
    link = article["link"]

    caption = (
        f"🗞 **{title}**\n\n"
        f"👤 Автор: {author}\n"
        f"📅 Дата: {pub}\n\n"
        f"💬 {lead}\n\n"
        f"[🔗 Читать]({link})"
    )

    image_url = article.get("image_url")

    try:
        if image_url:
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=image_url,
                caption=caption,
                parse_mode="MarkdownV2",
                reply_markup=get_main_keyboard(callback.from_user.id)
            )
            await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        else:
            await callback.message.edit_text(
                caption,
                parse_mode="MarkdownV2",
                reply_markup=get_main_keyboard(callback.from_user.id)
            )
    except TelegramBadRequest as e:
        logging.warning(f"Ошибка при отправке статьи: {e}")
        fallback = (
            f"🗞 {article['title']}\n"
            f"👤 Автор: {article['author']}\n"
            f"📅 Дата: {pub}\n"
            f"💬 {article['lead']}\n"
            f"Читать: {link}"
        )
        if image_url:
            try:
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=image_url,
                    caption=fallback,
                    reply_markup=get_main_keyboard(callback.from_user.id)
                )
                await bot.delete_message(callback.message.chat.id, callback.message.message_id)
            except Exception:
                await callback.message.edit_text(fallback, reply_markup=get_main_keyboard(callback.from_user.id))
        else:
            await callback.message.edit_text(fallback, reply_markup=get_main_keyboard(callback.from_user.id))


@dp.callback_query(lambda c: c.data == 'top3_habr')
async def process_top3_habr_callback(callback: types.CallbackQuery):
    await callback.answer("Загружаю топ-3...", show_alert=False)
    articles = get_top3_habr_articles()
    if not articles:
        await callback.message.edit_text(
            "❌ Не удалось загрузить топ-3 статей.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        return

    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    for i, art in enumerate(articles, 1):
        title = escape_markdown_v2(art["title"])
        link = art["link"]
        image_url = art.get("image_url")
        caption = f"{i}. [{title}]({link})"

        try:
            if image_url:
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=image_url,
                    caption=caption,
                    parse_mode="MarkdownV2"
                )
            else:
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=caption,
                    parse_mode="MarkdownV2"
                )
        except TelegramBadRequest:
            fallback = f"{i}. {art['title']} — {link}"
            if image_url:
                try:
                    await bot.send_photo(chat_id=callback.message.chat.id, photo=image_url, caption=fallback)
                except:
                    await bot.send_message(callback.message.chat.id, fallback)
            else:
                await bot.send_message(callback.message.chat.id, fallback)

    await bot.send_message(
        callback.message.chat.id,
        "Меню:",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )


@dp.callback_query(lambda c: c.data == 'news_menu')
async def process_news_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выберите новостной источник:",
        reply_markup=get_news_sources_keyboard()
    )


@dp.callback_query(lambda c: c.data.startswith('news_'))
async def process_news_callback(callback: types.CallbackQuery):
    source = callback.data
    await callback.answer("Загружаю новости...", show_alert=False)

    article = None
    if source == "news_lenta":
        article = get_lenta_news()
    elif source == "news_meduza":
        article = get_meduza_news()
    elif source == "news_bbc":
        article = get_bbc_news()

    if not article:
        await callback.message.edit_text(
            "❌ Не удалось загрузить новости. Попробуйте позже.",
            reply_markup=get_news_sources_keyboard()
        )
        return

    title = escape_markdown_v2(article["title"])
    link = article["link"]
    source_name = article["source"]
    caption = f"📰 **{source_name}**\n\n[{title}]({link})"

    try:
        await callback.message.edit_text(
            caption,
            parse_mode="MarkdownV2",
            reply_markup=get_news_sources_keyboard()
        )
    except TelegramBadRequest as e:
        fallback = f"📰 {source_name}\n\n{article['title']}\n\nЧитать: {link}"
        await callback.message.edit_text(fallback, reply_markup=get_news_sources_keyboard())


@dp.callback_query(lambda c: c.data == 'back_to_main')
async def process_back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )


@dp.callback_query(lambda c: c.data == 'datetime')
async def process_datetime_callback(callback: types.CallbackQuery):
    await callback.answer()
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    try:
        await callback.message.edit_text(
            f"📅 Текущая дата и время:\n**{now}**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'stats')
async def process_stats_callback(callback: types.CallbackQuery):
    await callback.answer()
    total = game_stats["total_games"]
    guesses = game_stats["total_guesses"]
    msg = (
        f"📊 **Статистика бота:**\n"
        f"• Всего игр начато: {total}\n"
        f"• Всего попыток: {guesses}\n"
        f"(Статистика общая, не персональная)"
    )
    try:
        await callback.message.edit_text(msg, parse_mode="Markdown",
                                         reply_markup=get_main_keyboard(callback.from_user.id))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.callback_query(lambda c: c.data == 'secret')
async def process_secret_callback(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Эта функция доступна только владельцу!", show_alert=True)
        return
    await callback.answer()
    secret_message = (
        "🔐 **Секретная панель владельца**\n\n"
        "Добро пожаловать, хозяин!\n"
        "Здесь могла быть важная информация 😉"
    )
    try:
        await callback.message.edit_text(
            secret_message,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(OWNER_ID)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in user_games:
        try:
            guess = int(text)
            game_stats["total_guesses"] += 1
        except ValueError:
            await message.reply("🔢 Пожалуйста, введите целое число.")
            return

        secret = user_games[user_id]
        if guess == secret:
            await message.answer("🎉 Поздравляю! Вы угадали число!")
            del user_games[user_id]
        elif guess < secret:
            await message.answer("⬆️ Моё число больше.")
        else:
            await message.answer("⬇️ Моё число меньше.")
        return

    await message.answer(f" Echo: {text}")


# === ЗАПУСК ===

async def main():
    logging.info("✅ Бот с мемами, новостями и статьями запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
