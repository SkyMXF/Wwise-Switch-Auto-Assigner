import logging
import os
from logging.handlers import RotatingFileHandler

import colorlog

LOGGER = logging.getLogger("SwitchAutoAssigner")
CLEAN_LOGGER = logging.getLogger("SwitchAutoAssigner.Clean")
LOG_DIR_PATH = os.path.join("logs", "SwitchAutoAssigner")


def init_logger(level: int = logging.DEBUG):
    logger = LOGGER
    logger.setLevel(level)
    logger.propagate = False

    # rotate file handler
    os.makedirs(LOG_DIR_PATH, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join(LOG_DIR_PATH, "running.log"),
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # color
    handler = logging.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'white',
            'INFO': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # clean logger without extra info
    clean_logger = CLEAN_LOGGER
    clean_logger.setLevel(level)
    clean_logger.propagate = False
    handler = logging.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(message)s",
        log_colors={
            'DEBUG': 'white',
            'INFO': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)
    clean_logger.addHandler(handler)
    clean_logger.addHandler(file_handler)

    # ban inner log
    # logger = logging.getLogger("WampClientAutobahn")
    # logger.setLevel(logging.CRITICAL)
    # logger = logging.getLogger("asyncio")
    # logger.setLevel(logging.WARNING)


def logger_switch_info_level():
    LOGGER.setLevel(logging.INFO)


def logger_switch_debug_level():
    LOGGER.setLevel(logging.DEBUG)


init_logger()
