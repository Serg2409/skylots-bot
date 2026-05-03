import os
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORY_HINTS = {
    "laptops": "ноутбук",
    "computers": "комп'ютерна техніка",
    "ram": "оперативна пам'ять",
    "ssd": "SSD накопичувач",
    "gpu": "відеокарта",
    "chargers": "зарядний пристрій для ноутбука",
    "other": "комп'ютерна техніка",
}


def generate_description(title: str, category: str, user_notes: str = "") -> str:
    """Генерує опис товару через Groq AI"""

    if not GROQ_API_KEY:
        return _fallback_description(title, category, user_notes)

    category_hint = CATEGORY_HINTS.get(category, "товар")

    notes_part = f"\nДодаткова інформація від продавця: {user_notes}" if user_notes else ""

    prompt = f"""Ти помічник продавця на українському аукціоні SkyLots. 
Напиши привабливий і чесний опис товару для оголошення українською мовою.

Товар: {title}
Категорія: {category_hint}{notes_part}

Вимоги до опису:
- Довжина: 3-5 речень
- Мова: українська
- Стиль: чіткий, інформативний, без зайвих слів
- Вкажи що товар у гарному стані (якщо не вказано інше)
- НЕ вигадуй характеристики яких немає в назві
- В кінці завжди додай: "📍 Чернівці | 🚚 Доставка Новою Поштою по всій Україні | 💳 Оплата на рахунок ФОП"

Відповідай ТІЛЬКИ текстом опису, без зайвих коментарів."""

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.7,
            },
            timeout=15,
        )
        data = response.json()
        description = data["choices"][0]["message"]["content"].strip()
        return description
    except Exception as e:
        print(f"Groq error: {e}")
        return _fallback_description(title, category, user_notes)


def _fallback_description(title: str, category: str, user_notes: str = "") -> str:
    """Базовий опис якщо AI недоступний"""
    category_hint = CATEGORY_HINTS.get(category, "товар")
    notes = f" {user_notes}" if user_notes else ""
    return (
        f"{title} у гарному робочому стані.{notes} "
        f"Категорія: {category_hint}. "
        f"📍 Чернівці | 🚚 Доставка Новою Поштою по всій Україні | 💳 Оплата на рахунок ФОП"
    )
