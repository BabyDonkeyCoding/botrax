"""Repairing gear module"""
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from player import Player
from travel import Travel
from util import functions, session_handler


def check(res, player: Player):
    """Check gear"""
    #
    __check_gear(player)
    # repair gear
    __repair(res)


def __check_gear(player: Player):
    # REPAIR?
    if not player.needs_repair() or player.get_travel().value >= Travel.REPAIR.value:
        return
    #
    target, _ = functions.get_closest_location(player.get_pos(), config.REPAIR_SHOPS)
    #
    if not target:
        return
    #
    botrax_logger.MAIN_LOGGER.info("Walking to shop for repairs at %s", str(target))
    #
    player.set_destination(target)
    player.set_travel(Travel.REPAIR)


def __repair(res):
    #
    if "?arrive_eval=repair" not in res.text:
        return
    #
    res = session_handler.get(config.URL_REPAIR_MENU)
    #
    if "Du hast keine kaputten Waffen dabei." in res.text:
        return
    #
    soup = BeautifulSoup(res.text, "html.parser")
    #
    regex_result = re.findall(
        r"(Zustand: \d{1,3}%)", soup.text
    )
    if len(regex_result) > 0:
        percentage = int(re.sub("[^0-9]", "", regex_result[0]))
        #
        if percentage > config.REPAIR_THRESHOLD:
            return
        # random wait
        wait = random.uniform(1, 4)
        time.sleep(wait)
        # repair all items
        session_handler.get(config.URL_REPAIR_ALL_GEAR)
        #
        config.REPAIR_THRESHOLD = _get_rnd_repair_threshold()
        # log action
        botrax_logger.DEBUG_LOGGER.debug("Repaired gear")
        # random wait
        wait = random.uniform(1, 3)
        time.sleep(wait)

def _get_rnd_repair_threshold() -> int:
    """Returns time we wait until next repair"""
    return random.randint(50, 80)