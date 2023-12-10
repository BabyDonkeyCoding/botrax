"""Module to trade items with Shops"""
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from item import ItemSellType
from player import Player
from trade import trade_conf as tc
from travel import Travel
from util import functions, session_handler


def perform_trade_actions(res, player: Player):
    """Perform various trading actions

    Args:
        res (_type_): _description_
        s (_type_): _description_
        p (Player): _description_
    """
    # use items from inventory
    used_item = use_item_from_list(player, config.special_consume_items)
    #
    __check_player_item_load(player)
    # check for buying possibility
    if "?arrive_eval=einkaufen" in res.text:
        # buy healing pots
        __buy_shop_consumables(player)
    #
    __check_consumables(player)
    # check for selling shop on field
    if "main.php?arrive_eval=verkaufen" not in res.text:
        return
    # set timestamp for next shop visit
    tc.NEXT_SHOP_SELL = functions.get_next_trade_timestamp()
    # log current shop prices
    __get_shop_prices()
    # sell trash items
    sold_something = __sell_junk(player)
    #
    if used_item or sold_something:
        # update player data
        player.update_player()


def __check_consumables(player):
    # buy consumables?
    if player.get_travel().value >= Travel.CONSUMABLES.value:
        return
    # walk through all consumables
    for c_item in config.PLAYER_DATA["consumables"]:
        # get the name
        i_name = str(c_item["name"])
        # check if item was unavailable during last buy attempt
        if i_name in config.UNAVAILABLE_ITEMS:
            # check if item was unavailable
            if (
                config.UNAVAILABLE_ITEMS[i_name]
                >= int(time.time()) - config.UNAVAILABLE_ITEM_THRESHOLD
            ):
                # item is still unavailable -> skip
                continue
            # set new threshold value
            config.UNAVAILABLE_ITEM_THRESHOLD = _get_unavailable_item_threshold()
            # delete entry
            del config.UNAVAILABLE_ITEMS[i_name]
        # init amount
        amount_need = 0
        # get amout on hand
        posession = player.get_amount_by_name(i_name)
        #
        i_max = float(c_item["max"])
        #
        if 0 < i_max < 1:
            i_max = round(player.get_speed() * i_max)
        # check how much we need to buy
        if posession < int(c_item["min"]):
            amount_need = int(i_max - posession)
        # how much do we need to buy?
        if amount_need <= 0:
            # skip
            continue
        # not enough gold on hand?
        if player.get_gold() < round(c_item["avg_price"] * amount_need):
            # skip
            continue
        # no id means we need to buy it from auction house
        if "location" not in c_item:
            target, _ = functions.get_closest_location(
                player.get_pos(), config.AH_LOCATIONS
            )
        else:
            # otherwise get item specific location
            target = c_item["location"]
        # no target location found
        if not target:
            continue
        # check for blocked target location
        if target in config.BLOCKED_LIST:
            continue
        # walk to the target location
        dbg_msg = f"Walking to {target} to buy {amount_need}x {i_name}"
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        player.set_destination(target)
        if i_name in config.healing_items:
            player.set_travel(Travel.HEALING)
        else:
            player.set_travel(Travel.CONSUMABLES)
        # break the loop
        break
    # return
    return


def _get_unavailable_item_threshold() -> int:
    """Returns random number for time to wait for an item which is unavailable"""
    return random.randint(1800, 3600)


def __get_shop_prices():
    # wait artificially to simulate input
    wait = random.uniform(0.5, 1)
    time.sleep(wait)
    # open the menu
    sell_menu = session_handler.get(config.URL_SELL_MENU)
    # wait artificially to simulate input
    wait = random.uniform(1, 2)
    time.sleep(wait)
    #
    links = BeautifulSoup(sell_menu.text, "lxml").find_all("a")
    #
    for link in links:
        href = link.get("href")
        if not href or "?arrive_eval=sell&sell_item=" not in href:
            continue
        #
        tr_tag = link.parent.parent
        name_tag = tr_tag.contents[0].contents[0]
        i_name = name_tag.next.strip()
        #
        link_txt = link.text
        i_price = int(re.sub("[^0-9]", "", link_txt))
        #
        item_data = {}
        if i_name in config.ITEM_DATA:
            item_data = config.ITEM_DATA[i_name]
            # remove old data structure
            if "last_shop_price" in item_data:
                del item_data["last_shop_price"]
        #
        shop_data = {}
        if "shop_price" in item_data:
            shop_data = item_data["shop_price"]
        #
        shop_data[int(time.time())] = i_price
        # shorten the list to limit data size
        if len(shop_data) > config.ITEM_DATA_SIZE_LIMIT:
            for key in list(shop_data.keys()):
                if list(shop_data.keys()).index(key) > config.ITEM_DATA_SIZE_LIMIT:
                    del shop_data[key]
        #
        item_data["shop_price"] = shop_data
        #
        config.ITEM_DATA[i_name] = item_data


def get_trainable_abilities():
    """Returns array of trainable abilities"""
    trainable_abilities = []
    #
    for key, ability in config.PLAYER_DATA["abilities"].items():
        #
        if ability["cur_lvl"] < ability["max_lvl"] or (
            ability["limit"] > 0 and ability["cur_lvl"] < ability["limit"]
        ):
            trainable_abilities.append(key)
    #
    return trainable_abilities


def use_item_from_list(player: Player, item_list: list):
    """Use item from given list.
    Does player have an item from the list, we will use it.
    Args:
        player (Player): player object
        item_list (list): list of items to check against
    """
    # geschenk keywords
    keywords = ["Geschenk von"]
    #
    knowledge_spell = "Wissenszauber: "
    trainable_abilities = get_trainable_abilities()
    #
    used_item = False
    #
    for item in player.get_items():
        # get item specific name
        item_name = item.get_name()
        #
        if any(key in item_name for key in item_list) or (
            knowledge_spell in item_name
            and any(key in item_name for key in trainable_abilities)
        ):
            #
            if (
                item_name == "Wissenszauber aus Reikan"
                and player.get_active_training() == "Lerntechnik"
            ):
                continue
            # generate random waiting time
            wait = random.uniform(1, 1.5)
            time.sleep(wait)
            #
            functions.use_item_by_name(player, item_name)
            # item has been used
            used_item = True
        # check for presents we carry
        elif any(key in item.get_name() for key in keywords):
            # generate random waiting time
            wait = random.uniform(1, 1.5)
            time.sleep(wait)
            #
            session_handler.get(
                config.URL_USE_ITEM + str(item.get_id()) + "&geschenk=oeffnen"
            )
            # debug
            botrax_logger.MAIN_LOGGER.info("Opened: %s", item_name)
            # item has been used
            used_item = True
    #
    return used_item


def __buy_shop_consumables(player: Player) -> bool:
    bought_consumables = False
    links = None
    # check all consumables
    for item in config.PLAYER_DATA["consumables"]:
        # check location
        if (
            "location" in item and item["location"] != player.get_pos()
        ) or "location" not in item:
            continue
        # wait artificially to simulate input
        wait = random.uniform(1, 2)
        time.sleep(wait)
        # buy item
        i_name = str(item["name"])
        p_item = player.get_item_by_name(i_name)
        p_amount = 0
        if p_item:
            p_amount = p_item.get_amount()
        # check maximum amount
        i_max = float(item["max"])
        if 0 < i_max < 1:
            i_max = round(player.get_speed() * i_max)
        # calculate amount needed
        amount_need = i_max - p_amount
        if amount_need <= 0:
            continue
        #
        if not links:
            # open the menu
            res = session_handler.get(config.URL_PURCHASE_MENU)
            links = BeautifulSoup(res.text, "lxml").find_all("a")
            # wait artificially to simulate input
            wait = random.uniform(0.5, 1)
            time.sleep(wait)
        # randomize amount if we want to buy multiple
        if i_max > 1:
            amount_need += random.randint(0, 4)
        #
        amount_need_s = str(amount_need)
        url = config.URL_INTERNAL_BASE
        # get link
        for link in links:
            if i_name in link.text:
                url += link.get("href")
                break
        #
        if url == config.URL_INTERNAL_BASE:
            continue
        #
        session_handler.get(url + "&anz=" + amount_need_s)
        # debug
        dbg_msg = "Bought " + amount_need_s + " " + i_name
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        bought_consumables = True
        # update player data
        player.update_player()
        #
        wait = random.uniform(1, 2)
        time.sleep(wait)
        #
    # return result
    return bought_consumables


def __sell_junk(player: Player) -> bool:
    #
    sold_something = False
    #
    if (
        "okay_shops" in config.PLAYER_DATA
        and player.get_pos() not in config.PLAYER_DATA["okay_shops"]
    ):
        return sold_something
    # wait artificially to simulate input
    time.sleep(random.uniform(0.5, 1))
    # open the menu
    sell_menu = session_handler.get(config.URL_SELL_MENU)
    # wait artificially to simulate input
    time.sleep(random.uniform(1, 2))
    # sell items
    for p_item in player.get_items():
        #
        i_name = p_item.get_name()
        # item name not listed in sell menu
        if i_name not in sell_menu.text:
            continue
        # item is not for shop selling
        if p_item.get_sell_type() != ItemSellType.SHOP:
            continue
        # debug
        i_amount = int(p_item.get_amount())
        #
        if i_name in player.get_equipped_items() or (
            "tools" in config.PLAYER_DATA and i_name in config.PLAYER_DATA["tools"]
        ):
            i_amount = int(player.get_amount_by_name(i_name) - 1)
        # skip item if nothing can be sold
        if i_amount < 1:
            continue
        #
        i_amount = str(i_amount)
        # sell item(s)
        session_handler.get(
            config.URL_MAIN
            + "?arrive_eval=sell&sell_item="
            + str(p_item.get_id())
            + "&anz="
            + i_amount
        )
        # debug message
        dbg_msg = "Sold " + i_amount + " " + i_name + " to the shop."
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # generate random waiting time
        time.sleep(random.uniform(1.5, 3.25))
        # set true
        sold_something = True
    # return result
    return sold_something


def __check_player_item_load(player: Player):
    """Check if the player has to move somewhere

    Args:
        player (): The player object
    """
    # Sell items?
    if player.get_travel().value >= Travel.ITEM_TRADE.value:
        return
    # init variables
    p_speed = player.get_speed()
    #
    p_load = player.get_amount_items_carried() / p_speed
    #
    has_high_value_item = player.carries_high_value_item()
    #
    now = int(time.time())
    # bag almost empty?
    if (
        p_load < 0.75
        and not has_high_value_item
        and tc.NEXT_AH_SELL > now
        and tc.NEXT_SHOP_SELL > now
    ):
        # skip further processing
        return
    # get back fill percentage level
    bag_90_percent_full = p_load >= 0.9
    bag_75_percent_full = p_load >= 0.75
    # init variables
    next_shop = None
    target = None
    # get all player available shops
    shop_list = config.LOCATION_DATA["shops"]
    # get best shops
    if "okay_shops" in config.PLAYER_DATA:
        shop_list = [config.PLAYER_DATA["okay_shops"][0]]
    # get closest shop
    next_shop, distance_to_shop = functions.get_closest_location(
        player.get_pos(), shop_list
    )
    # get closests auction house
    next_ah, distance_to_ah = functions.get_closest_location(
        player.get_pos(), config.AH_LOCATIONS
    )
    # get player item data
    (
        has_auc_items,
        has_shop_items,
        auc_amount,
        shop_amount,
    ) = player.get_item_overview()
    # CHECK SHOPS
    if (
        next_ah
        and player.get_gold() >= config.PLAYER_DATA["banking"]["min_char_gold"]
        and (
            (bag_90_percent_full or (bag_75_percent_full and distance_to_ah <= 13))
            and has_auc_items
            and shop_amount < auc_amount
        )
        or has_high_value_item
        or tc.NEXT_AH_SELL < now
    ):
        #
        target = next_ah
        botrax_logger.MAIN_LOGGER.info("Walking to the AH at: %s", str(next_ah))
    elif (
        next_shop
        and (
            (bag_90_percent_full or (bag_75_percent_full and distance_to_shop <= 50))
            and has_shop_items
            and auc_amount < shop_amount
        )
        or tc.NEXT_SHOP_SELL < now
    ):
        target = next_shop
        botrax_logger.MAIN_LOGGER.info("Walking to the shop at: %s", str(next_shop))
    # CHEK AUCTION HOUSE
    #
    if target:
        player.set_destination(target)
        player.set_travel(Travel.ITEM_TRADE)
