"""Farming methodologies to collect more gold ingame
    """

import random
import time

import botrax_logger
import config
from pathfinding import path
from player import Player
from travel import Travel
from util import functions


def __get_next_farming_timestamp(base_interval: int) -> int:
    """Returns time for next farming"""
    #
    randomized_int = random.randint(
        round(base_interval * 1.1), round(base_interval * 5.5)
    )
    #
    return int(time.time()) + randomized_int


def handle_farming(player: Player):
    """Handle farming tasks

    Args:
        player (Player): player object
    """
    # check for stopping
    __check_for_stop(player)
    #
    if player.get_travel().value >= Travel.FARMING.value or not player.is_save_pos():
        return
    #
    p_farm = player.get_farm()
    #
    if p_farm:
        __start(player, p_farm)
        return
    #
    farm_list = config.PLAYER_DATA["farming"]
    #
    random.shuffle(farm_list)
    #
    now = int(time.time())
    #
    for farm_list_item in farm_list:
        # test this ?
        if "next_farm" in farm_list_item and (
            farm_list_item["next_farm"] >= 0 and now < farm_list_item["next_farm"]
        ):
            continue
        # get default amount
        def_amount = float(farm_list_item["amount_default"])
        # default amount has been set to low value
        if def_amount <= 0:
            continue
        #
        if def_amount < 1:
            max_amount = round(player.get_speed() * def_amount)
        else:
            max_amount = def_amount
        # select minimum amount to farm
        min_value = max(int(abs(max_amount / random.uniform(1.5, 4))), 1)
        #
        farm_list_item["amount"] = int(
            random.uniform(min_value, max_amount + random.randint(0, 4))
        )
        #
        has_auc_items, _, _, _ = player.get_item_overview()
        # we have auction items
        if (
            has_auc_items
            and player.get_gold() >= 250
            and farm_list_item["amount"]
            > (player.get_speed() - player.get_amount_items_carried())
        ):
            #
            target, _ = functions.get_closest_location(
                player.get_pos(), config.AH_LOCATIONS
            )
            #
            if not target:
                return
            #
            botrax_logger.MAIN_LOGGER.info("Walking to the AH at: %s", str(target))
            #
            player.set_destination(target)
            #
            player.set_travel(Travel.ITEM_TRADE)
            #
            return
        #
        __start(player, farm_list_item)
        return


def __start(player: Player, farm):
    # get needed farm data
    i_name = farm["name"]
    i_tar_amount = farm["amount"]
    # check calculated amount
    if i_tar_amount < 1:
        return
    # get player data
    p_item = player.get_item_by_name(i_name)
    p_item_amount = 0
    # get amount we already have
    if p_item:
        p_item_amount = p_item.get_amount()
    #
    if __check_for_stop(player):
        return
    #
    player.set_farm(farm)
    #
    area_field_list = config.LOCATION_DATA["farming_areas"][i_name]
    # shuffle the list to generate random routes everytime
    random.shuffle(area_field_list)
    #
    dbg_msg = "Preparing " + str(farm["name"]).upper() + " farming"
    botrax_logger.MAIN_LOGGER.info(dbg_msg)
    #
    path = __get_route_for_list(area_field_list, player.get_pos())
    #
    player.update_path(path)
    player.set_travel(Travel.FARMING)
    #
    dbg_msg = (
        "Start farming "
        + i_name.upper()
        + ", currently having "
        + str(p_item_amount)
        + "/"
        + str(i_tar_amount)
    )
    botrax_logger.MAIN_LOGGER.info(dbg_msg)


def __check_for_stop(player: Player) -> bool:
    stopping = False
    farm = player.get_farm()
    #
    if not farm:
        return stopping
    # get needed farm data
    i_name = farm["name"]
    i_tar_amount = farm["amount"]
    # get player data
    p_item = player.get_item_by_name(i_name)
    p_item_amount = 0
    # get amount we already have
    if not p_item:
        return stopping
    # get current amount on hand
    p_item_amount = p_item.get_amount()
    # we still need to farm more items
    if p_item_amount < i_tar_amount:
        return stopping
    # we finished farming
    stopping = stop_farm(player)
    # return results
    return stopping


def stop_farm(player: Player):
    """Checks if we stop farming

    Args:
        player (Player): _description_

    Returns:
        bool: _description_
    """
    stop = False
    current_farm = player.get_farm()
    if not current_farm:
        return stop
    #
    stop = True
    i_name = current_farm["name"]
    i_tar_amount = current_farm["amount"]
    current_farm["next_farm"] = __get_next_farming_timestamp(
        current_farm["base_interval"]
    )
    #
    dbg_msg = "Finished farming " + str(i_tar_amount) + " " + str(i_name).upper()
    botrax_logger.MAIN_LOGGER.info(dbg_msg)
    #
    player.set_farm(None)
    player.update_path(None)
    player.set_travel(Travel.RANDOM)
    #
    return stop


def __get_route_for_list(list_with_locations, start):
    """Returns a route that covers all locations from given list

    Args:
        list_with_locations (list): List with locations
        start (str): Start position

    Returns:
        list: List with all walking steps
    """
    # create long path for all npcs we have seen
    tar_path = []
    #
    loop_start_location = start
    #
    then = int(time.time())
    #
    for loc in list_with_locations:
        #
        tar_path.extend(path.get_path(loop_start_location, loc))
        loop_start_location = loc
    #
    duration = int(time.time()) - then
    #
    botrax_logger.MAIN_LOGGER.info("Route creation took %s seconds.", duration)
    #
    return tar_path
