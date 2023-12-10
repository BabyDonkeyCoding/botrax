"""Modul for moving."""
import random
import re
import time
import traceback

import botrax_logger
import config
from move import movement_config as mc
from move import movement_functions
from pathfinding.spot import Spot
from player import Player
from travel import Travel
from util import functions, session_handler


def init_move(player: Player):
    """Initialize a move"""
    #
    if (
        player.get_travel() in [Travel.UNIQUE_NPC_KILL, Travel.GROUP_HUNTING]
        and not player.get_path()
    ):
        return
    dirx = diry = 0
    # get move direction
    try:
        dirx, diry = __get_next_move(player)
    except (
        FileNotFoundError,
        IOError,
        RuntimeError,
        TypeError,
        NameError,
        IndexError,
        ValueError,
        AttributeError,
        ConnectionError,
    ):
        botrax_logger.DEBUG_LOGGER.warning(traceback.format_exc())
    #
    if dirx == 0 and diry == 0:
        return
    # make the move
    __move(player, dirx, diry)


def __get_next_move(player: Player):
    #
    dirx, diry = 0, 0
    #
    if player.get_travel() == Travel.RANDOM:
        dirx, diry = __get_exploring_move(player)
    else:
        #
        dirx, diry = __get_next_path_move(player)
    # we did not get any direction to walk to
    if (
        dirx == 0
        and diry == 0
        and player.get_travel()
        and player.get_travel() not in [Travel.UNIQUE_NPC_KILL, Travel.GROUP_HUNTING]
    ):
        # repeat request
        (
            dirx,
            diry,
        ) = __get_next_move(player)
    #
    return dirx, diry


def __get_next_path_move(player: Player):
    #
    dirx = diry = tarx = tary = 0
    #
    path = player.get_path()
    #
    if not path or len(path) < 1:
        # check for travel mode
        if player.get_travel() not in [Travel.UNIQUE_NPC_KILL, Travel.GROUP_HUNTING]:
            # reset everything
            player.set_travel(Travel.RANDOM)
            player.update_path(None)
        # return the value
        return dirx, diry
    #
    p_posx = int(player.get_posx())
    p_posy = int(player.get_posy())
    #
    next_step = path[0]
    tarx, tary = next_step.get_pos()
    # get directions
    tarx = int(tarx)
    tary = int(tary)
    # we arrived at next step in path list
    if p_posx == tarx and p_posy == tary:
        # remove the step we arrived
        path.remove(path[0])
        # update the path list in player object
        player.update_path(path)
        #
        if len(path) > 0:
            # get the next step
            next_step = path[0]
            # get target locations to build move direction
            tarx, tary = next_step.get_pos()
            # get directions
            tarx = int(tarx)
            tary = int(tary)
            # debug out the next step coordinates
            dbg_msg = (
                "Next step: "
                + str(next_step.get_pos())
                + " | Remaining amount of steps: "
                + str(len(path))
            )
            botrax_logger.DEBUG_LOGGER.debug(dbg_msg)
        else:
            # arrived at destination
            botrax_logger.MAIN_LOGGER.info(
                "Arrived at destination: %s", next_step.to_string()
            )
            #
            player.set_travel(Travel.RANDOM)
            player.update_path(None)
    # get new direction vector
    dirx = tarx - p_posx
    diry = tary - p_posy
    # is next step a adjacent field?
    too_far = abs(dirx) > 1 or abs(diry) > 1
    # is target location a field we can reach?
    tar_pos = str(tarx) + "|" + str(tary)
    #
    if tar_pos not in config.COORD_DATA:
        return dirx, diry
    #
    coordinate = config.COORD_DATA[tar_pos]
    #
    cannot_go = not coordinate["cango"] or coordinate["avoid"] > 0
    # are we able to reach target spot?
    if too_far or cannot_go:
        # reset existing path value
        player.update_path(None)
        # write debug
        path_target = path[len(path) - 1].to_string()
        dbg_msg = f"Recalculating path torwards {path_target}"
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # calculate new path
        player.set_destination(path_target)
    #
    return dirx, diry


def __move(player: Player, dirx, diry):
    # init moving by getting page
    res = session_handler.get(
        config.URL_MAP
        + "?walkX="
        + str(dirx)
        + "&walkY="
        + str(diry)
        + "&intwalkid="
        + str(mc.INTWALKID)
    )
    # we received content back
    if not res:
        return
    # get walking id to send it with next request
    __get_intwalkid(res)
    # get current position
    pos_x, pos_y = movement_functions.get_current_position(res)
    #
    player.set_posx(int(pos_x))
    player.set_posy(int(pos_y))
    #
    current_loc = player.get_pos()
    # set been there items
    if current_loc not in mc.BEEN_THERE_LIST and player.get_travel() == Travel.RANDOM:
        mc.BEEN_THERE_LIST.append(current_loc)
    # keep length maximum length by popping first entry if longer
    if len(mc.BEEN_THERE_LIST) > mc.BEEN_THERE_MAX_LENGTH:
        mc.BEEN_THERE_LIST.pop(0)
    # did we move?
    if mc.LAST_MOVE_LOC != current_loc:
        # if yes, set new data
        mc.LAST_MOVE_LOC = current_loc
        mc.LAST_MOVE_TIME = time.time()
    elif (
        (abs(time.time() - mc.LAST_MOVE_TIME) > mc.LAST_MOVE_THRESHOLD)
        and current_loc not in config.AH_LOCATIONS
        and current_loc not in config.BANKING_LOCATIONS
        and not player.is_save_pos()
        and player.get_travel().value
        not in [Travel.UNIQUE_NPC_KILL.value, Travel.GROUP_HUNTING.value]
    ):
        # we are in a dungeon
        if int(player.get_posx()) <= 0:
            #
            mc.BEEN_THERE_LIST.clear()
        # we on overworld
        else:
            #
            tar_location = functions.get_rnd_loc(current_loc)
            # we might have a problem on our path
            dbg_msg = "Looks like I am stuck!? Moving to rnd hunting ground: " + str(
                tar_location
            )
            botrax_logger.MAIN_LOGGER.info(dbg_msg)
            #
            player.set_destination(tar_location)
            player.set_travel(Travel.TRAVEL)
            player.target_npc = None
            #
            if not player.get_path():
                player.set_travel(Travel.RANDOM)
                player.update_path(None)
            #
            mc.BEEN_THERE_LIST.clear()
    # get no cango areas from map data and store in list
    movement_functions.get_avoid_fields(res)
    # get npcs on map due to soul seeing
    movement_functions.get_npc_map_data(res, player)


def __get_intwalkid(res) -> str:
    #
    regex_result = re.findall(r"&intwalkid=\d{1,9}", res.text)
    #
    if len(regex_result) > 0:
        new_walkid = re.sub("[^0-9]", "", regex_result[0])
        mc.INTWALKID = new_walkid


def __get_exploring_move(player: Player) -> int:
    # init varibales
    dirx = diry = 0
    pposx = int(player.get_posx())
    pposy = int(player.get_posy())
    pos_spot = Spot(pposx, pposy)
    tar_spot = None
    limit_counter = 0
    max_choices = 1
    pot_neighbors = {}
    tmp1 = None
    tmp2 = None
    # build array of potential neighbors
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            # current spot ignore
            if x == 0 and y == 0:
                continue
            pot_neighbors[f"{pposx + x}|{pposy + y}"] = Spot(pposx + x, pposy + y)
    # update the list
    pos_spot.update_neighbors(pot_neighbors)
    # get actual neighbor positions
    act_neighbors = pos_spot.get_neighbors()
    # field has neighbors
    if act_neighbors:
        max_choices = len(act_neighbors)
        tar_spot = random.choice(act_neighbors)
        #
        while (
            tar_spot.to_string() in mc.BEEN_THERE_LIST and limit_counter < max_choices
        ):
            tar_spot = random.choice(act_neighbors)
            limit_counter += 1
    #
    else:
        #
        if limit_counter >= max_choices:
            # we are in a dungeon
            if int(player.get_posx()) <= 0:
                #
                been_there_size = len(mc.BEEN_THERE_LIST)
                #
                if been_there_size > 1:
                    #
                    tmp1 = mc.BEEN_THERE_LIST[been_there_size - 1]
                    tmp2 = mc.BEEN_THERE_LIST[been_there_size - 2]
                #
                mc.BEEN_THERE_LIST.clear()
                #
                if act_neighbors and len(act_neighbors) > 1 and tmp1 and tmp2:
                    mc.BEEN_THERE_LIST.append(tmp2)
                    mc.BEEN_THERE_LIST.append(tmp1)
            # we on overworld
            else:
                # clear the been there list
                mc.BEEN_THERE_LIST.clear()
                # remove path
                tar_location = functions.get_rnd_loc(player.get_pos())
                #
                if tar_location:
                    # debug
                    dbg_msg = "Breaking move deadlock and moving to " + tar_location
                    # log
                    botrax_logger.MAIN_LOGGER.info(dbg_msg)
                    # set path to new target location
                    player.set_destination(tar_location)
                    player.set_travel(Travel.TRAVEL)
                    # break while loop
                else:
                    #
                    jump_locations = [
                        "2",
                        "68",
                        "87",
                        "110",
                        "196",
                        "290",
                        "437",
                        "538",
                        "816",
                        "884",
                        "988",
                        "1321",
                        "1715",
                        "4304",
                        "5810",
                    ]
                    #
                    botrax_logger.MAIN_LOGGER.info(
                        "Using zauber kugel because path not found"
                    )
                    #
                    player.use_gzk(jump_locations)
                    #
                    return dirx, diry
    #
    if tar_spot:
        tar_loc = tar_spot.get_pos()
        dirx = tar_loc[0] - pposx
        diry = tar_loc[1] - pposy
    #
    # return values
    return dirx, diry
