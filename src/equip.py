"""Equipment checking module"""

import config
from util import session_handler
from player import Player

def check_equip(player):
    """Check player equipment"""
    # check for better attack weapons
    __attack_weapons(player, config.ATT_WEAPON_DATA)
    __attack_weapons(player, config.DEF_WEAPON_DATA)


def __attack_weapons(player: Player, json_data):
    p_weapon_name = ''
    p_weapon_p = 0
    key_attribute = 'attack'
    if json_data == config.ATT_WEAPON_DATA:
        # get equipped weapon
        p_weapon_name = player.get_att_weapon()
        if p_weapon_name:
            p_weapon_p = player.get_att_weapon_p()
    else:  # get equipped weapon
        key_attribute = 'defense'
        p_weapon_name = player.get_def_weapon()
        if p_weapon_name:
            p_weapon_p = player.get_def_weapon_p()
    # go through all items in the inventory
    for p_item in player.get_items():
        # check if inventory item is an attack weapon
        p_item_name = p_item.get_name()
        if p_item_name in json_data:
            # we found a weapon in the inventory - get all attributes
            element = json_data[p_item_name]
            w_p = element[key_attribute]
            w_strength = element['strength']
            w_int = element['intelligence']
            w_academy = element['academy']
            w_race = element['race']
            w_magic = element['magic']
            # check values against player attributes
            if w_p > p_weapon_p and w_strength <= player.get_attp() and w_int <= player.get_int() and w_academy <= player.get_academy_limit() and (w_race == -1 or w_race == player.get_race()) and not w_magic:
                # equip weapon
                session_handler.get(
                    config.URL_ITEM + '?action=activate&act_item_id='+str(p_item.get_id()))
                #
                player.update_player()
