import os
import re
import time
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SKYLOTS_EMAIL = os.environ.get("SKYLOTS_EMAIL", "")
SKYLOTS_PASSWORD = os.environ.get("SKYLOTS_PASSWORD", "")
BASE_URL = "https://skylots.org"

CATEGORY_IDS = {
    "laptops":   "4913",   # Ноутбуки
    "computers": "4891",   # Комп'ютери та комплектуючі
    "ram":       "5015",   # Оперативна пам'ять
    "ssd":       "5020",   # SSD накопичувачі
    "gpu":       "5010",   # Відеокарти
    "chargers":  "5035",   # Блоки живлення для ноутбуків
    "other":     "4891",   # Комп'ютери та комплектуючі
}


class SkyLotsClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "uk-UA,uk;q=0.9,ru;q=0.8",
        })
        self.logged_in = False

    def login(self):
        """Логін на SkyLots"""
        try:
            # Отримуємо сторінку логіну для cookies
            resp = self.session.get(f"{BASE_URL}/login.php", timeout=15)

            # Парсимо CSRF токен якщо є
            soup = BeautifulSoup(resp.text, "html.parser")
            token_input = soup.find("input", {"name": "token"})
            token = token_input["value"] if token_input else ""

            # Логінимось
            data = {
                "login": SKYLOTS_EMAIL,
                "password": SKYLOTS_PASSWORD,
                "token": token,
                "remember": "1",
            }
            resp = self.session.post(f"{BASE_URL}/login.php", data=data, timeout=15, allow_redirects=True)

            # Перевіряємо чи залогінились
            if "cabinet" in resp.url or "Вихід" in resp.text or "Кабінет" in resp.text:
                self.logged_in = True
                logger.info("SkyLots: успішний логін")
                return True
            else:
                logger.error("SkyLots: помилка логіну")
                return False
        except Exception as e:
            logger.error(f"SkyLots login error: {e}")
            return False

    def upload_photo(self, photo_path: str) -> str:
        """Завантажує фото і повертає URL або ID"""
        try:
            with open(photo_path, "rb") as f:
                resp = self.session.post(
                    f"{BASE_URL}/ajax/upload_photo.php",
                    files={"file": (os.path.basename(photo_path), f, "image/jpeg")},
                    timeout=30,
                )
            data = resp.json()
            return data.get("photo_id", "") or data.get("id", "")
        except Exception as e:
            logger.error(f"Photo upload error: {e}")
            return ""

    def post_lot(self, title: str, price: float, description: str,
                 category: str, photo_paths: list) -> dict:
        """Виставляє лот на SkyLots"""
        try:
            if not self.logged_in:
                if not self.login():
                    return {"success": False, "error": "Не вдалось залогінитись"}

            # Отримуємо форму виставлення лота
            resp = self.session.get(f"{BASE_URL}/sell.php", timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Збираємо всі приховані поля форми
            form_data = {}
            for inp in soup.find_all("input", {"type": "hidden"}):
                if inp.get("name"):
                    form_data[inp["name"]] = inp.get("value", "")

            # Завантажуємо фото
            photo_ids = []
            for path in photo_paths[:5]:
                pid = self.upload_photo(path)
                if pid:
                    photo_ids.append(pid)

            cat_id = CATEGORY_IDS.get(category, CATEGORY_IDS["other"])

            # Заповнюємо форму лота
            form_data.update({
                "lot_name": title,
                "lot_price": str(int(price)),
                "lot_description": description,
                "lot_category": cat_id,
                "lot_type": "2",          # Купити зараз
                "lot_count": "1",
                "lot_duration": "30",     # 30 днів
                "lot_location": "Чернівці",
                "delivery_nova_poshta": "1",
                "payment_fop": "1",
            })

            # Додаємо фото ID
            for i, pid in enumerate(photo_ids):
                form_data[f"photo[{i}]"] = pid

            # Відправляємо форму
            resp = self.session.post(
                f"{BASE_URL}/sell.php",
                data=form_data,
                timeout=30,
                allow_redirects=True,
            )

            # Перевіряємо результат
            if "lot" in resp.url or resp.status_code == 200:
                # Шукаємо номер лота у відповіді
                lot_id_match = re.search(r'/lot/(\d+)', resp.url + resp.text)
                lot_id = lot_id_match.group(1) if lot_id_match else "невідомо"
                return {
                    "success": True,
                    "lot_id": lot_id,
                    "url": f"{BASE_URL}/lot/{lot_id}" if lot_id != "невідомо" else BASE_URL,
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}

        except Exception as e:
            logger.error(f"Post lot error: {e}")
            return {"success": False, "error": str(e)}


# Глобальний клієнт
_client = None


def get_client() -> SkyLotsClient:
    global _client
    if _client is None:
        _client = SkyLotsClient()
    return _client


def post_lot_to_skylots(title: str, price: float, description: str,
                         category: str, photo_paths: list) -> dict:
    client = get_client()
    if not client.logged_in:
        client.login()
    return client.post_lot(title, price, description, category, photo_paths)
