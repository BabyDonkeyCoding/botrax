"""Module for fighting entities"""
import math
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
import fight_functions
import healing
from player import Player
from travel import Travel
from util import functions, session_handler


def kill(res, player: Player):
    """Search field for killable entities"""
    # retrieve data
    soup = BeautifulSoup(res.text, "lxml")
    # kill npcs on field
    response = __kill_normal_npc(soup, player)
    # check result
    if response:
        res = response
    #
    return res


def __kill_normal_npc(soup, player: Player):
    # initialize variables
    attack_list = None
    # from 100XP we get fast attack option
    attack_list = soup.find_all("a", {"class": "fastattack"})
    # below 100XP we need to use normal fight menu
    if not attack_list:
        #
        attack_list = soup.find_all("a", {"href": re.compile(r"action=attacknpcmenu")})
    #
    res = __attack_normal_npc(player, attack_list)
    #
    return res


def __attack_normal_npc(player: Player, attack_list):
    #
    after_attack_response = None
    #
    for att in attack_list:
        # get attack URL
        attack_url = str(att.get("href"))
        # in low xp range we do not have fastattack
        attack_url = _check_attack_menu(attack_url)
        # check url
        if "npc_id" not in attack_url or "action=attacknpc" not in attack_url:
            # cancel attack
            continue
        # init NPC name
        npc_name = ""
        #
        npc = att.parent
        # get npc name from site
        npc_name_s = BeautifulSoup(str(npc), "lxml").find("b")
        # if we got it, we extract the string
        if npc_name_s:
            npc_name = npc_name_s.text.strip()
        # update player before any calculation for fight
        player.update_player()
        # get player HP values
        p_hp = int(player.get_hp())
        p_max_hp = int(player.get_max_hp())
        # NPC not in our database?
        if npc_name.upper() not in config.NPC_DATA["npcs"]:
            # abort fight
            continue
        # npc should be in list
        npc_json = config.NPC_DATA["npcs"][npc_name.upper()]
        # check XP and Gold we can expect from NPC kill
        if (
            int(npc_json["xp"]) == 0
            and int(npc_json["gold"]) < 1
            and not player.is_in_group()
        ):
            # Abort fight because NPC gives neither XP nor Gold
            continue
        # calculate attacker and defender factors
        p_attack = int(player.get_attp()) + int(player.get_att_weapon_p())
        p_defense = int(player.get_defp()) + int(player.get_def_weapon_p())
        # get NPC stats
        npc_list_att = int(npc_json["attack"])
        npc_s = str(npc.text)
        # get npc attack power and HP
        npc_att_p = int(fight_functions.get_npc_att_p(npc_s))
        npc_hp = int(npc_json["hp"])
        #
        p_def_factored = math.floor(p_defense * 0.04)
        # there is a mismatch between filed npc and json data
        if npc_att_p > npc_list_att and npc_att_p > p_def_factored:
            continue
        #
        defender_calc_tmp = npc_list_att - p_defense
        #
        if p_defense >= npc_list_att:
            defender_calc_tmp = 1
        # FaktorVerteidiger = LAngreifer / ( AVerteidiger - VAngreifer )
        # FaktorAngreifer = LVerteidiger / ( AAngreifer - VVerteidiger)
        f_defender = p_hp / defender_calc_tmp
        f_attacker = npc_hp / p_attack
        # check NPX strength
        if f_attacker > (p_max_hp / defender_calc_tmp):
            # NPC too strong
            continue
        #
        if f_attacker > f_defender and p_hp < p_max_hp:
            # init healing variable
            healed = True
            while f_attacker > f_defender and p_hp < p_max_hp and healed:
                # heal yourself on field or with item
                healed = healing.heal_from_items(player, True)
                # get updated values
                p_hp = int(player.get_hp())
                p_max_hp = int(player.get_max_hp())
                # new calculation
                f_defender = p_hp / defender_calc_tmp
            # npc too strong or not enough HP etc.
            if f_attacker > f_defender:
                continue
        # chase npc instead of killing it if it is not a "phasen npc"
        chasing_npc_perc = 0
        player_is_not_farming = player.get_travel().value != Travel.FARMING.value
        #
        if "chase_percentage" in config.PLAYER_DATA:
            chasing_npc_perc = float(config.PLAYER_DATA["chase_percentage"])
        #
        if (
            chasing_npc_perc > 0
            and functions.get_chance(chasing_npc_perc)
            and "Phasen" not in npc_name
            and player_is_not_farming
        ) or npc_name.lower() in (
            name.lower() for name in config.PLAYER_DATA["npc"]["blacklist"]
        ):
            attack_url = attack_url.replace("action=attacknpc", "action=chasenpc")
        # generate random waiting time
        final_url = config.URL_INTERNAL_BASE + attack_url
        # sleep for a bit before attacking next npc
        wait = random.uniform(0.5, 1)
        time.sleep(wait)
        # Attack!
        after_attack_response = session_handler.get(final_url)
        #
        if after_attack_response and "Niederlage" in after_attack_response.text:
            # update current location player data
            player.update_player()
            # move to location we died
            player.set_destination(f"{player.get_posx()}|{player.get_posy()}")
            #
            player.set_travel(Travel.TRAVEL)
            # open debug file
            botrax_logger.DEBUG_LOGGER.warning(after_attack_response.text)
            # print a debug warning
            dbg_msg = (
                "I died attacking "
                + npc_name
                + " A:"
                + str(npc_att_p)
                + " @"
                + player.get_pos()
            )
            botrax_logger.MAIN_LOGGER.warning(dbg_msg)
            # return as we are dead now
            return
        # update player data
        player.update_player()
    #
    return after_attack_response

def _check_attack_menu(attack_url):
    #
    if "action=attacknpcmenu" in attack_url:
            # open attack menu
        after_attack_response = session_handler.get(
                config.URL_INTERNAL_BASE + attack_url
            )
            # get links
        attack_link = BeautifulSoup(after_attack_response.text, "lxml").find(
                "a", {"href": re.compile("action=attacknpc&")}
            )
        #
        if attack_link:
            #
            attack_url = attack_link.get("href")
    #
    return attack_url
