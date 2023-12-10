"""Player Abilities Handling Module"""
import math
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from player import Player
from trade import trade
from util import session_handler

TRAIN_ABILITY_URL = (
    "http://weltxyz.freewar.de/freewar/internal/ability.php?action=train&ability_id="
)


def training(player: Player):
    """Do trainging on our abilities"""
    # get current time
    now = int(time.time())
    # check if it is time to check again
    if now <= config.NEXT_MISSING_ABILITY_CHECK:
        return
    #
    config.NEXT_MISSING_ABILITY_CHECK = now + random.randint(50, 70)
    # get abilities page
    res = session_handler.get(config.URL_ABILITY)
    #
    if not res:
        return
    # update the abilities
    update_abilities(res)
    # check for books to buy
    __missing_abilities(player)
    # get the active ability
    __get_active_ability(res, player)
    # exit if we are already training something
    if not player.get_active_training():
        # train next level
        __train_abilities(player.get_pos())


def __get_active_ability(res, player):
    # check for training
    if res and "Du trainierst gerade" not in res.text:
        player.set_active_training(None)
        return False
    #
    soup = BeautifulSoup(res.text, "lxml")
    active_ability = soup.find("p", {"class", "listrow"})
    ability_name = active_ability.contents[1].text
    player.set_active_training(ability_name)
    return True


def update_abilities(res):
    """Update the player's abilities"""
    if not res:
        res = session_handler.get(config.URL_ABILITY)
    #
    soup = BeautifulSoup(res.text, "lxml")
    page_abilities = soup.find_all("a", {"href": re.compile(r"action=show_ability")})
    #
    cur_ab_name = ""
    # clean the list
    for page_ability in page_abilities:
        # get link of ability
        href = page_ability.get("href")
        # get name of current ability
        cur_ab_name = page_ability.text
        # add ability if not in data
        if cur_ab_name not in config.PLAYER_DATA["abilities"]:
            config.PLAYER_DATA["abilities"][cur_ab_name] = {}
        # set basic values
        ability = config.PLAYER_DATA["abilities"][cur_ab_name]
        #
        ability["id"] = re.sub("[^0-9]", "", href)
        #
        parent = page_ability.parent.parent
        # get lvl string
        cur_lvl_raw = parent.contents[1].text
        # get the current level
        cur_lvl = int(re.sub("[^0-9]", "", cur_lvl_raw))
        ability["cur_lvl"] = cur_lvl
        ability["max_lvl"] = cur_lvl
        if len(parent.contents) > 2:
            # add ability to player abilities
            ability["max_lvl"] = int(parent.contents[2].text)
    # clean the ability data if it was not read
    for _, ability in config.PLAYER_DATA['abilities'].items():
        for attribute in ['cur_lvl', 'max_lvl', 'limit']:
            #
            if attribute in ability:
                continue
            #
            ability[attribute] = 0


def __missing_abilities(player: Player):
    #
    for _, ability in config.PLAYER_DATA["abilities"].items():
        #
        if "cur_lvl" in ability:
            continue
        #
        if "item" not in ability:
            continue
        #
        item_name = ability["item"]
        #
        if not item_name:
            continue
        #
        tar_item = player.get_item_by_name(item_name)
        #
        if tar_item:
            #
            trade.use_item_from_list(player, [item_name])
            #
            for idx, obj in enumerate(config.PLAYER_DATA["consumables"]):
                if obj["name"] == item_name:
                    config.PLAYER_DATA["consumables"].pop(idx)
            #
            time.sleep(random.uniform(1, 2.5))
        else:
            # attach it to consumables
            for idx, obj in enumerate(config.PLAYER_DATA["consumables"]):
                if obj["name"] == item_name:
                    return
            # create json object
            ability_item = {}
            ability_item["name"] = item_name
            ability_item["min"] = 1
            ability_item["max"] = 1
            ability_item["location"] = ability["location"]
            ability_item["id"] = ability["id"]
            ability_item["avg_price"] = ability["avg_price"]
            # add the item if we did not find it
            config.PLAYER_DATA["consumables"].append(ability_item)


def __train_abilities(player_pos):
    # wrong position
    if player_pos == "96|99":
        return
    # get id for ability to train
    target_ability_id, name = __get_target_ab_id()
    #
    if target_ability_id == 0:
        return
    # wait a few seconds before training new ability
    time.sleep(random.uniform(3, 9.5))
    # train the ability
    session_handler.get(TRAIN_ABILITY_URL + target_ability_id)
    # print a text
    botrax_logger.MAIN_LOGGER.info("Started training %s", name)


def __get_target_ab_id() -> str:
    # train abilities
    loop_id = 0
    loop_cur_lvl = 0
    loop_max_lvl = 0
    tmp_lvl = math.inf
    tar_lvl = -1
    tar_name = ""
    #
    for key, ability in config.PLAYER_DATA["abilities"].items():
        tar_lvl = ability["limit"]
        # get current values
        loop_cur_lvl = ability["cur_lvl"]
        loop_max_lvl = ability["max_lvl"]
        # we have reached max level of this ability
        if loop_cur_lvl == loop_max_lvl:
            continue
        #
        if loop_cur_lvl < tmp_lvl and (
            tar_lvl > 0 and loop_cur_lvl < tar_lvl or tar_lvl == -1
        ):
            #
            tmp_lvl = loop_cur_lvl
            loop_id = ability["id"]
            tar_name = key
    #
    return loop_id, tar_name
