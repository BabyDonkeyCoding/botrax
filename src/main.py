""" Module to initiate the Bot
    """
import argparse
import os
import time

import config
from bot import Bot


def __get_arguments():
    # init variables
    show_gui = True
    # parse argumtens
    parser = argparse.ArgumentParser()
    parser.add_argument("--c")
    parser.add_argument("modes", nargs=argparse.REMAINDER)
    #
    args = parser.parse_args()
    # parse the argument values
    if args.c:
        config.CONF_FILE = args.c
    if "nogui" in args.modes:
        show_gui = False
    if "nomove" in args.modes:
        config.AUTOMOVE = False
    if "dev" in args.modes:
        config.DEVELOPER_MODE = True
    # return results
    return show_gui


if __name__ == "__main__":
    # set correct time zone
    os.environ["TZ"] = "Europe/Berlin"
    time.tzset()
    # get config args
    LOAD_GUI = __get_arguments()
    # init the bot
    bot = Bot()
    # start the bot
    bot.startup()
