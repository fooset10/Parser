import requests
from bs4 import BeautifulSoup
import time
import random
import sys

def parse_habr_articles(pages=1):
    base_url = "https://habr.com/ru/articles/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []

    for page_num in range(1, pages + 1):
        # Новая схема пагинации: ?page=2, ?page=3 и т.д.
        url = f"{base_url}?page={page_num}"
        print(f"Парсинг страницы: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Проверка на капчу или блокировку
            if "captcha" in response.url.lower() or "cloudflare" in response.text.lower():
                print("⚠️ Обнаружена капча или блокировка. Остановка.")
                break

            soup = BeautifulSoup(response.text, "lxml")

            # Новые классы на ноябрь 2025:
            posts = soup.find_all("div", {"data-test-id": "article-snippet"})

            if not posts:
                print("❗ Нет статей на странице — возможно, достигнут конец или изменилась структура.")
                break

            for post in posts:
                # Заголовок и ссылка
                title_tag = post.find("a", {"data-test-id": "article-title-link"})
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag["href"]
                if link.startswith("/"):
                    link = "https://habr.com" + link

                # Автор
                author_tag = post.find("a", {"data-test-id": "article-author-link"})
                author = author_tag.get_text(strip=True) if author_tag else "Аноним"

                # Дата публикации
                time_tag = post.find("time")
                published = time_tag["datetime"] if time_tag else "Неизвестно"

                articles.append({
                    "title": title,
                    "link": link,
                    "author": author,
                    "published": published
                })

            print(f"✅ Найдено {len(posts)} статей на странице {page_num}")
            # Пауза между запросами
            time.sleep(random.uniform(1.5, 3.0))

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети при запросе {url}: {e}")
            break
        except Exception as e:
            print(f"💥 Неожиданная ошибка: {e}")
            break

    return articles


if __name__ == "__main__":
    print("🚀 Запуск парсера Хабра...")
    data = parse_habr_articles(pages=2)

    if not data:
        print("Нет данных для отображения.")
        sys.exit(1)

    print(f"\n📄 Получено {len(data)} статей. Первые 5:\n")
    for item in data[:5]:
        print(f"📌 {item['title']}")
        print(f"👤 Автор: {item['author']}")
        print(f"📅 Дата: {item['published']}")
        print(f"🔗 Ссылка: {item['link']}\n")
        print("-" * 80)