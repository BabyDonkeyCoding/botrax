# _ring_ability_ready
# https://weltxyz.freewar.de/freewar/internal/item.php?action=activate&act_item_id=493928489
# https://weltxyz.freewar.de/freewar/internal/item.php?action=activate&act_item_id=493928489&ring_action=activate
# https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=rselect
# 77|87
# https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=rselect2&act_item_id=491575075
#
# https://weltxyz.freewar.de/freewar/internal/item.php?action=activate&act_item_id=491575075&ring_action=activate

import multiprocessing
import random
import time

import botrax_logger
import config
from util import session_handler
import travel
from player import Player

IN_PROCESS = False
KNOWLEDGE_RING_THRESHOLD = int((3600 * 24 * 14) + 36000)
KNOWLEDGE_RING_NAME = "Ring des Wissbegierigen"
RING_EQUIP_LOCATION = "77|87"


def check_ring(res, player: Player):
    """ "Method performs all necessary checks for knowledge ring"""
    # check if we already have a ring
    if player.get_ring():
        # check if we can use the ring
        __ability_ready(player)
        # return if we already have a ring
    elif (
        config.PLAYER_DATA["last_knowledge_ring"]
        < time.time() - KNOWLEDGE_RING_THRESHOLD
    ):
        # pick up the ring
        __pick_up(res, player)
        # equip the ring
        __equip_knowledge_ring(player)


def __equip_knowledge_ring(player: Player):
    knowledge_ring_item = player.get_item_by_name(KNOWLEDGE_RING_NAME)
    # check if successfully taken
    if (
        knowledge_ring_item
        and player.get_pos() != RING_EQUIP_LOCATION
        and player.get_travel().value < travel.Travel.INVESTMENTS.value
    ):
        #
        player.set_destination(RING_EQUIP_LOCATION)
        player.set_travel(travel.Travel.INVESTMENTS)
        botrax_logger.MAIN_LOGGER.info(
            "Walk to jeweler to equip knowledge ring at %s", RING_EQUIP_LOCATION
        )
    if knowledge_ring_item and player.get_pos() == RING_EQUIP_LOCATION:
        time.sleep(random.randint(1, 3))
        # open menu
        res = session_handler.get(
            "https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=rselect"
        )
        time.sleep(random.randint(1, 3))
        #
        config.PLAYER_DATA["last_knowledge_ring"] = int(time.time())
        #
        if "arrive_eval=rselect2&act_item_id=" in res.text:
            # equip ring
            session_handler.get(
                "https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=rselect2&act_item_id="
                + str(knowledge_ring_item.get_id())
            )
            # set current time for equipped time
            time.sleep(random.randint(1, 3))
            #
            botrax_logger.MAIN_LOGGER.info("Equipped knowledge ring")


def __pick_up(res, player):
    # https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=wissensring
    if "?arrive_eval=wissensring" in res.text:
        # take the ring
        session_handler.get(
            "https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=wissensring"
        )
        #
        player.update_player()


def __ability_ready(player: Player):
    # not ready
    if not player._ring_ability_ready:
        return
    #
    item = player.get_item_by_name(player.get_ring())
    if not item or IN_PROCESS:
        return
    #
    process = multiprocessing.Process(
        name="Use ring", target=__use_ring, args=(player,)
    )
    process.start()


def __use_ring(player: Player):
    global IN_PROCESS
    IN_PROCESS = True
    #
    wait = random.uniform(6, 47)
    time.sleep(wait)
    #
    item_id = str(player.get_item_by_name(player.get_ring()).get_id())
    #
    session_handler.get(config.URL_USE_ITEM + item_id)
    #
    session_handler.get(config.URL_USE_ITEM + item_id + "&ring_action=activate")
    # debug output
    dbg_msg = "Used Ring: " + player.get_ring()
    #
    botrax_logger.DEBUG_LOGGER.debug(dbg_msg)
    #
    IN_PROCESS = False
