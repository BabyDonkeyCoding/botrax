"""Module for auction house actions"""
import math
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
import farming
from util import session_handler, functions
from trade import trade_conf as tc
from item import ItemCategory, ItemSellType
from player import Player


def use(res, player: Player):
    """Trade at auction house

    Args:
        res (_type_): response from server
        session (session): session
        player (Player): player object
    """
    if (
        player.get_pos() not in config.AH_LOCATIONS
        or player.get_pos() in config.BLOCKED_LIST
    ):
        return
    # arrived set next timestamp
    tc.NEXT_AH_SELL = functions.get_next_trade_timestamp()
    # arrived at auction house and therefore will sell all farmed items
    farm = player.get_farm()
    if farm and player.get_item_by_name(farm["name"]):
        farming.stop_farm(player)
    # clean no sell values
    __clean_data("no_sell", tc.MAX_NO_SELL_AGE)
    __clean_data("offer", tc.MAX_OFFER_AGE)
    __clean_data("sold", tc.MAX_SOLD_AGE)
    #
    __update_auction_item_prices()
    #
    __auction_buy_items(res, player)
    #
    __auction_off_items(res, player)


def __clean_data(key, max_age):
    now = int(time.time())
    for item in config.ITEM_DATA.items():
        if "auction" not in config.ITEM_DATA[str(item[0])]:
            continue
        auction = config.ITEM_DATA[str(item[0])]["auction"]
        #
        if key not in auction:
            continue
        #
        to_delete = []
        #
        for sub_item in auction[key]:
            if int(sub_item) < now - max_age:
                to_delete.append(sub_item)
        # remove items
        for todelete in to_delete:
            del auction[key][todelete]
        #


def __update_auction_item_prices():
    # https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=itembuy&cat=1&cheapbuy=1
    # get current timestamps
    now = int(time.time())
    # check threshold of auction scan
    if now > config.NEXT_AUCTION_ITEM_SCAN:
        return
    #
    config.NEXT_AUCTION_ITEM_SCAN = now + random.uniform(3600, 7200)
    # walk through categories
    for item_category in ItemCategory:
        #
        time.sleep(random.uniform(1, 4))
        #
        url = (
            config.URL_MAIN
            + "?arrive_eval=itembuy&cat="
            + str(item_category.value)
            + "&cheapbuy=1"
        )
        res = session_handler.get(url)
        #
        time.sleep(random.uniform(2, 8))
        #
        line_breaks = BeautifulSoup(res.text, "lxml").find_all("br")
        #
        for line_break in line_breaks:
            # check for correct link
            sibling = line_break.next_sibling
            if sibling.name != "b":
                continue
            # init variables
            i_name = ""
            i_price = 0
            price_s = ""
            #
            i_name = sibling.text
            while "für" not in price_s and sibling.next_sibling:
                sibling = sibling.next_sibling
                price_s = str(sibling).strip()
            #
            seller_name = price_s
            # skip items sold by player
            if config.PLAYER_DATA["username"].casefold() in seller_name.casefold():
                continue
            #
            regex_result = re.findall(r"für \d{1,3}.\d{1,3}.\d{1,3} Gold", sibling)
            if len(regex_result) == 0:
                continue
            #
            offer_price_s = re.sub("[^0-9]", "", regex_result[0])
            #
            i_price = int(offer_price_s)
            #
            item_data = {}
            #
            if i_name in config.ITEM_DATA and isinstance(
                config.ITEM_DATA[i_name], dict
            ):
                item_data = config.ITEM_DATA[i_name]
            # remove old offer price entry if existing
            if "auction_offer_price" in item_data:
                del item_data["auction_offer_price"]
            # remove old category entry if existing
            if "category" in item_data:
                del item_data["category"]
            # init auction data
            auction_data = {}
            if "auction" in item_data:
                auction_data = item_data["auction"]
            # get no sell dictionary
            offer_data = {}
            if "offer" in auction_data:
                offer_data = auction_data["offer"]
            # init last timestamp value with current time
            last_timestamp = now
            # check amount of keys in the offer_data dictionary
            if len(offer_data) > 0:
                # extract keys a list of integers
                key_list = (int(k) for k in offer_data.keys())
                # check for sale value
                has_value = any(k == i_price for k in offer_data.values())
                # get maxmimum value as int
                last_timestamp = int(max(key_list))
                # check if the last timestamp is longer ago than we want
                if last_timestamp >= now - 14400 or has_value:
                    continue
            # write new data to dictionary
            offer_data[now] = i_price
            # shorten the list to limit data size
            if len(offer_data) > config.ITEM_DATA_SIZE_LIMIT:
                for key in list(offer_data.keys()):
                    if list(offer_data.keys()).index(key) > config.ITEM_DATA_SIZE_LIMIT:
                        del offer_data[key]
            # add offer data to auction dictionary
            auction_data["offer"] = offer_data
            # add category data to auction dictionary
            auction_data["category"] = item_category.name
            # write auction data to item dictionary
            item_data["auction"] = auction_data
            #
            config.ITEM_DATA[i_name] = item_data
            #
            __check_buy_option(i_name,i_price)


def __check_buy_option(i_name, i_price):
    # check if we have sold this item
    if i_name not in config.ITEM_DATA or (
        i_name in config.ITEM_DATA[i_name]
        and "sold" not in config.ITEM_DATA[i_name]
    ):
        return
    # get average selling price for this item
    db_selling_price = __get_selling_price(i_name, True)
    # price is higher than 90% of what we usually sell for
    if i_price > math.ceil(db_selling_price * 0.9):
        return
    #
    print(f"Found cheap {i_name} with price {i_price}")


def __auction_buy_items(res, player: Player):
    # https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=itemabgabe
    # check for auction house on field
    res = session_handler.get(config.URL_MAIN + "?arrive_eval=itembuy&cat=3&cheapbuy=1")
    #
    if not res:
        return
    # check consumables
    for c_item in config.PLAYER_DATA["consumables"]:
        # not on auction house item or not enough gold to buy it
        if (
            "location" in c_item
            or int(player.get_gold()) < c_item["avg_price"]
            or c_item["name"] in config.UNAVAILABLE_ITEMS
        ):
            continue
        #
        amount = 0
        # get amout on hand
        player_amount = player.get_amount_by_name(c_item["name"])
        # check how much we need to buy
        amount = int(c_item["max"]) - player_amount
        # we have enough items available
        if amount <= 0:
            continue
        # init variables for further processing
        found_item = False
        i_name = str(c_item["name"])
        # walk through amount of items we need
        for _ in range(amount):
            #
            found_item = False
            #
            links = BeautifulSoup(res.text, "lxml").find_all("a")
            #
            for link in links:
                #
                if "kaufen" not in link.text:
                    continue
                #
                auction_item_name = (
                    link.previous_sibling.previous_sibling.previous_sibling.previous_sibling.text
                )
                #
                if i_name != auction_item_name:
                    continue
                # sleep to look more like human player
                wait = random.uniform(2, 3)
                time.sleep(wait)
                #
                url = link.get("href")
                # buy the item
                res = session_handler.get(config.URL_INTERNAL_BASE + url)
                #
                botrax_logger.MAIN_LOGGER.info(
                    "Bought %s from auction house", auction_item_name
                )
                # sleep to look more like human player
                wait = random.uniform(1, 2)
                time.sleep(wait)
                #
                found_item = True
                #
                break
        #
        if not found_item:
            #
            config.UNAVAILABLE_ITEMS[i_name] = int(time.time())
            #
            botrax_logger.MAIN_LOGGER.info(
                "%s not available at auction house! Will check back later", i_name
            )


def __auction_off_items(res, player: Player):
    # https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=itemabgabe
    # check for auction house on field
    if int(player.get_gold()) < 200:
        return
    # wait artificially to simulate input
    time.sleep(random.uniform(1, 1.5))
    # open the menu
    sell_menu = session_handler.get(config.URL_AUCTION_SELL_MENU)
    # no sell menu available
    if not sell_menu:
        return
    # get undercut value from config
    undercut = config.PLAYER_DATA["auction"]["undercut"]
    # walk through the player items
    for idx, p_item in enumerate(player.get_items()):
        # check if the item is auctionable
        if not p_item.is_auctionable():
            continue
        # init variables
        recommended_price_url = None
        i_name = None
        item_amount = 0
        res = None
        db_selling_price = 0
        i_name = p_item.get_name()
        # player item not listed in auction house sell menu
        if i_name not in sell_menu.text:
            player.get_items()[idx].set_auctionable(False)
            continue
        # item is not for auction selling
        if p_item.get_sell_type() != ItemSellType.AUCTION:
            continue
        # get amount of items we have on hand
        item_amount = p_item.get_amount()
        # deduct one if it is equipped
        if i_name in player.get_equipped_items():
            item_amount = player.get_amount_by_name(i_name) - 1
        # check for remaining amount
        if item_amount <= 0:
            continue
        #
        item_amount = str(item_amount)
        # build url for the item
        recommended_price_url = (
            config.URL_MAIN
            + "?arrive_eval=itemabgabe2&abgabe_item="
            + str(p_item.get_id())
            + "&anz="
            + item_amount
        )
        # get page with recommended price for the item we want to sell
        res = session_handler.get(recommended_price_url)
        # get the conents
        soup = BeautifulSoup(res.text, "lxml")
        #
        input_element = soup.find("select", {"name": "angebote"})
        #
        if not input_element:
            continue
        #
        text = input_element.contents[0].text
        # define mininum price for item
        min_selling_price = 0
        if (
            i_name in config.ITEM_DATA
            and "shop" in config.ITEM_DATA[i_name]
            and "shop_price" in config.ITEM_DATA[i_name]["shop"]
        ):
            item = config.ITEM_DATA[i_name]
            # create a list with all values
            lst = list(item["shop"]["shop_price"].values())
            # calculate average offering price
            min_selling_price = int(math.ceil(sum(lst) / len(lst)) + 5)
        #
        selling_price = int(input_element.contents[0].get("value"))
        # no competitors in auction house and we have it in list
        if "Mittlerer Shopwert" in text:
            min_selling_price = max(
                int(math.ceil((selling_price + 5) * 1.05) + 5), min_selling_price
            )
            # in case we have offer data, calculate a price on basis of database
            db_selling_price = __get_selling_price(i_name)
            selling_price = max(min_selling_price, db_selling_price)
        elif not (
            any(key in text for key in config.PLAYER_DATA["team"])
            or str(" ") + config.PLAYER_DATA["username"] + str(" ") in text
        ):
            # calculate new selling price
            cutaway = selling_price - int(math.floor(selling_price * undercut))
            # cut at least one gold from the price
            cutaway = max(cutaway, 1)
            # calculate new selling price
            selling_price = int(selling_price - cutaway)
        #
        if selling_price < min_selling_price:
            p_item.set_auctionable(False)
            continue
        # check against fixed prices
        if (
            "fixed_prices" in config.PLAYER_DATA["auction"]
            and i_name in config.PLAYER_DATA["auction"]["fixed_prices"]
        ):
            selling_price = int(config.PLAYER_DATA["auction"]["fixed_prices"][i_name])
        # sell the item
        url = config.URL_MAIN + "?arrive_eval=itemabgabe3"
        # abgabe_item=483664254&angebote=40&anz=1&money=40&time_days=0&Submit=Zum+Verkauf+geben
        # create login payload data
        auction_post_data = {
            "abgabe_item": str(p_item.get_id()),
            "angebote": str(selling_price),
            "anz": item_amount,
            "money": str(selling_price),
            "time_days": 0,
            "Submit": " Zum+Verkauf+geben",
        }
        # wait for a random time
        time.sleep(random.uniform(1.5, 8))
        # auction off items
        session_handler.post(url, auction_post_data)
        # wait for a random time
        time.sleep(random.uniform(2, 3))
        # necessary to open menu again before selling next item
        session_handler.get(config.URL_AUCTION_SELL_MENU)
        # generate debug message
        dbg_msg = (
            "Auctioned off "
            + item_amount
            + " "
            + i_name
            + " for "
            + str(selling_price)
            + " gold each"
        )
        # log the message
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
    # update the player data
    player.update_player()
    # wait for random time
    time.sleep(random.uniform(1, 3))


def __get_selling_price(i_name, only_sold = False):
    #
    db_selling_price = 0
    #
    if (
        i_name in config.ITEM_DATA
        and "auction" in config.ITEM_DATA[i_name]
        and "sold" in config.ITEM_DATA[i_name]["auction"]
        and len(list(config.ITEM_DATA[i_name]["auction"]["sold"].values())) > 0
    ):
        item = config.ITEM_DATA[i_name]
        # create a list with all values
        lst = list(item["auction"]["sold"].values())
        # calculate average offering price
        avergare_offer = sum(lst) / len(lst)
        # set selling price
        db_selling_price = int(math.floor(avergare_offer))
        #
    elif (
        i_name in config.ITEM_DATA
        and "auction" in config.ITEM_DATA[i_name]
        and "offer" in config.ITEM_DATA[i_name]["auction"]
        and len(list(config.ITEM_DATA[i_name]["auction"]["offer"].values())) > 0
        and not only_sold
    ):
        item = config.ITEM_DATA[i_name]
        # create a list with all values
        lst = list(item["auction"]["offer"].values())
        # calculate average offering price
        avergare_offer = sum(lst) / len(lst)
        # set selling price
        db_selling_price = int(math.floor(avergare_offer))
    return db_selling_price
