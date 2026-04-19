import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # INFO+ -> logs/processing.log
    ingestion_handler = logging.FileHandler(LOG_DIR / "processing.log")
    ingestion_handler.setLevel(logging.INFO)
    ingestion_handler.setFormatter(formatter)

    # ERROR+ -> logs/errors.log
    error_handler = logging.FileHandler(LOG_DIR / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(ingestion_handler)
    logger.addHandler(error_handler)
    logger.propagate = False

    return logger