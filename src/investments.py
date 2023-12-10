"""Module to handle investments in the game"""
import math
import random
import re
import time

from bs4 import BeautifulSoup

import academy
import botrax_logger
import config
from player import Player
from travel import Travel
from util import functions, session_handler

# url string telling us we can do prepay
PREPAY_URL_S = "arrive_eval=prepay"
# url string telling us we can upgrade here
UPGRADE_URL_S = "?arrive_eval=upgrade"


def check(res, player: Player):
    """Check if we can upgrade investments"""
    # select next investment to work on
    __select_next_invest(player)
    # check for pickup location
    if player.get_pos() in config.INVEST_PICKUP_LOCATIONS:
        __check_pickup(res.text)
    # check for next investment
    if player.get_travel().value > Travel.INVESTMENTS.value:
        return
    # no investment?
    if not player.get_invest():
        # go back to other tasks
        return
    #
    __do_action(res, player)
    #
    __check_where_to_go(player)


def finish_selected_invest(player, added_time):
    """Finish the current investment"""
    if not player.get_invest():
        return
    #
    now = int(time.time())
    #
    if functions.get_chance(0.03):
        time_reduction = random.randint(3600 * 2, 3600 * 24)
        #
        botrax_logger.DEBUG_LOGGER.info(f"Reduced Investment timing by {time_reduction} seconds.")
        # reduce the timing
        now -= time_reduction
    #
    player.get_invest()["last_action"] = now
    player.get_invest()["next_action"] = now + added_time
    # reset invest
    player.set_invest(None)
    # reset value back to default
    config.PLAYER_DATA["banking"]["min_char_gold"] = functions.get_min_char_gold()
    config.PLAYER_DATA["banking"]["max_char_gold"] = functions.get_max_char_gold()
    #
    player.update_player()


def __select_next_invest(player: Player):
    # check for existing
    if player.get_invest():
        return
    # init variables
    target_idx = -1
    now = int(time.time())
    loop_time = now
    # check array for invest with oldest action seen
    for invest in config.PLAYER_DATA["investments"]:
        # create pickup locations list
        if (
            invest["type"] == "storage"
            and invest["location"] not in config.INVEST_PICKUP_LOCATIONS
        ):
            config.INVEST_PICKUP_LOCATIONS.append(invest["location"])
        # check for max level being reached
        if (
            "lvl" in invest
            and "limit" in invest
            and int(invest["lvl"]) >= int(invest["limit"])
            and invest["type"] not in ["storage"]
        ):
            continue
        # check any study investemt on its conditions
        if invest["type"] == "study" and not academy.check_conditions(player):
            continue
        # no last action given?
        if "last_action" not in invest:
            invest["last_action"] = now
        # last actionis older than loop variable value?
        elif invest["last_action"] < loop_time and invest["next_action"] <= now:
            # set new loop variable value
            loop_time = invest["last_action"]
            # set new target index
            target_idx = config.PLAYER_DATA["investments"].index(invest)
    #
    if target_idx >= 0:
        #
        next_invest = config.PLAYER_DATA["investments"][target_idx]
        next_invest["prepared"] = False
        player.set_invest(next_invest)
        #
        dbg_msg = f"Plan is to invest {next_invest['costs']:,} gold in {next_invest['name']} next"
        botrax_logger.MAIN_LOGGER.info(dbg_msg)


def __check_where_to_go(player: Player):
    # INVESTMENTS
    invest = player.get_invest()
    #
    if not invest or player.get_travel().value >= Travel.INVESTMENTS.value:
        return
    #
    player.update_player()
    # define costs for current investment
    costs = 0
    if invest["type"] == "study":
        costs = academy.get_hp_academy_costs()
        player.get_invest()["costs"] = costs
    elif "costs" in invest:
        costs = int(invest["costs"])
        #
        if invest["prepay"] and costs > config.PREPAY_MAX:
            costs = config.PREPAY_AMOUNT
            invest["costs"] = costs
        #
        if (
            "lvl" in invest
            and "limit" in invest
            and int(invest["lvl"]) >= int(invest["limit"])
        ):
            costs = 0
            invest["costs"] = costs
    #
    __check_finances(player, costs)
    # variables
    i_name = invest["name"]
    # build ready
    if player.get_gold() >= costs:
        # move to location
        target = invest["location"]
        botrax_logger.MAIN_LOGGER.info(
            "Walking to " + target + " for investment " + i_name
        )
        player.set_destination(target)
        player.set_travel(Travel.INVESTMENTS)


def __check_pickup(site_text):
    # check for pickup link in site
    if "arrive_eval=drink&checkid=" not in site_text:
        return
    # Checks location for available pickup
    links = BeautifulSoup(site_text, "lxml").find_all(
        "a", {"href": re.compile(r"arrive_eval=drink&checkid=")}
    )
    # check all links at the field
    for link in links:
        # wait for random amount of time after picking up items
        time.sleep(random.uniform(0.5, 1.5))
        # request the pickup of items
        session_handler.get(config.URL_INTERNAL_BASE + link.get("href"))
        # create debug message
        dbg_msg = "Picked up " + str(link.text)
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # wait for random amount of time after picking up items
        time.sleep(random.uniform(1, 2))


def __check_finances(player: Player, costs):
    #
    if "prepared" in player.get_invest() and player.get_invest()["prepared"]:
        return
    #
    min_char_gold_tmp = int(
        config.PLAYER_DATA["banking"]["min_char_gold_default"] * random.uniform(1, 1.2)
    )
    #
    total_player_gold = player.get_gold_bank() + player.get_gold()
    #
    min_gold_bank = config.PLAYER_DATA["banking"]["min_bank_gold"]
    #
    # or we are below 35k but have our bank more than 90% filled
    if player.get_bank_limit() < min_gold_bank:
        min_gold_bank = math.floor(player.get_bank_limit() * 0.9)
    #
    difference = total_player_gold - min_gold_bank
    #
    if difference < costs + min_char_gold_tmp:
        return
    #
    if player.get_invest()["type"] == "study":
        #
        max_number = (
            player.get_xp() + player.get_invest()["xp"] - player.get_academy_limit()
        ) // player.get_invest()["xp"]
        #
        diff_amount = difference // costs
        #
        costs = min(max_number * costs, diff_amount * costs)
        player.get_invest()["costs"] = costs
    # add to the costs of the investment
    costs += min_char_gold_tmp
    #
    invest_name = player.get_invest()["name"]
    #
    log_msg = f"Preparing {costs:,} gold for investment: {invest_name}"
    botrax_logger.MAIN_LOGGER.info(log_msg)
    # set min player gold to new value
    config.PLAYER_DATA["banking"]["min_char_gold"] = costs
    # set max player gold to new value
    config.PLAYER_DATA["banking"]["max_char_gold"] = costs + min_char_gold_tmp
    #
    player.get_invest()["prepared"] = True


def __do_action(res, player: Player):
    # check if we are at any interesting location
    current_invest = player.get_invest()
    #
    if not current_invest or player.get_pos() != current_invest["location"]:
        return
    # active invest is a study
    if current_invest["type"] == "study":
        academy.study(player)
        return
    # get text
    site_text = res.text
    if (
        "lvl" in current_invest
        and "limit" in current_invest
        and int(current_invest["lvl"]) >= int(current_invest["limit"])
    ):
        finish_selected_invest(player, random.randint(43000, 69000))
        return
    # can we prepay?
    current_invest["prepay"] = PREPAY_URL_S in site_text
    # in case we do not have enough gold or investment not active
    if player.get_gold() < current_invest["costs"]:
        return
    # try to buy or upgrade
    res, site_text = __buy_investment(res, current_invest, site_text)
    # can we upgrade it?
    res, tried_prepay, upgraded = __upgrade_investment(res, current_invest)
    # random values for pickup locations
    delay = random.randint(86400, 92300)
    if tried_prepay:
        delay = random.randint(300, 900)
    # set timings for next actions
    res = session_handler.get(config.URL_MAIN)
    #
    offset = random.randint(30, 520)
    current_invest, delay = _get_investment_details(current_invest, res.text)
    dbg_msg = f"Remaining costs: {current_invest['costs']:,} gold"
    botrax_logger.MAIN_LOGGER.info(dbg_msg)
    #
    if not tried_prepay and not upgraded:
        return
    #
    if tried_prepay and delay == 0:
        delay = random.randint(360, 7000)
    #
    added_time = delay + offset
    #
    finish_selected_invest(player, added_time)
    #
    time.sleep(random.uniform(1, 2))


def _get_investment_details(invest, site_text):
    # init variables
    costs = 0
    level = 0
    delay = 0
    # get site as normal string without html tags
    soup = BeautifulSoup(site_text, "html.parser")
    soup_text = soup.text
    # check costs
    regex_result = re.findall(r"Kosten: \d{1,3}.\d{1,3}.\d{1,3} Goldmünzen", soup_text)
    if len(regex_result) > 0:
        cost_s = re.sub("[^0-9]", "", regex_result[0])
        costs = int(cost_s)
    # set costs
    invest["costs"] = costs
    # check level
    regex_result = re.findall(r"\bStufe \d+", soup_text)
    if len(regex_result) > 0:
        # regex search for stufe string with number
        level_s = re.sub("[^0-9]", "", regex_result[0])
        level = int(level_s)
    #
    invest["lvl"] = level
    # set timings for next actions
    # check timing
    regex_result = re.findall(r"ist in \d+ Minuten", soup_text)
    regex_result.extend(re.findall(r"wird in \d+ Minuten", soup_text))
    # check for time
    if len(regex_result) > 0:
        timing = re.sub("[^0-9]", "", regex_result[0])
        #
        delay = round(60 * int(timing))
    #
    return invest, delay


def __upgrade_investment(res, invest):
    """Method tries to prepay a defined amount of gold to the given investment or tries direct upgrade.

    Args:
        res (response): main web page response
        invest (_type_): current investment

    Returns:
        res: response
        tried_prepay: result of prepay attempt
        tried_upgrade: result of upgrade attempt
    """
    tried_prepay = False
    upgraded = False
    # money=5000&submit=Anzahlung+machen
    if PREPAY_URL_S in res.text and invest["costs"] == config.PREPAY_AMOUNT:
        # random waiting time
        time.sleep(random.uniform(1.1, 2.5))
        # create login post data
        prepay_post_data = {
            "money": invest["costs"],
            "submit": "Anzahlung+machen",
        }
        # login on main page with post data
        res = session_handler.post(
            config.URL_MAIN + "?arrive_eval=prepay2", prepay_post_data
        )
        if res and "Du hast eine Anzahlung in Höhe von" not in res.text:
            return res, tried_prepay, upgraded
        # set flag for prepay action to True
        tried_prepay = True
        # log action
        dbg_msg = f"Prepayed {invest['costs']:,} gold for {invest['name']} at {invest['location']}"
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # set new PREPAYMENT amount for next investment
        config.PREPAY_AMOUNT = int(
            random.randrange(
                config.PREPAY_MIN, config.PREPAY_MAX, config.PREPAY_STEP_SIZE
            )
        )
        # wait a random amount of time to appear human
        time.sleep(random.uniform(0.5, 2.5))
    # We do have the money for direct upgrade or prepay not available
    elif UPGRADE_URL_S in res.text:
        # random waiting time
        time.sleep(random.uniform(1.1, 2.5))
        # request upgrade
        res = session_handler.get(config.URL_MAIN + UPGRADE_URL_S)
        # check response of our tryo to upgrade the investment
        if res and "Du hast nicht genug Geld dabei" in res.text:
            invest["prepared"] = False
            return res, tried_prepay, upgraded
        # set upragde flag to True
        upgraded = True
        # log the action
        botrax_logger.MAIN_LOGGER.info(
            "Upgraded: " + invest["name"] + " at " + invest["location"]
        )
        # random waiting time
        time.sleep(random.uniform(0.9, 3))
    # return results
    return res, tried_prepay, upgraded


def __buy_investment(res, invest, site_text):
    # init variables
    buy_href_s = "?arrive_eval=buy"
    # check for link to buy investment on the page
    if buy_href_s in site_text:
        # random waiting time
        time.sleep(random.uniform(1.1, 2.5))
        # buy the investment
        session_handler.get(config.URL_MAIN + buy_href_s)
        # write log
        botrax_logger.MAIN_LOGGER.info(
            "Bought: " + invest["name"] + " at " + invest["location"]
        )
        # get mian page again after last request
        res = session_handler.get(config.URL_MAIN)
        if res:
            # get text in case we got a response
            site_text = res.text
    # return variables
    return res, site_text
