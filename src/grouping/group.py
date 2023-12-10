"""Module for group related tasks and actions"""
import math
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
import fight_functions
from chat import chat_config
from chat.chat import Chatchannel, talk_with_chat
from grouping import group_conf as gc
from grouping import group_mgmt
from travel import Travel
from util import session_handler


def handle_grouping(res_main, player):
    """Handles all group related tasks."""
    # clean the log
    _clean_tagged_npcs()
    #
    _stop_waiting(player)
    # check group hunting
    _group_hunting(res_main, player)
    #
    group_mgmt.manage_group(player)


def _stop_waiting(player):
    #
    if gc.TAGGED_NPC and player.last_slap < int(time.time()) - gc.MAX_WAIT_TIME:
        # update config
        gc.TAGGED_NPC = None
        gc.MAX_WAIT_TIME = random.uniform(25, 40)
        # update player
        player.set_travel(Travel.RANDOM)
        player.target_npc = None
        #
        talk_with_chat(random.choice(chat_config.CONTINUE), Chatchannel.GROUP)
    #


def _clean_tagged_npcs():
    indexes = []
    #
    for key, value in gc.LAST_TAGGED_NPS.items():
        if value < int(time.time()) - gc.TAG_SAVE_THRESHOLD:
            indexes.append(key)
    #
    for index in indexes:
        del gc.LAST_TAGGED_NPS[index]
    #


def _group_hunting(res, player):
    # check for NPC
    if (
        "(Gruppen-NPC)" not in res.text
        or not player.is_in_group()
        or player.get_travel().value > Travel.GROUP_HUNTING.value
    ):
        return
    # check aborting conditions
    if player.target_npc:
        _kill_grp_npc(res, player)
    else:
        _tag_grp_npc(res, player)


def _tag_grp_npc(res, player):
    #
    area = config.COORD_DATA[player.get_pos()]["area"]
    #
    if gc.TAGGED_NPC or "Tanien" in area:
        return
    #
    soup = BeautifulSoup(res.text, "lxml")
    # get fast attack links
    tag_list = soup.find_all("a", {"href": re.compile(r"action=fastnpcposition")})
    #
    for link in tag_list:
        # get the NPC name from the link
        npc_name, _ = _get_npc_details(link)
        # check if NPC is blacklisted
        npc_is_blacklisted = (
            npc_name in config.PLAYER_DATA["npc"]["blacklist"]
        )
        # check if NPC is the current target NPC
        npc_is_not_target_npc = (
            player.target_npc and npc_name.casefold() != player.target_npc.casefold()
        )
        # NPC is "Phasen" NPC type
        npc_is_phasen_npc = "Phasen" in npc_name
        not_group_npc = "(Gruppen-NPC)" not in str(link.parent)
        # check our cancle conditions
        if (
            npc_is_blacklisted
            or npc_is_not_target_npc
            or npc_name in gc.LAST_TAGGED_NPS
            or npc_is_phasen_npc
            or not_group_npc
        ):
            continue
        #
        if "Geist von" in npc_name and "2tower.jpg" in res.text:
            continue
        # set the NPC
        player.target_npc = npc_name
        gc.TAGGED_NPC = npc_name
        gc.LAST_TAGGED_NPS[npc_name] = int(time.time())
        player.update_path(None)
        player.set_travel(Travel.GROUP_HUNTING)
        #
        time.sleep(random.uniform(0.75, 3))
        # set last slap time
        player.last_slap = int(time.time())
        # attack
        res = session_handler.get(config.URL_INTERNAL_BASE + link.get("href"))
        #
        botrax_logger.MAIN_LOGGER.warning(f"Tagging Group NPC {npc_name}")


def _kill_grp_npc(res, player):
    #
    group_members_on_field = "GRUPPEN-MITGLIED".casefold() in res.text.casefold()
    #
    if not group_members_on_field:
        return
    #
    soup = BeautifulSoup(res.text, "lxml")
    # get fast attack links
    attack_list = soup.find_all("a", {"href": re.compile(r"&action=slapnpc&mark=")})
    #
    for att in attack_list:
        # get link value
        href = att.get("href")
        # get npc data
        npc_name, u_npc_attack = _get_npc_details(att)
        # reset tagged NPC
        if gc.TAGGED_NPC and npc_name in gc.TAGGED_NPC:
            gc.TAGGED_NPC = None
        # check whitelist names
        if npc_name in config.PLAYER_DATA["npc"]["blacklist"]:
            continue
        if (
            player.target_npc
            and npc_name.casefold() not in str(player.target_npc).casefold()
        ):
            continue
        #
        if "Geist von" in npc_name and "2tower.jpg" in res.text:
            continue
        #
        p_def = player.get_defp() + player.get_def_weapon_p()
        #
        p_def_factored = math.floor(p_def * 0.8)
        #
        if u_npc_attack > p_def_factored or (
            player.target_npc and npc_name not in player.target_npc
        ):
            continue
        # use group attack mode
        href.replace("mark=0", "mark=1")
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
        #
        time.sleep(random.uniform(0.75, 3))
        # set last slap time
        player.last_slap = now
        # slap the group NPC
        res = session_handler.get(config.URL_INTERNAL_BASE + href)


def _get_npc_details(att):
    npc = att.parent
    # init NPC name
    npc_name = ""
    # get npc name
    name_soup = BeautifulSoup(str(npc), "lxml").find("b")
    #
    if name_soup:
        npc_name = name_soup.text.strip()
        # check if we can attack the unique NPC
    u_npc_attack = int(fight_functions.get_npc_att_p(str(npc.text)))
    return npc_name, u_npc_attack
