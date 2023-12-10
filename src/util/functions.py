"""Module with basic functions"""
import math
import random
import re
import time

import botrax_logger
import config
import pathfinding
from util import session_handler


def get_next_trade_timestamp() -> int:
    """Returns randomized timestamp for next trade action"""
    return int(time.time()) + random.randint(3600, 7200)


def use_item_by_name(player, item_name: str):
    """Use item by given name."""
    #
    item = player.get_item_by_name(item_name)
    if not item:
        return False
    # generate random waiting time
    wait = random.uniform(1, 1.5)
    time.sleep(wait)
    # create url
    url = config.URL_ITEM + f"?action=activate&act_item_id={item.get_id()}"
    check_id = item.get_check_id()
    if check_id:
        url += f"&itemcheckid={check_id}"
    # use the item
    session_handler.get(url)
    # debug
    botrax_logger.MAIN_LOGGER.info("Used: %s", item_name)
    #
    return True


def get_min_char_gold() -> int:
    """Returns minimum char gold value"""
    default_value = config.PLAYER_DATA["banking"]["min_char_gold_default"]
    return random.randint(round(default_value * 0.975), round(default_value * 1.3))


def get_max_char_gold() -> int:
    """Returns maximum char gold value"""
    min_default_value = config.PLAYER_DATA["banking"]["min_char_gold_default"]
    #
    max_base_value = round(min_default_value * 4.5)
    #
    return random.randint(round(max_base_value * 0.9), round(max_base_value * 1.5))


def get_next_bank_port() -> int:
    """Returns time for next possible bank port"""
    return int(time.time() + random.randint(30, 45))


def get_night_break() -> int:
    """Returns time we want to sleep"""
    return random.randint(28000, 33000)


def get_next_logout() -> int:
    """Returns the next logout time stamp"""
    return int(int(time.time()) + random.randint(15259, 23832))


def get_target_timestamp(string) -> int:
    """ " Returns the timestamp of decay or finalization"""
    # get now
    now = int(time.time())
    #
    loop_value = 0
    # timings array
    timings = {"Tage": 86400, "Stunden": 3600, "Minuten": 60}
    # get time from string
    for timing in timings.items():
        regex = re.findall(r"\d+ " + timing[0], string)
        if len(regex) > 0:
            amount = re.sub("[^0-9]", "", regex[0])
            if not amount:
                continue
            #
            amount = int(amount)
            #
            loop_value += int(round(timing[1] * amount))
    # calculate total
    total = now + loop_value
    #
    return int(total)


def get_next_break() -> int:
    """Returns the next break time stamp"""
    return int(time.time() + random.randint(6875, 14934))


def get_chance(percentage) -> bool:
    """Returns True if the given percentage is hit by random generator

    Args:
        percentage: float: The percentage to check against as float between 0 and 1
    """
    rnd_number = round(random.uniform(0, 1), 2)
    result = rnd_number <= percentage
    return result


def get_closest_location(player_pos, locations) -> str:
    """Returns closest location from the given list in reference to the given player_pos

    Args:
        player_pos (str): Players current position in format 'x|y'
        list_with_locations (list): List with various locations

    Returns:
        str: The target location
    """
    # tmp_distance
    tar_dis = math.inf
    tar_loc = None
    # loop all locations
    for location in locations:
        #
        if location in config.COORD_DATA and config.COORD_DATA[location]["avoid"] > 0:
            continue
        #
        loop_dis = get_distance(player_pos, location)
        #
        if isinstance(location, dict):
            loop_loc = location["Position"]
        else:
            loop_loc = location
        #
        if (
            loop_dis < tar_dis
            and loop_loc not in config.CRATER_LIST
            and loop_loc not in config.BLOCKED_LIST
        ):
            tar_dis = loop_dis
            tar_loc = loop_loc
        #
    # return item and distance to the item
    return tar_loc, tar_dis


def get_distance(player_pos: str, target_pos):
    """Return the distance between to positions

    Args:
        player_pos (str): _description_
        item (_type_): _description_

    Returns:
        _type_: _description_
    """
    distance = 0
    pposx = int(player_pos.split("|")[0])
    pposy = int(player_pos.split("|")[1])
    pos_array = []
    # item is string
    if isinstance(target_pos, dict):
        pos_array = target_pos["Position"].split("|")
    else:
        pos_array = target_pos.split("|")
    #
    distance = (
        abs(int(pos_array[0]) - pposx) ** 2 + (abs(int(pos_array[1]) - pposy) ** 2)
    ) ** 0.5
    #
    distance = int(distance)
    #
    return distance


def get_rnd_loc(player_pos):
    """Returns location for the next hunting ground random."""
    #
    if "-" in player_pos:
        return None
    #
    can_go = False
    tar_loc = None
    loop_tar_loc = None
    path = []
    limit = 100
    step = 1
    range_width = 30
    # get positions
    pposx, pposy = player_pos.split("|")
    # cast to integer
    pposx = int(pposx)
    pposy = int(pposy)
    # randonmly select target location from coordinates
    while (not can_go or len(path) == 0) and step <= limit:
        #
        tar_x = random.randint(pposx - range_width, pposx + range_width)
        tar_y = random.randint(pposy - range_width, pposy + range_width)
        loop_tar_loc = f"{tar_x}|{tar_y}"
        #
        if "-" in loop_tar_loc or loop_tar_loc not in config.COORD_DATA:
            continue
        # get a path
        path = pathfinding.path.get_path(player_pos, loop_tar_loc)
        # check if we cango
        can_go = (
            config.COORD_DATA[loop_tar_loc]["cango"]
            and config.COORD_DATA[loop_tar_loc]["avoid"] == 0
        )
        #
        step += 1
    #
    if step <= limit:
        tar_loc = loop_tar_loc
    #
    return tar_loc
