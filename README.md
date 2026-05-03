# 🤖 SkyLots Telegram Бот

Бот для автоматичного виставлення лотів на SkyLots через Telegram.

## Як користуватись ботом

### Команди:
- `/start` — запуск, показує твій Chat ID
- `/newlot` — виставити новий лот
- `/mylots` — переглянути всі активні лоти
- `/deletelot` — видалити лот
- `/yml` — отримати посилання на YML файл для SkyLots

### Процес виставлення лота:
1. `/newlot` → обираєш категорію (кнопками)
2. Пишеш назву товару
3. Пишеш ціну
4. Пишеш опис (або `/skip`)
5. Надсилаєш фото (до 5 штук)
6. `/done` — лот збережено ✅

## Деплой на Railway

### Крок 1: Завантаж код на GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ТВІЙ_ЮЗЕРНЕЙМ/skylots-bot.git
git push -u origin main
```

### Крок 2: Деплой на Railway
1. Зайди на railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Обери свій репозиторій

### Крок 3: Додай змінні середовища на Railway
У розділі "Variables" додай:
- `BOT_TOKEN` = твій токен від BotFather
- `OWNER_CHAT_ID` = твій Chat ID (дізнаєшся після /start)

### Крок 4: Отримай публічний URL
Railway автоматично дасть URL типу: `skylots-bot.up.railway.app`
Додай його як змінну:
- `RAILWAY_PUBLIC_DOMAIN` = `skylots-bot.up.railway.app`

### Крок 5: Налаштуй синхронізацію на SkyLots
1. Кабінет → Мої продажі → Синхронізація
2. "Створити нову синхронізацію"
3. Вкажи URL: `https://skylots-bot.up.railway.app/feed.yml`
4. Збережи

Готово! Тепер лоти з бота автоматично з'являються на SkyLots 🎉
