"""Module for handling dungeons"""
# Entry grave https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=oben1139
# Exit grave https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=oben1159

# https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=unten325
# last_dungeon_transition

import random
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
import dungeons.dungeon_utils as du
from move import movement_functions
from util import session_handler
from travel import Travel


def check_dungeon(res, player):
    """Check whether or not we want to enter or leave a dungeon."""
    # dungeon transitions blocked
    if (
        player.get_path()
        or player.get_travel().value >= Travel.NPC_HUNTING.value
        or player.get_pos() in config.PLAYER_DATA["dungeons"]["avoid"]
        or "Portal in die Unterwelt" in res.text
        or any(key in res.text for key in config.PLAYER_DATA["dungeons"]["avoid"])
    ):
        return
    # get current time
    now = int(time.time())
    #
    __init_dungeons_player_data(now)
    # get soup object from server response
    soup = BeautifulSoup(res.text, "lxml")
    # get all links from server response
    links = soup.find_all("a")
    #
    ref_tags = [
        "?arrive_eval=oben",
        "?arrive_eval=unten",
        "?arrive_eval=rausgehen",
        "?do=treppe",
    ]
    #
    link_text_tags = ["verlassen", "betreten", "steigen"]
    # loop through all links
    for link in links:
        # get link reference
        href = str(link.get("href"))
        # we are at a dungeon exit
        if (
            any(key in href for key in ref_tags)
            or
            any(key in link.text for key in link_text_tags)
        ) and config.PLAYER_DATA["dungeons"]["next_dungeon_transition"] <= now:
            # check for exit
            if player.get_posx() < 0 and player.get_posy() < 0:
                # log
                botrax_logger.MAIN_LOGGER.info(
                    "<<< Leaving Dungeon at position %s", player.get_pos()
                )
                #
                __do_dungeon_transition(href, player)
            # check for entrance
            elif (
                player.get_posx() > 0
                and player.get_posy() > 0
                and (
                    href not in config.PLAYER_DATA["dungeons"]["visited"]
                    or config.PLAYER_DATA["dungeons"]["visited"][href]
                    <= now - du.DUNGEON_ENTERING_THRESHOLD
                )
            ):
                #
                botrax_logger.MAIN_LOGGER.info(
                    ">>> Entering Dungeon at position %s", player.get_pos()
                )
                #
                config.PLAYER_DATA["dungeons"]["visited"][href] = now
                # enter dungeon
                __do_dungeon_transition(href, player)
                #
                player.set_travel(Travel.RANDOM)


def __init_dungeons_player_data(now):
    if "dungeons" not in config.PLAYER_DATA:
        config.PLAYER_DATA["dungeons"] = {}
        config.PLAYER_DATA["dungeons"]["visited"] = {}
    #
    if "next_dungeon_transition" not in config.PLAYER_DATA["dungeons"]:
        config.PLAYER_DATA["dungeons"]["next_dungeon_transition"] = now
    if "visited" not in config.PLAYER_DATA["dungeons"]:
        config.PLAYER_DATA["dungeons"]["visited"] = {}


def __do_dungeon_transition(href, player):
    # get current time stamp
    now = int(time.time())
    # enter dungeon
    session_handler.get(config.URL_MAIN + href.replace("main.php", ""))
    # set time for this dungeon transition
    config.PLAYER_DATA["dungeons"]["next_dungeon_transition"] = now + random.randint(
        15, 25
    )
    # get current position
    pos_x, pos_y = movement_functions.get_current_position(None)
    #
    player.set_posx(int(pos_x))
    player.set_posy(int(pos_y))
