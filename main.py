import threading
import logging
import os
from server import run_flask
from bot import main as run_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Запускаємо Flask сервер у фоні
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logging.info("Flask сервер запущено у фоні")
    logging.info("Запускаємо Telegram бота...")
    
    # Запускаємо бота (основний потік)
    run_bot()
