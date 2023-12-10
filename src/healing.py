import math
import random
import time

import botrax_logger
import config
from player import Player
from travel import Travel
from util import functions, session_handler

URL_DRINK_WATER = (
    "http://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=drinkwater"
)
URL_DRINK = "http://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=drink"
URL_DRINK_BEER = (
    "http://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=drinkbeer"
)

NEXT_HEALING = int(time.time())


def heal_player(res, player: Player, in_combat: bool):
    """Heal player

    Args:
        res (response): Response
        session (session): Session
        player (Player): Player object
        in_combat (bool): boolean
    """
    # check player hp
    if player.get_hp() == player.get_max_hp():
        return
    #
    healed = __heal_field(res, player)
    #
    if healed:
        player.update_player()
        return
    #
    healed = heal_from_items(player, in_combat)
    #
    if healed:
        player.update_player()
        return
    #
    __walk_to_healing(player)


def __walk_to_healing(player: Player):
    # there are no healing locations saved
    if "healind" not in config.LOCATION_DATA or not config.LOCATION_DATA["healing"]:
        return
    # we have enough health or not enough gold
    if (
        player.get_hp() > math.floor(player.get_max_hp() / 2)
        or player.get_travel().value >= Travel.HEALING.value
        or player.get_gold() <= 20
    ):
        return
    # get closest healing location
    target, _ = functions.get_closest_location(
        player.get_pos(), config.LOCATION_DATA["healing"]
    )
    # search gave no results
    if not target:
        return
    # we have all data we need, walk to the location
    dbg_msg = "Walking to " + target + " for healing"
    # output to logger
    botrax_logger.MAIN_LOGGER.info(dbg_msg)
    # update player data
    player.set_destination(target)
    player.set_travel(Travel.HEALING)


def __heal_field(res, player: Player) -> bool:
    # take free healing from tower
    healed = False
    txt = res.text
    if "arrive_eval=drink" not in txt or player.get_pos() in config.no_drinking_pos:
        return
    # prefer healing on towers
    if "Kontrollturm" in txt and "arrive_eval=drinkwater" in txt:
        wait = random.uniform(1, 1.5)
        time.sleep(wait)
        # drink from water to heal
        session_handler.get(URL_DRINK_WATER)
        #
        if player.get_travel() == Travel.HEALING:
            player.set_travel(Travel.RANDOM)
        #
        healed = True
        #
        return healed
    p_pos = player.get_pos()
    # reset travel mode
    if player.get_travel() == Travel.HEALING:
        player.set_travel(Travel.RANDOM)
    # health seems low, drink beer first
    if "arrive_eval=drinkbeer" in txt:
        #
        now = int(time.time())
        #
        p_hp = player.get_hp()
        p_max_hp = player.get_max_hp()
        #
        while p_hp < p_max_hp or int(time.time()) < now + 30:
            wait = random.uniform(0.5, 1)
            time.sleep(wait)
            # drink beer to heal
            session_handler.get(URL_DRINK_BEER)
            #
            player.update_player()
            #
            p_hp = player.get_hp()
            p_max_hp = player.get_max_hp()
        #
        return True
    #
    calc = player.get_hp() / player.get_max_hp()
    #
    hp_perc = round(calc * 100)
    # drink water as last option
    # drink water from pot
    if "arrive_eval=drink" in txt and p_pos == "76|110":
        wait = random.uniform(1, 1.5)
        time.sleep(wait)
        # drink from water to heal
        session_handler.get(URL_DRINK)
        #
        return True
    if "arrive_eval=drinkwater" in txt:
        #
        if hp_perc > 90 and p_pos != "87|112":
            return False
        #
        wait = random.uniform(1, 1.5)
        time.sleep(wait)
        # drink from water to heal
        session_handler.get(URL_DRINK_WATER)
        #
        player.update_player()
        return True
    #
    return False


def heal_from_items(player: Player, in_combat) -> bool:
    """Heal player by using items

    Args:
        player (Player): player object
        in_combat (_type_): Flag whether or not we are in combat

    Returns:
        bool: True if successfully healed, false otherwise
    """
    global NEXT_HEALING
    #
    if player.get_hp() == player.get_max_hp():
        return False
    #
    healed = False
    now = int(time.time())
    # try item healing
    healing_items_carried = player.get_healing_items()
    # get consumables
    consumables = []
    for cl_item in config.PLAYER_DATA["consumables"]:
        consumables.append(cl_item["name"])
    #
    has_non_consumable_healing = False
    for item in healing_items_carried:
        item_name = item.get_name()
        if item_name not in consumables:
            has_non_consumable_healing = True
    #
    for item in healing_items_carried:
        # item is a healing item and we have hp deficit greater or equal to amount item will heal us for
        item_name = item.get_name()
        #
        if item_name in consumables and has_non_consumable_healing and not in_combat:
            continue
        #
        if (
            item_name == "energetischer Heilzauber"
            and player.get_phase_energy_cur() < 500
        ):
            continue
        #
        item_healing = config.healing_items.get(item_name)
        #
        if item_healing < 0:
            item_healing = player.get_max_hp()
        #
        for _ in range(item.get_amount()):
            #
            current_hp = player.get_hp()
            #
            #
            if player.get_hp() == player.get_max_hp():
                break
            #
            healing_delta_reached = current_hp <= (player.get_max_hp() - item_healing)
            #
            critical_hp = current_hp <= math.ceil(
                int(player.get_max_hp()) * random.uniform(0.1, 0.15)
            )
            #
            if (
                (healing_delta_reached and now >= NEXT_HEALING)
                or in_combat
                or critical_hp
            ):
                # use item
                item_id = str(item.get_id())
                #
                wait = random.uniform(1, 1.5)
                time.sleep(wait)
                res = session_handler.get(
                    config.URL_ITEM + "?action=activate&act_item_id=" + item_id
                )
                # set last time we healed
                NEXT_HEALING = now + random.randint(10, 15)
                #
                player.update_player(res)
                #
                healed = True
    #
    if healed:
        player.update_player()
    # return result
    return healed
