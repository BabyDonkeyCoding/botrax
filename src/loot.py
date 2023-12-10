import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from util import session_handler
from player import Player


def check_field(res, player: Player):
    """Check field for items to pickup or get from special locations."""
    #
    __pick_up_from_location(res)
    #
    if "Du siehst keine Items an diesem Ort" in res.text:
        return res
    #
    res = __loot(res, player)
    #
    return res


def __pick_up_from_location(res):
    # get wissenszauber from reikan shop
    if "arrive_eval=wissenszauber" in res.text:
        #
        wait = random.uniform(1, 1.5)
        time.sleep(wait)
        #
        session_handler.get(config.URL_MAIN + "?arrive_eval=wissenszauber")
        #
        wait = random.uniform(2, 4)
        time.sleep(wait)


def __loot(res, player: Player):
    # retrieve data
    soup = BeautifulSoup(res.text, "lxml")
    # get all items on the floow
    items = soup.find_all("p", {"class": "listplaceitemsrow"})
    #
    items_carried = player.get_amount_items_carried()
    #
    looted_something = False
    #
    for item in items:
        # get links
        soup = BeautifulSoup(str(item.contents), "lxml")
        links = soup.find_all("a")
        # check all items on floor
        for link in links:
            # grab everything
            link_url = str(link.get("href"))
            if "action=takemoney" in link_url:
                # sleep to look more like human player
                wait = random.uniform(0.5, 1)
                time.sleep(wait)
                #
                botrax_logger.DEBUG_LOGGER.debug("Taking money from ground")
                #
                res = session_handler.get(config.URL_INTERNAL_BASE + link_url)
                continue
            # right now we do not want to harvest stuff
            if "Ernten" in str(link):
                continue
            # get player speed value
            p_speed = player.get_speed()
            # get parent element
            parent_soup = BeautifulSoup(str(item.contents), "lxml").find("b")
            #
            amount_soup = soup.find("span", {"class": "itemamount"})
            #
            amount = 1
            #
            if amount_soup:
                amount = int(re.sub("[^0-9]", "", amount_soup.text))
            # get item name from parent element
            i_name = parent_soup.text.strip()
            # check if the item is listed in the no pickup list
            if i_name in config.no_pickup_items:
                continue
            # check if we have too many items on hand
            if (
                i_name not in config.healing_items
                or (i_name in config.healing_items and player.get_item_by_name(i_name))
            ) and items_carried >= p_speed:
                continue
            # 
            if "action=take" in link_url:
                for _ in range(amount):
                    # sleep to look more like human player
                    wait = random.uniform(1, 1.5)
                    time.sleep(wait)
                    #
                    botrax_logger.DEBUG_LOGGER.debug("Looting: %s", i_name)
                    #
                    res = session_handler.get(config.URL_INTERNAL_BASE + link_url)
                    #
                    looted_something = True
    if looted_something:
        #
        player.update_player()
    # return current response
    return res
