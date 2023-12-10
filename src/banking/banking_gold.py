"""Module for handling gold at bank."""
import math
import random
import re
import time

import botrax_logger
import config
from util import session_handler, functions
from banking import banking_items
from player import Player
from travel import Travel
import investments

UPPER_LIMIT = 200
LOWER_LIMIT = -200
MAX_CHAR_GOLD_RND_FACTOR = random.uniform(2.3, 2.5)


def __get_next_banking_check() -> int:
    """Returns the next xp sell time stamp"""
    return int(time.time()) + random.randint(30, 90)


def __need_banking(player: Player):
    """Check if player needs banking."""
    global MAX_CHAR_GOLD_RND_FACTOR
    # check timing
    if (
        time.time() <= config.NEXT_BANKING_CHECK
        and player.get_pos() not in config.BANKING_LOCATIONS
    ):
        return
    # set next timing
    config.NEXT_BANKING_CHECK = __get_next_banking_check()
    # get current player gold
    p_gold = player.get_gold()
    #
    been_to_bank = player.get_gold_bank() > -1
    # check need for further analysis
    if (
        player.get_travel().value >= Travel.BANK.value
        or player.get_travel().value
        in [
            Travel.CONSUMABLES.value,
        ]
        or (
            (
                config.PLAYER_DATA["banking"]["min_char_gold"]
                < p_gold
                < config.PLAYER_DATA["banking"]["max_char_gold"]
            )
            and been_to_bank
        )
    ):
        # if yes, then return
        return
    # otherwise, calculate difference between gold we have on character and gold we should have
    difference_rounded = __gold_difference_rounded(player)
    #
    if LOWER_LIMIT < difference_rounded < UPPER_LIMIT:
        return
    # do we have more than max limit on character?
    max_gold_on_hand = p_gold > config.PLAYER_DATA["banking"]["max_char_gold"]
    #
    if (
        p_gold
        >= round(
            config.PLAYER_DATA["banking"]["max_char_gold"] * MAX_CHAR_GOLD_RND_FACTOR
        )
        and player.get_pos() not in config.BANKING_LOCATIONS
    ):
        #
        MAX_CHAR_GOLD_RND_FACTOR = random.uniform(2.3, 2.5)
        # we found the item in our inventory
        if time.time() > config.NEXT_BANK_PORT and player.use_gzk(["73"]):
            # debug
            dbg_msg = "Too much gold on hand, used Zauberkugel to go to Bank."
            botrax_logger.MAIN_LOGGER.info(dbg_msg)
            #
            config.NEXT_BANK_PORT = functions.get_next_bank_port()
            #
            return
    # is total gold below bank limit?
    total_gold_below_bank_limit = (
        player.get_gold_bank() + difference_rounded
    ) < player.get_bank_limit()
    # is the bank filled up to minimum amount?
    minimum_gold_in_bank = (
        player.get_gold_bank() > config.PLAYER_DATA["banking"]["min_bank_gold"]
    )
    # gold we need is in bank
    bank_gold_e2 = (
        abs(difference_rounded) < player.get_gold_bank()
        and config.PLAYER_DATA["banking"]["min_char_gold"]
        == config.PLAYER_DATA["banking"]["min_char_gold_default"]
    )
    # check combinations
    if (
        (minimum_gold_in_bank or bank_gold_e2)
        or (max_gold_on_hand and total_gold_below_bank_limit)
        or not been_to_bank
    ):
        # get closest bank
        target, _ = functions.get_closest_location(
            player.get_pos(), config.BANKING_LOCATIONS
        )
        #
        if not target or target == player.get_pos():
            return
        # debug messages
        dbg_msg = (
            f"Walking to bank at: {target} | Difference is: {int(difference_rounded):,}"
        )
        # log debug message
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # set travel and destination
        player.set_destination(target)
        player.set_travel(Travel.BANK)


def __open_bank_account(res, player: Player):
    # check if we have a bank account
    if "Du hast noch kein Konto" not in res.text:
        return
    # check that we have gold to open bank account
    if player.get_gold() > 0:
        __deposit_gold(res, player.get_gold())
        # update all data
        player.update_player()


def do_banking(res, player: Player):
    """Do stuff necessary for banking
    Args:
        res (_type_): response
        session (_type_): session
        player (Player): player
    """
    # check if we want to go to bank
    __need_banking(player)
    # we are at a bank
    if player.get_pos() not in config.BANKING_LOCATIONS:
        # return
        return
    #
    __set_player_bank_gold(res, player)
    # update all data
    player.update_player()
    # check for existing bank account
    __open_bank_account(res, player)
    #
    if config.AUTOMOVE:
        # check for investments to make
        investments.check(res, player)
    # get bank amount
    res = __check_bank_action(res, player)
    # get auction items out of bank
    banking_items.check_storage(res, player)


def __check_bank_action(res, player):
    # check for bank location
    difference_rounded = __gold_difference_rounded(player)
    #
    if LOWER_LIMIT < difference_rounded < UPPER_LIMIT:
        return res
    #
    bank_action_happened = False
    # do we have gold than we need on character? Check that we do not deposit very small amounts
    if (
        difference_rounded >= UPPER_LIMIT
        and player.get_gold_bank() < player.get_bank_limit()
        and player.get_travel().value not in [Travel.CONSUMABLES.value]
    ):
        # do we have too much gold on character regarding bank limit?
        if (player.get_gold_bank() + difference_rounded) > player.get_bank_limit():
            # calculate difference between bank limit and player gold
            difference_rounded = player.get_bank_limit() - player.get_gold()
        # deposit excess money
        __deposit_gold(res, difference_rounded)
        # set flag
        bank_action_happened = True
    # do we have less gold than we need on character?
    elif difference_rounded <= LOWER_LIMIT and player.get_gold_bank() > 0:
        #
        min_bank_gold = config.PLAYER_DATA["banking"]["min_bank_gold"]
        #
        if (
            player.get_bank_limit() > min_bank_gold
            and (
                player.get_gold_bank() > min_bank_gold
                or config.PLAYER_DATA["banking"]["min_char_gold"]
                == config.PLAYER_DATA["banking"]["min_char_gold_default"]
            )
        ) or player.get_bank_limit() < min_bank_gold:
            #
            if abs(difference_rounded) > player.get_gold_bank():
                difference_rounded = player.get_gold_bank()
            # withdraw money
            __withdraw_gold(res, abs(difference_rounded))
            #
            bank_action_happened = True
    # update bank amount on player if action happened
    if bank_action_happened:
        #
        res = session_handler.get(config.URL_MAIN)
        # get bank amount
        __set_player_bank_gold(res, player)
        # wait a bit before taking items with your
        time.sleep(random.uniform(1.5, 3))
    return res


def __gold_difference_rounded(player):
    # get exact value
    difference_exact = (
        player.get_gold() - config.PLAYER_DATA["banking"]["min_char_gold"]
    )
    # round the value to nearest tenth
    difference_rounded = round(int(math.ceil(difference_exact / 10) * 10), -2)
    # check if we have a negative difference
    if difference_exact < 0:
        difference_rounded = round(int(math.floor(difference_exact / 10) * 10), -2)
    # return the calculated result
    return difference_rounded


def __set_player_bank_gold(res, player: Player):
    # check costs
    regex_result = re.findall(
        r"Du hast \d{1,3}.\d{1,3}.\d{1,3} Goldmünzen auf deinem Konto", res.text
    )
    #
    if len(regex_result) > 0:
        gold_amount = re.sub("[^0-9]", "", regex_result[0])
        # we found the text and a value
        if gold_amount != "":
            # set value to the player object
            int_value_bank_gold = int(gold_amount)
            player.set_gold_bank(int_value_bank_gold)


def __deposit_gold(res, amount):
    #
    now = time.time()
    if (
        amount > 0
        and now >= config.NEXT_DEPOSIT
        and "?arrive_eval=einzahlen" in res.text
    ):
        # wait artificially to simulate input
        wait = random.uniform(0.5, 1)
        time.sleep(wait)
        #
        session_handler.get(config.URL_DEPOSIT_MENU)
        # wait artificially to simulate input
        wait = random.uniform(1.5, 3)
        time.sleep(wait)
        # create deposit payload data
        deposit_post_data = {"money": amount, "submit": "Einzahlen"}
        # post money deposit to server
        session_handler.post(config.URL_DEPOSIT_MONEY, deposit_post_data)
        # print debug
        dbg_msg = f"Deposited {amount:,} gold to the bank."
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # set last deposit time
        config.NEXT_DEPOSIT = now + random.randint(10, 60)
        # randomize the max value again
        config.PLAYER_DATA["banking"]["max_char_gold"] = functions.get_max_char_gold()


def __withdraw_gold(res, amount):
    # get current time
    now = time.time()
    #
    if (
        amount > 0
        and now >= config.NEXT_WITHDRAW
        and "?arrive_eval=abheben" in res.text
    ):
        # wait artificially to simulate input
        wait = random.uniform(0.5, 1)
        time.sleep(wait)
        #
        session_handler.get(config.URL_WITHDRAW_MENU)
        # wait artificially to simulate input
        wait = random.uniform(0.9, 1.25)
        time.sleep(wait)
        # create deposit payload data
        withdraw_post_data = {"money": amount, "submit": "Abheben"}
        # post money deposit to server
        session_handler.post(config.URL_WITHDRAW_MONEY, withdraw_post_data)
        # print debug
        dbg_msg = f"Withdrew {amount:,} gold from the bank."
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # set last deposit time
        config.NEXT_WITHDRAW = now + random.randint(20, 60)


# TRANSFER
# https://weltxyz.freewar.de/freewar/internal/main.php?arrive_eval=spielen2&nomessage=ignore
# name=zY&money=1000&verwendung=muli&Submit=Überweisung+durchführen
