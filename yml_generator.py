import json
import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

LOTS_FILE = "lots.json"
YML_FILE = "feed.yml"
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "localhost:5000")

CATEGORY_MAP = {
    "laptops":   {"id": "1", "name": "Ноутбуки"},
    "computers": {"id": "2", "name": "Комп'ютерна техніка"},
    "ram":       {"id": "3", "name": "Оперативна пам'ять"},
    "ssd":       {"id": "4", "name": "SSD накопичувачі"},
    "gpu":       {"id": "5", "name": "Відеокарти"},
    "chargers":  {"id": "6", "name": "Зарядні пристрої для ноутбуків"},
    "other":     {"id": "7", "name": "Комп'ютерна техніка та електроніка"},
}


def load_lots():
    if not os.path.exists(LOTS_FILE):
        return []
    with open(LOTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_lots(lots):
    with open(LOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(lots, f, ensure_ascii=False, indent=2)


def add_lot(lot):
    lots = load_lots()
    lots.append(lot)
    save_lots(lots)


def delete_lot(lot_id):
    lots = load_lots()
    lots = [l for l in lots if l["id"] != lot_id]
    save_lots(lots)


def generate_yml():
    lots = load_lots()
    protocol = "https" if "railway" in BASE_URL else "http"
    base = f"{protocol}://{BASE_URL}"

    root = Element("yml_catalog")
    root.set("date", datetime.now().strftime("%Y-%m-%d %H:%M"))

    shop = SubElement(root, "shop")

    SubElement(shop, "name").text = "Комп'ютерна техніка Чернівці"
    SubElement(shop, "company").text = "serg2409"
    SubElement(shop, "url").text = "https://skylots.org"

    # Валюта
    currencies = SubElement(shop, "currencies")
    currency = SubElement(currencies, "currency")
    currency.set("id", "UAH")
    currency.set("rate", "1")

    # Категорії
    categories = SubElement(shop, "categories")
    for key, cat in CATEGORY_MAP.items():
        category = SubElement(categories, "category")
        category.set("id", cat["id"])
        category.text = cat["name"]

    # Лоти
    offers = SubElement(shop, "offers")
    for lot in lots:
        offer = SubElement(offers, "offer")
        offer.set("id", lot["id"])
        offer.set("available", "true")
        offer.set("type", "vendor.model")

        SubElement(offer, "name").text = lot["title"]
        SubElement(offer, "price").text = str(int(lot["price"]))
        SubElement(offer, "currencyId").text = "UAH"

        cat_info = CATEGORY_MAP.get(lot["category"], CATEGORY_MAP["other"])
        SubElement(offer, "categoryId").text = cat_info["id"]

        # Фото
        for photo_path in lot.get("photos", []):
            filename = os.path.basename(photo_path)
            SubElement(offer, "picture").text = f"{base}/photos/{filename}"

        # Опис
        description_parts = []
        if lot.get("description"):
            description_parts.append(lot["description"])

        description_parts.append("📍 Місто: Чернівці")
        description_parts.append("🚚 Доставка: Нова Пошта по Україні")
        description_parts.append("💳 Оплата: на рахунок ФОП")

        SubElement(offer, "description").text = "\n".join(description_parts)

        SubElement(offer, "country_of_origin").text = "Не вказано"

    # Красивий XML
    xml_str = minidom.parseString(tostring(root, encoding="unicode")).toprettyxml(indent="  ")
    # Прибираємо зайвий рядок <?xml...?> бо додамо свій
    lines = xml_str.split("\n")
    clean_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                   '<!DOCTYPE yml_catalog SYSTEM "shops.dtd">'] + lines[1:]
    result = "\n".join(clean_lines)

    with open(YML_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    return YML_FILE
