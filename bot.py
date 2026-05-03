import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from yml_generator import add_lot, generate_yml, load_lots, delete_lot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8782026591:AAFeDTVD6foeJm8_t8ITMd3w8WIsU5JUHuU")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")  # заповниш після першого запуску

CATEGORIES = {
    "laptops": "💻 Ноутбуки",
    "computers": "🖥️ Комп'ютерна техніка",
    "ram": "🧠 Оперативна пам'ять",
    "ssd": "💾 SSD накопичувачі",
    "gpu": "🎮 Відеокарти",
    "chargers": "🔌 Зарядні пристрої",
    "other": "📦 Інше",
}

# Стани розмови
CATEGORY, TITLE, PRICE, DESCRIPTION, PHOTO = range(5)


def is_owner(update: Update) -> bool:
    if not OWNER_CHAT_ID:
        return True  # якщо не задано — дозволяємо всім (для першого запуску)
    return str(update.effective_chat.id) == str(OWNER_CHAT_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Привіт! Я бот для виставлення лотів на SkyLots.\n\n"
        f"Твій Chat ID: `{chat_id}`\n\n"
        f"Команди:\n"
        f"/newlot — виставити новий лот\n"
        f"/mylots — переглянути активні лоти\n"
        f"/deletelot — видалити лот\n"
        f"/yml — отримати посилання на YML файл",
        parse_mode="Markdown"
    )


async def new_lot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ Немає доступу.")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["photos"] = []

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"cat_{key}")]
        for key, name in CATEGORIES.items()
    ]
    await update.message.reply_text(
        "📂 Обери категорію товару:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CATEGORY


async def got_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat_key = query.data.replace("cat_", "")
    context.user_data["category"] = cat_key
    context.user_data["category_name"] = CATEGORIES[cat_key]

    await query.edit_message_text(
        f"✅ Категорія: {CATEGORIES[cat_key]}\n\n"
        f"📝 Введи назву товару:\n"
        f"_(наприклад: Ноутбук Lenovo IdeaPad 15 i5/8GB/256SSD)_",
        parse_mode="Markdown"
    )
    return TITLE


async def got_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text

    await update.message.reply_text(
        f"✅ Назва: {update.message.text}\n\n"
        f"💰 Введи ціну в гривнях (тільки число):\n"
        f"_(наприклад: 15000)_",
        parse_mode="Markdown"
    )
    return PRICE


async def got_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_text = update.message.text.replace(" ", "").replace(",", ".")
        price = float(price_text)
        if price <= 0:
            raise ValueError
        context.user_data["price"] = price
    except ValueError:
        await update.message.reply_text("❌ Введи коректну ціну, наприклад: `15000`", parse_mode="Markdown")
        return PRICE

    await update.message.reply_text(
        f"✅ Ціна: {price:.0f} грн\n\n"
        f"📄 Введи опис товару:\n"
        f"_(стан, комплектація, особливості — або напиши /skip щоб пропустити)_",
        parse_mode="Markdown"
    )
    return DESCRIPTION


async def got_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text(
        "✅ Опис збережено\n\n"
        "📷 Надішли фото товару (до 5 штук)\n"
        "Коли закінчиш — натисни /done"
    )
    return PHOTO


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = ""
    await update.message.reply_text(
        "✅ Опис пропущено\n\n"
        "📷 Надішли фото товару (до 5 штук)\n"
        "Коли закінчиш — натисни /done"
    )
    return PHOTO


async def got_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data.get("photos", [])

    if len(photos) >= 5:
        await update.message.reply_text("⚠️ Максимум 5 фото. Натисни /done")
        return PHOTO

    photo = update.message.photo[-1]
    file = await photo.get_file()

    # Зберігаємо фото локально
    os.makedirs("photos", exist_ok=True)
    filename = f"photos/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    await file.download_to_drive(filename)
    photos.append(filename)
    context.user_data["photos"] = photos

    await update.message.reply_text(
        f"✅ Фото {len(photos)}/5 додано\n"
        f"Надішли ще або натисни /done"
    )
    return PHOTO


async def photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data.get("photos", [])

    if not photos:
        await update.message.reply_text("⚠️ Додай хоча б одне фото!")
        return PHOTO

    # Зберігаємо лот
    lot = {
        "id": str(int(datetime.now().timestamp())),
        "title": context.user_data["title"],
        "category": context.user_data["category"],
        "category_name": context.user_data["category_name"],
        "price": context.user_data["price"],
        "description": context.user_data.get("description", ""),
        "photos": photos,
        "created": datetime.now().isoformat(),
    }

    add_lot(lot)
    generate_yml()

    await update.message.reply_text(
        f"🎉 Лот додано!\n\n"
        f"📦 *{lot['title']}*\n"
        f"💰 {lot['price']:.0f} грн\n"
        f"📂 {lot['category_name']}\n"
        f"🆔 ID: `{lot['id']}`\n\n"
        f"SkyLots підтягне лот при наступній синхронізації (раз на добу)\n\n"
        f"/newlot — виставити ще один",
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END


async def my_lots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    lots = load_lots()
    if not lots:
        await update.message.reply_text("📭 Активних лотів немає.\n/newlot — додати перший")
        return

    text = f"📋 *Активні лоти ({len(lots)}):*\n\n"
    for lot in lots:
        text += f"🆔 `{lot['id']}`\n"
        text += f"📦 {lot['title']}\n"
        text += f"💰 {lot['price']:.0f} грн\n"
        text += f"📂 {lot['category_name']}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def delete_lot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    lots = load_lots()
    if not lots:
        await update.message.reply_text("📭 Немає лотів для видалення.")
        return

    keyboard = [
        [InlineKeyboardButton(f"❌ {lot['title'][:30]}", callback_data=f"del_{lot['id']}")]
        for lot in lots
    ]
    await update.message.reply_text(
        "Який лот видалити?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lot_id = query.data.replace("del_", "")
    lots = load_lots()
    lot = next((l for l in lots if l["id"] == lot_id), None)

    if lot:
        delete_lot(lot_id)
        generate_yml()
        await query.edit_message_text(f"✅ Лот *{lot['title']}* видалено.", parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ Лот не знайдено.")


async def get_yml_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if base_url:
        yml_url = f"https://{base_url}/feed.yml"
    else:
        yml_url = "http://localhost:5000/feed.yml"

    await update.message.reply_text(
        f"🔗 Посилання на YML файл:\n`{yml_url}`\n\n"
        f"Вкажи це посилання в SkyLots → Синхронізація",
        parse_mode="Markdown"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Скасовано. /newlot — почати знову.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("newlot", new_lot)],
        states={
            CATEGORY: [CallbackQueryHandler(got_category, pattern="^cat_")],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_title)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_price)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_description),
                CommandHandler("skip", skip_description),
            ],
            PHOTO: [
                MessageHandler(filters.PHOTO, got_photo),
                CommandHandler("done", photos_done),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mylots", my_lots))
    app.add_handler(CommandHandler("deletelot", delete_lot_start))
    app.add_handler(CommandHandler("yml", get_yml_link))
    app.add_handler(CallbackQueryHandler(confirm_delete, pattern="^del_"))
    app.add_handler(conv)

    logger.info("Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
