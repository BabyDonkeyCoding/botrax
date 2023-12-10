"""Botrax logging module."""
import logging
import os
import pathlib
from datetime import datetime as dt

import config

MAIN_LOGGER = None
CHAT_LOGGER = None
DEBUG_LOGGER = None
MESSAGE_LOGGER = None


def __setup_logger(name, log_file, level=logging.INFO):
    #
    handler = logging.FileHandler(
        filename=str(pathlib.Path().resolve())
        + os.sep
        + "log"
        + os.sep
        + log_file
        + "_"
        + str(dt.now().date()).replace(" ", "_")
        + ".log"
    )
    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S"
    )
    # add formatter to ch
    handler.setFormatter(formatter)
    #
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    # start loggers with init log message
    logger.debug(
        "New session started for user: %s", str(config.PLAYER_DATA["username"])
    )
    return logger


def init(log_level=logging.INFO):
    """Set up the loggers"""
    global MAIN_LOGGER, CHAT_LOGGER, DEBUG_LOGGER, MESSAGE_LOGGER
    #
    dbg_msg = "]]]Starting new session[[["
    # first file logger
    if not MAIN_LOGGER:
        MAIN_LOGGER = __setup_logger(
            "Main Logger", str(config.PLAYER_DATA["username"]) + "_main", log_level
        )
        #
        MAIN_LOGGER.info(dbg_msg)
    if not CHAT_LOGGER:
        # second file logger
        CHAT_LOGGER = __setup_logger(
            "Chat_logger", str(config.PLAYER_DATA["username"]) + "_chat", log_level
        )
        CHAT_LOGGER.info(dbg_msg)
    if not DEBUG_LOGGER:
        # second file logger
        DEBUG_LOGGER = __setup_logger(
            "Debug_logger", str(config.PLAYER_DATA["username"]) + "_debug", log_level
        )
        DEBUG_LOGGER.info(dbg_msg)
    if not MESSAGE_LOGGER:
        # second file logger
        MESSAGE_LOGGER = __setup_logger(
            "Message_logger",
            str(config.PLAYER_DATA["username"]) + "_messages",
            log_level,
        )
        MESSAGE_LOGGER.info(dbg_msg)
