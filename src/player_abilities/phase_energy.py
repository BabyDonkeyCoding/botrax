"""Module for phase energy handling"""
import config


def __get_taunektarbier():
    item = {}
    item["name"] = "Flasche Taunektarbier"
    item["min"] = 0
    item["max"] = 0
    item["location"] = "100|88"
    item["id"] = 315
    item["avg_price"] = 35
    return item


def check_phase_energy(player):
    """Check if we need alternative healing item"""
    # check if we have unlocked the ability
    if player.get_phase_energy_max() < 0:
        return
    #
    if player.get_phase_energy_cur() > (player.get_phase_energy_max() / 2):
        # reset consumable needed amount
        for item in config.PLAYER_DATA["consumables"]:
            if item["name"] == "Flasche Taunektarbier":
                item["min"] = 0
                item["max"] = 0
        # return back
    else:
        # adjust existing consumable
        for item in config.PLAYER_DATA["consumables"]:
            if item["name"] == "Flasche Taunektarbier":
                item["min"] = 1
                item["max"] = 0.2
                return
        # add new consumable
        con_item = __get_taunektarbier()
        con_item["min"] = 1
        con_item["max"] = 0.2
        config.PLAYER_DATA["consumables"].append(con_item)
