"""Module for items handling at the bank"""
import random
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from util import session_handler

MAX_STORAGE_ITEMS = 690


def check_storage(res, player):
    """Check bank storage"""
    # https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=itemmitnahme&kat=6&fastback=1
    if not res or "?arrive_eval=itemmitnahme&kat=6&fastback=1" not in res.text:
        return
    # get all items in storage
    __get_storage_contents(player)
    # put items in storage if necessary
    __put_items_in_storage(player)
    # get all items in storage
    __get_storage_contents(player)
    # get item from storage
    __get_items_from_storage(player)


def __get_storage_contents(player):
    #
    res = session_handler.get(config.URL_EMPTY_STORAGE_MENU)
    if not res:
        return
    #
    storage_items = {}
    #
    links = BeautifulSoup(res.text, "lxml").find_all("a")
    #
    for link in links:
        href = link.get("href")
        if href and "?arrive_eval=itemmitnahme2&fastback=1&kat=6&" in href:
            #
            parent = link.parent.parent
            #
            list_i_name = (
                str(parent.contents[0].contents[0].contents[0].text.strip())
                .replace("(M+)", "")
                .replace("(M)", "")
                .strip()
            )
            #
            amount = link.previous_sibling.previous_sibling.text
            amount_s = 1
            #
            if amount:
                amount_s = int(amount)
            #
            storage_items[list_i_name] = amount_s
    #
    player.set_storage_items(storage_items)


def __put_items_in_storage(player):
    # open menu
    res = session_handler.get(config.URL_PUT_ITEMS_IN_STORAGE_MENU)
    if not res:
        return
    # ITEM https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=itemabgabe2&abgabe_item=383692535
    # get all links
    links = BeautifulSoup(res.text, "lxml").find_all("a")
    # walk through links
    for link in links:
        # get href from link
        href = link.get("href")
        # check if we have found a link we are looking for
        if not href or "arrive_eval=itemabgabe2&abgabe_item=" not in href:
            # skip this link for further processing
            continue
        # init variables
        item_name = link.parent.parent.contents[0].contents[0].contents[0].text.strip()
        #
        player_item = player.get_item_by_name(item_name)
        #
        if not player_item or player_item.is_equipped():
            continue
        #
        to_store_amount = 0
        # item shall not be stored
        if item_name not in config.PLAYER_DATA["banking"]["storage"]:
            continue
        # get amount we want to store
        target_amount = int(config.PLAYER_DATA["banking"]["storage"][item_name])
        #
        if target_amount < 0:
            to_store_amount = player_item.get_amount()
        elif item_name not in player.get_storage_items():
            to_store_amount = target_amount
        else:
            to_store_amount = target_amount - int(player.get_storage_items()[item_name])
        # nothing to store
        if to_store_amount <= 0:
            # skip
            continue
        # we have to store some amount
        if to_store_amount > 1:
            href += "&anzahl=" + str(to_store_amount)
        # store item
        session_handler.get(config.URL_INTERNAL_BASE + href)
        #
        dbg_s = str(to_store_amount) + " " + str(item_name)
        #
        dbg_msg = f"Putting {dbg_s} to the bank storage"
        #
        botrax_logger.DEBUG_LOGGER.info(dbg_msg)
        #
        wait = random.uniform(1.25, 4)
        time.sleep(wait)


def __get_items_from_storage(player):
    #
    res = session_handler.get(config.URL_EMPTY_STORAGE_MENU)
    if not res:
        return
    #
    links = BeautifulSoup(res.text, "lxml").find_all("a")
    #
    for link in links:
        #
        href = link.get("href")
        if (
            not href
            or "?arrive_eval=itemmitnahme2&fastback=1&kat=6&mit_item" not in href
        ):
            continue
        #
        parent = link.parent.parent
        #
        list_i_name = (
            str(parent.contents[0].contents[0].contents[0].text.strip())
            .replace("(M+)", "")
            .replace("(M)", "")
            .strip()
        )
        #
        list_item = None
        if list_i_name in config.ITEM_DATA:
            list_item = config.ITEM_DATA[list_i_name]
        #
        if not list_item:
            continue
        # init variables
        pickup_amount = 0
        tar_storage_amount = 0
        #
        if list_i_name in config.PLAYER_DATA["banking"]["storage"]:
            # get amount we want to store
            tar_storage_amount = int(
                config.PLAYER_DATA["banking"]["storage"][list_i_name]
            )
        # we want to store all items?
        if tar_storage_amount < 0:
            # skip
            continue
        #
        pickup_amount = (
            int(player.get_storage_items()[list_i_name]) - tar_storage_amount
        )
        #
        if pickup_amount <= 0:
            continue
        #
        if pickup_amount > 1:
            href += "&anzahl=" + str(pickup_amount)
        #
        res = session_handler.get(config.URL_INTERNAL_BASE + href)
        #
        dbg_s = str(pickup_amount) + "x " + list_i_name
        #
        dbg_msg = f"Taking {dbg_s} from bank storage"
        #
        botrax_logger.DEBUG_LOGGER.debug(dbg_msg)
        #
        wait = random.uniform(1.25, 4)
        time.sleep(wait)
