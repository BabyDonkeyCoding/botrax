"""Academy Handling"""
import random
import time

import botrax_logger
import config
from player import Player
from travel import Travel
from util import functions, session_handler


def check_conditions(player):
    """Check if academy conditions are met"""
    target_location = None
    if player.get_invest():
        target_location = player.get_invest()["location"]
    #
    player_xp = player.get_xp()
    #
    factored_player_xp = int(
        player_xp * config.PLAYER_DATA["academy"]["academy_factor"]
    )
    #
    player_academylimit = player.get_academy_limit()
    #
    if (
        factored_player_xp <= player_academylimit
        or player_academylimit > player_xp + 100
        or (target_location and target_location in config.BLOCKED_LIST)
        or (target_location and target_location in config.CRATER_LIST)
    ):
        return False
    # return result
    return True


def get_hp_academy_costs() -> int:
    """Calculates the costs for HP academy"""
    costs = 7500
    skill_name = "Lebenstraining"
    if skill_name in config.PLAYER_DATA["abilities"]:
        # get current level of ability
        life_training_lvl = config.PLAYER_DATA["abilities"][skill_name]["cur_lvl"]
        # life academy costs
        if life_training_lvl == 50:
            costs = 4500
        else:
            costs = int(7500 * (0.99 ** int(life_training_lvl)))
    # return value
    return int(costs)

def study(player: Player):
    """Study at academy of life for more HP"""
    # not at right position
    if not player.get_invest() or player.get_pos() != player.get_invest()["location"]:
        return
    #
    anz_s = ""
    anz = player.get_gold() // get_hp_academy_costs()
    if anz < 1:
        return
    # we have enough gold for multiple courses
    if anz > 1:
        anz_s = "&anz=" + str(anz)
    # wait a random time
    wait = random.uniform(1, 1.5)
    time.sleep(wait)
    # request action
    session_handler.get(config.URL_MAIN + "?arrive_eval=kurs" + anz_s)
    # create debug message
    dbg_msg = "Took " + str(anz) + " course(s) at academy at " + str(player.get_pos())
    botrax_logger.MAIN_LOGGER.info(dbg_msg)
    # get current time
    now = int(time.time())
    player.get_invest()["last_action"] = now
    player.get_invest()["next_action"] = now + random.randint(1000, 10000)
    player.get_invest()["prepared"] = False
    # remove invest from player object
    player.set_invest(None)
    #
    player.update_player()
    # reset value back to default
    config.PLAYER_DATA["banking"]["min_char_gold"] = functions.get_min_char_gold()
    config.PLAYER_DATA["banking"]["max_char_gold"] = functions.get_max_char_gold()
    #
    player.set_travel(Travel.RANDOM)
    player.update_path(None)
    # wait random amount of time
    wait = random.uniform(1, 1.5)
    time.sleep(wait)
