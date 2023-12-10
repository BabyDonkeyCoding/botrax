"""
Module for fighting unique NPCs
"""

import math
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
import fight_functions
from player import Player
from travel import Travel
from util import session_handler


def check_for_npc(res, player: Player):
    """Check if we are fighting a unique NPC"""
    # able to attack unique NPC?
    if player.get_travel().value > Travel.UNIQUE_NPC_KILL.value:
        return res
        # retrieve data
    soup = BeautifulSoup(res.text, "lxml")
    # get fast attack links
    attack_list = soup.find_all("a", {"href": re.compile(r"&action=slapnpc&mark=")})
    #
    for att in attack_list:
        # get npc data
        npc = att.parent
        # get link value
        href = att.get("href")
        # skip non unique NPCs (e.g.: resistance NPCs, etc.)
        if "(Unique-NPC)" not in npc.text:
            continue
        # init NPC name
        npc_name = ""
        # get npc name
        name_soup = BeautifulSoup(str(npc), "lxml").find("b")
        #
        if name_soup:
            npc_name = name_soup.text.strip()
        # check whitelist names
        if npc_name.casefold() in (
            name.casefold() for name in config.PLAYER_DATA["npc"]["blacklist"]
        ) or (
            player.target_npc and npc_name.casefold() != player.target_npc.casefold()
        ):
            continue
        # check if we can attack the unique NPC
        u_npc_attack = int(fight_functions.get_npc_att_p(str(npc.text)))
        #
        p_def = player.get_defp() + player.get_def_weapon_p()
        #
        p_def_factored = math.floor(p_def * 0.04)
        #
        if (
            (
                "uniques" in config.PLAYER_DATA["npc"]
                and npc_name in config.PLAYER_DATA["npc"]["uniques"]
            )
            or u_npc_attack <= p_def_factored
            or (
                player.target_npc
                and npc_name in player.target_npc
            )
        ):
            # set new target if not already present
            if not player.target_npc:
                player.target_npc = npc_name
                # log
                botrax_logger.MAIN_LOGGER.warning(
                    "Start attacking Unique NPC %s", npc_name
                )
                #
                player.set_travel(Travel.UNIQUE_NPC_KILL)
                player.update_path(None)
            #
            now = int(time.time())
            #
            player.update_player()
            # check for overall hp
            p_hp = int(player.get_hp())
            p_max_hp = int(player.get_max_hp())
            # check for last slap and HP value
            if now <= player.last_slap + random.uniform(4.75, 7.1) or (
                p_hp < round(p_max_hp * 0.1)
            ):
                continue
            # set last slap time
            player.last_slap = now
            # attack
            res = session_handler.get(config.URL_INTERNAL_BASE + href)
    #
    return res
