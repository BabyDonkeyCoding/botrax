""" Module for player tasks to be performed."""
import datetime
import random
import time

import botrax_logger
import config
import quest
from chat import chat, chat_config
from player import Player
from player_abilities import phase_energy
from travel import Travel
from util import functions


def handle_tasks(player: Player) -> bool:
    """Does player tasks and returns True if we want to logout, otherwise returns False."""
    #
    player.update_player()
    # always use protection ;)
    __check_protection(player)
    # check for completed quests
    __check_quests()
    # check phase energy status
    phase_energy.check_phase_energy(player)
    # avoid logout when in development mode
    if config.DEVELOPER_MODE:
        return False
    # check for logout
    logout = __check_logout(player)
    # return logout request
    return logout


def __check_protection(player):
    # check if we have already protected the player
    if (
        "Schutz" in player.get_status()
        or player.get_gold()
        <= int(config.PLAYER_DATA["banking"]["max_char_gold"] * 2.5)
        or player.get_travel().value != Travel.INVESTMENTS.value
        or (player.get_invest() and player.get_invest()["type"] == "storage")
        or player.is_save_pos()
    ):
        return
    # use protection item
    if functions.use_item_by_name(player, "Schutzzauber"):
        #
        player.update_player(None)


def __check_logout(player):
    #
    if not player.is_save_pos():
        return False
    # get current time
    now = time.time()
    # get current hour
    c_hour = datetime.datetime.now().hour
    c_minute = datetime.datetime.now().minute
    # check if we need some time to sleep during night
    if (
        c_hour == config.LOGOUT_TARGET_HOUR and c_minute >= config.LOGOUT_TARGET_MINUTE
    ) or (c_hour > config.LOGOUT_TARGET_HOUR and (c_hour < 4 or c_hour > 21)):
        #
        config.LOGOUT_TARGET_HOUR = random.choice([22, 23])
        config.LOGOUT_TARGET_MINUTE = random.randint(1, 59)
        # get time we want to sleep
        wait = functions.get_night_break()
        #
        added_waittime = __get_random_day_off_time()
        #
        config.PLAYER_DATA["breaks"]["next_logout"] = (
            functions.get_next_logout() + wait + added_waittime
        )
        #
        sum_waittime = wait + added_waittime
        # set the waiting time
        config.RE_LOGIN_WAIT_TIME = sum_waittime
        # change the bot mode
        return True
    # LONG break
    if now > config.PLAYER_DATA["breaks"]["next_logout"]:
        # define how long to wait
        wait = _get_logout_break()
        #
        config.PLAYER_DATA["breaks"]["next_logout"] = functions.get_next_logout() + wait
        # set the waiting time
        config.RE_LOGIN_WAIT_TIME = wait
        # change the bot mode
        return True
    # SHORT break
    if now > config.PLAYER_DATA["breaks"]["next_break"]:
        # get random time for a short break
        wait = _get_short_break()
        #
        botrax_logger.MAIN_LOGGER.info(
            "I need a short break for %s seconds!", str(wait)
        )
        #
        if player.is_in_group():
            # shorten break time
            wait = int(wait /2)
            #
            chat.talk_with_chat(
                random.choice(chat_config.AFK_MESSAGES), chat.Chatchannel.GROUP
            )
        # take a short break
        time.sleep(wait)
        #
        botrax_logger.MAIN_LOGGER.info("Back from my break")
        #
        config.PLAYER_DATA["breaks"]["next_break"] = functions.get_next_break() + wait
        #
        if player.is_in_group():
            chat.talk_with_chat(
                random.choice(chat_config.RETURN_MESSAGES), chat.Chatchannel.GROUP
            )
    # return result
    return False


def __check_quests():
    # get current time
    now = time.time()
    # check time against variable
    if now >= config.NEXT_QUEST_CHECK:
        # try to claim quests
        quest.claim_quests()
        # set new timestamp for next check
        config.NEXT_QUEST_CHECK = now + random.randint(140, 600)


def __get_random_day_off_time() -> int:
    # init variable
    added_waittime = 0
    # by a chance of 15% we are taking a whole day off
    if functions.get_chance(0.06):
        added_waittime = _get_day_break()
    #
    elif functions.get_chance(0.02):
        added_waittime = _get_days_break()
    #
    return added_waittime

def _get_short_break() -> int:
    """Returns the short break duration in seconds"""
    return random.randint(125, 745)


def _get_logout_break() -> int:
    """Returns the short break duration in seconds"""
    return random.randint(1500, 4500)


def _get_day_break() -> int:
    """Returns the length of the break longer than a day"""
    return int(random.randint(37000, 46000))

def _get_days_break() -> int:
    """Returns the length of the break longer than a day"""
    return int(random.randint(46000, 65000))