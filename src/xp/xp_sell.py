"""Academy Handling"""
import random
import time

import botrax_logger
import config
from player import Player
from travel import Travel
from util import session_handler

XP_SELL_LOCATION = "80|94"


def __get_next_xp_sell_timestamp() -> int:
    """Returns the next xp sell time stamp"""
    return int(time.time()) + int(random.randrange(50000, 500000, 100))


def __get_next_max_xp_sell() -> int:
    """Returns the next max xp value to sell"""
    return int(random.randrange(300, 2501, 50))


def check_xp_sell(res, player: Player):
    """Check everything for study tasks"""
    # check config
    if "next_xp_sell_amount" not in config.PLAYER_DATA["academy"]:
        config.PLAYER_DATA["academy"]["next_xp_sell_amount"] = __get_next_max_xp_sell()
    # check travel mode
    if player.get_travel().value > Travel.XP_SELL.value:
        return
    # check timing
    now = int(time.time())
    if now < int(config.PLAYER_DATA["academy"]["next_xp_sell"]):
        return
    # check min xp sell type has been set
    if (
        "min_academy_xpsell" not in config.PLAYER_DATA["academy"]
        or config.PLAYER_DATA["academy"]["min_academy_xpsell"] < 0
    ):
        return
    # check current XP agains minimum xp limit
    if (
        player.get_xp()
        < config.PLAYER_DATA["academy"]["min_academy_xpsell"]
        + config.PLAYER_DATA["academy"]["next_xp_sell_amount"]
    ):
        return
    # define a offset we want to add to the academy limit
    # to avoid going under 100% unnecessarily
    academy_limit_safety_offset = 250
    # calculated targeted academy limit
    if player.get_academy_limit() + academy_limit_safety_offset > round(
        player.get_xp() * float(config.PLAYER_DATA["academy"]["academy_factor"])
    ):
        return
    # check location
    if player.get_pos() == XP_SELL_LOCATION:
        # sell XP
        __sell_xp(res, player)
    elif player.get_travel().value < Travel.XP_SELL.value:
        # set route to xp selling tower
        # get location to sell XP
        target = XP_SELL_LOCATION
        # debug message
        botrax_logger.MAIN_LOGGER.info(
            "Walking to the dark tower to sell XP at location: %s", str(target)
        )
        # set target to player
        player.set_destination(target)
        player.set_travel(Travel.XP_SELL)


def __sell_xp(res, player: Player):
    # get the target xp value
    target_xp_value = round(
        player.get_xp() * float(config.PLAYER_DATA["academy"]["academy_factor"])
    )
    # calculate the amount xp we want to spend
    xp_selling_amount = target_xp_value - player.get_academy_limit()
    # round to nearest 10
    xp_selling_amount = round(xp_selling_amount, -2)
    # limit xp selling to maximum amount in player config
    xp_selling_amount = min(
        xp_selling_amount, config.PLAYER_DATA["academy"]["next_xp_sell_amount"]
    )
    # we can spend XP and are at the right position
    if (
        "arrive_eval=xpsaug" in res.text
        and xp_selling_amount > 0
        and player.get_xp() - xp_selling_amount
        > config.PLAYER_DATA["academy"]["min_academy_xpsell"]
    ):
        #
        time.sleep(random.uniform(1, 3))
        # change xp to money
        session_handler.get(
            config.URL_MAIN + "?arrive_eval=xpsaug&anz=" + str(xp_selling_amount)
        )
        # debug message
        dbg_msg = "Sold " + str(xp_selling_amount) + " XP"
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # set next xp selling amount
        config.PLAYER_DATA["academy"]["next_xp_sell_amount"] = __get_next_max_xp_sell()
        # wait a bit
        time.sleep(random.uniform(0.5, 2))
    # set next xp selling timestamp
    config.PLAYER_DATA["academy"]["next_xp_sell"] = __get_next_xp_sell_timestamp()
    #
    player.set_invest(None)
