import random
import time

import config
from util import session_handler


def tower_control_ability(player):
    """Use tower ability if available"""
    #
    now = time.time()
    #
    if (
        player.get_pos() not in config.BANKING_LOCATIONS
        and player.get_pos() not in config.AH_LOCATIONS
        and now >= config.NEXT_TOWER_ABILITY_USE
        and not player.is_save_pos()
    ):
        # https://weltxyz.freewar.de/freewar/internal/item.php?action=towercontrol&use
        session_handler.get(config.URL_ITEM + "?action=towercontrol&use")
        #
        config.NEXT_TOWER_ABILITY_USE = now + random.randint(610, 695)
