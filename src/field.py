"""Module for checking of fields"""
import random
import time
from urllib import response

from bs4 import BeautifulSoup

import config

SAVE_KEY = "save"


def check_field(res: response, player):
    """
    Check field for save or not save, ice blocks, craters or other blocking things (NPCs)
    """
    #
    __save_spot(res, player)
    #
    __ice_block(res)
    #
    __remove_old_entries()
    #
    player_pos = player.get_pos()
    #
    __crater(res, player_pos)
    #
    __blocked(res, player_pos)


def __save_spot(res, player):
    # init variables
    player_position = player.get_pos()
    save_pos = False
    # check coordinate database
    if (
        player_position in config.COORD_DATA
        and SAVE_KEY in config.COORD_DATA[player_position]
    ):
        # get value
        save_pos = config.COORD_DATA[player_position][SAVE_KEY]
    else:
        # check field data
        save_keywords = [
            "Angriffe unmöglich",
            "Angriffe nicht möglich",
            "Angriffe sind hier nicht möglich",
            "Angriffe sind hier unmöglich",
            "ein Ort des Friedens",
            "Angriffe sind in der Markthalle unmöglich",
            "Angriffe sind im Dorf unmöglich",
            "Angriffe sind deswegen im Dorf unmöglich",
            "Angriffe sind hier deswegen unmöglich",
        ]
        #
        save_pos = (
            any(key.casefold() in res.text.casefold() for key in save_keywords)
        ) or player_position in config.BANKING_LOCATIONS
        #
        if (
            player_position in config.COORD_DATA
        ):
            config.COORD_DATA[player_position][SAVE_KEY] = save_pos
    #
    player.set_save_pos(save_pos)


def __ice_block(res):
    # we stepped on frozen area
    if any(key in res.text for key in ["Kaltes Eis", "Blitzeiskuppel"]):
        time.sleep(random.uniform(19, 23))


def __remove_old_entries():
    # create new list
    tmp_del = []
    # clean existing crater list
    for item in config.CRATER_LIST:
        if config.CRATER_LIST.get(item) <= int(time.time()) - 10800:
            tmp_del.append(item)
    for item in tmp_del:
        del config.CRATER_LIST[item]
    # clear temporary list
    tmp_del.clear()
    # create new list
    tmp_del = []
    # clean existing blocked list
    for item in config.BLOCKED_LIST:
        if config.BLOCKED_LIST.get(item) <= int(time.time()) - 10800:
            tmp_del.append(item)
    for item in tmp_del:
        del config.BLOCKED_LIST[item]
    # reset avoid
    if int(time.time()) < config.AVOID_NEXT_CHECK:
        return
    # check all items
    for item in config.COORD_DATA.items():
        # found an old one?
        if (
            item[1]["avoid"] > 0
            and item[1]["avoid"] <= int(time.time()) - config.AVOID_THRESHOLD
        ):
            # reset its value
            item[1]["avoid"] = 0
    # set next check timestamp
    config.AVOID_NEXT_CHECK = int(time.time()) + random.randint(375, 775)


def __blocked(res: response, p_pos: str):
    #
    blocked_keywords = [
        "Ein NPC blockiert diesen Ort. Durch Bekämpfen oder Vertreiben des Wesens kann dieser Ort wieder befreit werden."
    ]
    #
    if any(key in res.text for key in blocked_keywords):
        config.BLOCKED_LIST[p_pos] = int(time.time())
    elif p_pos in config.BLOCKED_LIST:
        del config.BLOCKED_LIST[p_pos]


def __crater(res, p_pos):
    # retrieve data
    soup = BeautifulSoup(res.text, "lxml")
    header = soup.find("td", {"class": "mainheader"})
    #
    if not header:
        return
    #
    header_s = header.text
    #
    if header_s == "Krater":
        # add to list if not already present
        config.CRATER_LIST[p_pos] = int(time.time())
    elif p_pos in config.CRATER_LIST:
        del config.CRATER_LIST[p_pos]
