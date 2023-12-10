"""Module to check field for NPCs"""

import time
from bs4 import BeautifulSoup, NavigableString

import config
from npc import normal_npc, special_npc
from travel import Travel
from move import movement_functions

WATCHDOG_NPC = "zähnefletschender Wachhund"

def perform(res, player):
    """Check field for NPCs"""
    #
    if "Du siehst keine Person an diesem Ort" in res.text:
        #
        if player.get_travel().value == Travel.UNIQUE_NPC_KILL.value:
            player.set_travel(Travel.RANDOM)
        #
        return res
    #
    __check_avoid_npcs(res, player)
    #
    response = normal_npc.kill(res, player)
    #
    if response:
        res = response
    #
    if (
        "Unique-NPC" not in res.text
        or (player.target_npc and player.target_npc not in res.text)
    ):
        return res
    # look for unique npc
    response = special_npc.check_for_npc(res, player)
    # check result
    if response:
        res = response
    #
    return res


def __check_avoid_npcs(res, player):
    """Check if we meet the watchdog

    Args:
        res (response): response
        player (Player.Player): player object
    """
    #
    avoid_npcs = config.PLAYER_DATA["npc"]["avoid"]
    # we found a keyword and have low hp?
    if not any(key in res.text for key in avoid_npcs):
        return
    #
    users = BeautifulSoup(res.text, "lxml").find_all("p", {"class": "listusersrow"})
    #
    for user in users:
        # init variables
        u_name = ""
        # ist frei.
        text = user.text
        #
        if isinstance(user.contents[1], NavigableString):
            continue
        #
        u_name = user.contents[1].text.strip()
        p_pos = player.get_pos()
        # we have met the watchdog
        if (
            u_name in avoid_npcs or WATCHDOG_NPC in u_name
        ) and p_pos in config.COORD_DATA:
            # add npc position to blocked area
            config.COORD_DATA[p_pos]["avoid"] = int(time.time())
            # walk away from watchdog
            __check_watchdog(u_name, player, text)


def __check_watchdog(u_name, player, text):
    #
    if WATCHDOG_NPC not in u_name:
        return
    search_txt = "die Passage in fast alle Richtungen, nur der "
    pos = text.find(search_txt)
    pos2 = text.find("ist frei")
    direction = text[pos + len(search_txt) : pos2].strip()
    #
    spot = movement_functions.get_direction_spot(direction, player)
    #
    player.update_path([spot])
    player.set_travel(Travel.EMERGENCY)
