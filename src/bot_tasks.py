"""Module for bot specific tasks"""
import multiprocessing
import random
import time

import config
from util import check_shops


def perform_tasks():
    """Do bot specific tasks"""
    # get current time
    now = int(time.time())
    # in case enough time has passed -> save player config back to file
    if now >= config.NEXT_CFG_SAVE:
        #
        process = multiprocessing.Process(
            name="Saving config", target=config.save, args=()
        )
        #
        process.start()
        #
        config.NEXT_CFG_SAVE = now + random.randint(60,90)
    # check timing for shop price update
    if now >= config.NEXT_SHOP_PRICE_CHECK:
        # update the pricing
        check_shops.update_shops()
        # set next time to check shop prices
        config.NEXT_SHOP_PRICE_CHECK = now + random.randint(3600, 5400)
