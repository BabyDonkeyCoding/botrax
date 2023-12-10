"""Module for movement related funtions"""
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from move import movement_config as mc
import pathfinding
from pathfinding.spot import Spot
from travel import Travel
from util import session_handler


def get_direction_spot(msg_text, player):
    """Searches message string for direction and generates a direction spot for navigation"""
    # init search variable
    search_txt = "Richtung"
    # get direction string from message string
    if search_txt in msg_text:
        direction = msg_text[
            msg_text.find(search_txt) + len(search_txt) : len(msg_text)
        ].strip()
    else:
        direction = msg_text
    # get current user position coordinates
    p_posx = int(player.get_posx())
    p_posy = int(player.get_posy())
    # calculate direction
    if direction == "Norden":
        p_posx = int(p_posx)
        p_posy = int(p_posy - 1)
    elif direction == "Süden":
        p_posx = int(p_posx)
        p_posy = int(p_posy + 1)
    elif direction == "Osten":
        p_posx = int(p_posx + 1)
        p_posy = int(p_posy)
    elif direction == "Westen":
        p_posx = int(p_posx - 1)
        p_posy = int(p_posy)
    elif direction == "Nordwesten":
        p_posx = int(p_posx - 1)
        p_posy = int(p_posy - 1)
    elif direction == "Nordosten":
        p_posx = int(p_posx + 1)
        p_posy = int(p_posy - 1)
    elif direction == "Südwesten":
        p_posx = int(p_posx - 1)
        p_posy = int(p_posy + 1)
    elif direction == "Südosten":
        p_posx = int(p_posx + 1)
        p_posy = int(p_posy + 1)
    #
    return Spot(p_posx, p_posy)


def get_current_position(res):
    """Reads the current position from the map of the game"""
    # in case for first init call
    if not res:
        res = session_handler.get(config.URL_MAP_RELOAD)
    # init variables
    pos_x = 0
    pos_y = 0
    # we have content
    if not res:
        return pos_x, pos_y
    #
    regex_result1 = re.findall(r"pos_x = -?\d{1,6}", res.text)
    #
    if len(regex_result1) > 0:
        pos_x = regex_result1[0].replace("pos_x = ", "")
    #
    regex_result2 = re.findall(r"pos_y = -?\d{1,6}", res.text)
    #
    if len(regex_result2) > 0:
        pos_y = regex_result2[0].replace("pos_y = ", "")

    # return
    return pos_x, pos_y


def get_avoid_fields(res):
    """Retrive nocango fields from map"""
    if not res:
        return
    soup = BeautifulSoup(res.text, "lxml")
    # we prefer fast attacking NPCs
    nocangos = soup.find_all("a", {"class": "nocango"})
    # walk through all items
    for ncg in nocangos:
        # get parent class
        parent_class = ncg.parent.get("class")
        # check for normal fields only
        if "maptd" not in parent_class:
            continue
        #
        pos_txt = ncg.parent.get("id")
        # find x value
        sp_str = pos_txt
        sp_str = sp_str[4 : len(pos_txt)]
        new_var = sp_str.rfind("y")
        sp_str = sp_str[0:new_var]
        x_coord = sp_str
        # get y value
        # find x value
        sp_str = pos_txt
        pos = sp_str.find("y")
        y_coord = sp_str[pos + 1 : len(pos_txt)]
        #
        loc = str(str(x_coord) + "|" + str(y_coord))
        #
        if loc not in config.COORD_DATA:
            continue
        #
        config.COORD_DATA[loc]["avoid"] = int(time.time())


def get_npc_map_data(res, player):
    """Retrieves NPCs from map"""
    # we are on a path already -> return
    if player.get_travel().value >= Travel.NPC_HUNTING.value:
        return
    # in case for first init call
    if not res:
        res = session_handler.get(config.URL_MAP)
    # create empty list
    npc_locations = []
    # get page content
    soup = BeautifulSoup(res.text, "lxml")
    # get elements which show NPCs on map
    npcs = soup.find_all("g", {"class": "npcs"})
    #
    for npc in npcs:
        parent_element = npc.parent.parent.parent
        pos_txt = parent_element.get("id")
        # find x value
        sp_str = pos_txt
        sp_str = sp_str[4 : len(pos_txt)]
        new_var = sp_str.rfind("y")
        sp_str = sp_str[0:new_var]
        npc_x = sp_str
        # get y value
        # find x value
        sp_str = pos_txt
        pos = sp_str.find("y")
        npc_y = sp_str[pos + 1 : len(pos_txt)]
        #
        loc = str(npc_x) + "|" + str(npc_y)
        # do not visit places we have been to already
        #
        if (
            loc not in mc.BEEN_THERE_LIST
            and loc in config.COORD_DATA
            and config.COORD_DATA[loc]["avoid"] == 0
        ):
            npc_locations.append(loc)
    # check if we got some data
    if not npc_locations:
        return
    # set up variables
    tmp_path = []
    tmp_start = player.get_pos()
    # create long path for all npcs we have seen
    for npc in npc_locations:
        #
        tmp_path.extend(pathfinding.path.get_path(tmp_start, npc))
        tmp_start = npc
    # check if path has been created
    if tmp_path:
        # update player
        player.update_path(tmp_path)
        player.set_travel(Travel.NPC_HUNTING)
        #
        dbg_msg = f"Hunting NPCs for {len(tmp_path)} steps with final position {tmp_start}"
        # log dbg msg
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
