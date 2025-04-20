import logging
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler
import os

log_path = os.path.join("logs", "bot.log")
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

log_handler = RotatingFileHandler(f"modules/logger/{log_path}", maxBytes=1_000_000, backupCount=5)

formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_handler.setFormatter(formatter)

logger.addHandler(log_handler)

