"""Handle the messages we receive ingame"""
import math
import random
import re
import time

from bs4 import BeautifulSoup, Tag

import botrax_logger
import chat.chat as chat
import config
import investments
from player import Player
from travel import Travel
from util import session_handler

ATTACK_THRESHOLD = 5
MAX_SOLD_ENTRIES = 10


def __log_messages(res, player):
    # collect the message regardless of type
    in_combat = False
    soup = BeautifulSoup(res.text, "lxml")
    nodes = soup.find_all("p", {"class": "maincaption2"})
    #
    for node in nodes:
        #
        msg_s = __get_message_string(node)
        #
        if not msg_s:
            continue
        #
        if __got_attacked(msg_s, player):
            in_combat = True
            botrax_logger.MESSAGE_LOGGER.warning(msg_s)
        #
        elif __received_letter(msg_s):
            botrax_logger.MESSAGE_LOGGER.warning(str(msg_s))
        #
        else:
            botrax_logger.MESSAGE_LOGGER.info(msg_s)
    #
    return in_combat


def __get_message_string(node):
    #
    msg_s = ""
    # check type
    child_node = node.contents[len(node.contents) - 1]
    #
    if child_node and isinstance(child_node, Tag):
        msg_s = child_node.text.replace(" - ", "")
    #
    node = node.next_sibling
    #
    while node and node.next_sibling and node.name != "p" and node.name != "a":
        sub_string = ""
        # check type
        if isinstance(node, Tag):
            sub_string += node.text.replace("<br>", "/n")
        else:
            sub_string += str(node).replace("<br>", "/n")
        # add the substring
        msg_s += sub_string
        #
        if __check_sold_item(node, sub_string):
            msg_s = None
            # break while loop
            break
        # check for not sold items
        if __check_no_sell_item(node, sub_string):
            msg_s = None
            # break while loop
            break
        # get next sibling
        node = node.next_sibling
    #
    return msg_s


def __check_no_sell_item(node, sub_string):
    # init variable
    no_sell = False
    # check for key string
    if "konnten leider nicht in der Markthalle verkauft" not in sub_string:
        return no_sell
    #
    children = node.next_sibling.contents[0].contents
    # extract the name
    name_raw = children[0].text
    pos = name_raw.find("x ")
    item_name = str(name_raw[pos + 2 : len(name_raw)])
    # get the amount of gold we did not sell for
    gold = int(
        children[2]
        .text.replace("/", "")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
        .strip()
    )
    # add data to item data
    # get auction dictionary
    auction_data = {}
    if item_name in config.ITEM_DATA and "auction" in config.ITEM_DATA[item_name]:
        auction_data = config.ITEM_DATA[item_name]["auction"]
    # get no sell dictionary
    no_sell_data = {}
    if "no_sell" in auction_data:
        no_sell_data = auction_data["no_sell"]
    # add updated data
    no_sell_data[int(time.time())] = gold
    # update auction dictionary
    auction_data["no_sell"] = no_sell_data
    # update data in JSON
    config.ITEM_DATA[item_name]["auction"] = auction_data
    # null the msg_s
    ah_msg = f"NO SELL: {item_name} for {gold} gold"
    #
    botrax_logger.MESSAGE_LOGGER.info(ah_msg)
    no_sell = True
    #
    return no_sell


def __check_sold_item(node, sub_string):
    result = False
    if "Ein Postvogel bringt dir ein kleines Päckchen mit Gold." in sub_string:
        item_amount = ""
        #
        try:
            item_amount = node.next_sibling.next_sibling.next_sibling.text
            item_amount = re.sub("[^0-9]", "", item_amount)
        except AttributeError:
            pass
            #
        if item_amount == "":
            item_amount = 1
            #
        item_name = node.next_sibling.next_sibling.next_sibling.next_sibling.text
        #
        gold_text_value = (
            node.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.text
        )
        #
        gold_text_value = (
            gold_text_value.replace("/", "")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
            .strip()
        )
        # get auction dictionary
        auction_data = {}
        if item_name in config.ITEM_DATA and "auction" in config.ITEM_DATA[item_name]:
            auction_data = config.ITEM_DATA[item_name]["auction"]
            # get no sell dictionary
        sell_data = {}
        if "sold" in auction_data:
            sell_data = auction_data["sold"]
            # add updated data
            sell_data[int(time.time())] = int(gold_text_value)
            #
            if len(sell_data) > MAX_SOLD_ENTRIES:
                for _ in range(len(sell_data) - MAX_SOLD_ENTRIES):
                    list(sell_data).pop(0)
                    # update auction dictionary
            auction_data["sold"] = sell_data
        if auction_data:
            # update data in JSON
            config.ITEM_DATA[item_name]["auction"] = auction_data
            # null the msg_s
        ah_msg = f"AH SELL: {item_amount} x {item_name} for {gold_text_value} gold each totaling: {int(item_amount)*int(gold_text_value)}."
        #
        botrax_logger.MESSAGE_LOGGER.info(ah_msg)
        result = True
    return result


def check_for_messages(res, player: Player) -> bool:
    """Check main area for messages

    Args:
        res (response): response from main page request
        player (Player): player object

    Returns:
        bool: True if we receive messages that hint to player attacking us, otherwise False
    """
    # init variables
    in_combat = False
    response = None
    # close to prevent duplicates
    if "read_msg=" and "&msg_isreport=" in res.text:
        # close messages
        response = __close_message(res)
        # log messages we received
        in_combat = __log_messages(res, player)
    #
    if "Niederlage" in res.text:
        # open debug file
        botrax_logger.MAIN_LOGGER.warning(BeautifulSoup(res.text, "lxml").text.strip())
        #
        __dump_chatlog()
        # return as we are dead now
    if "Kampf - Sieg" in res.text:
        # open debug file
        botrax_logger.DEBUG_LOGGER.warning(BeautifulSoup(res.text, "lxml").text.strip())
    #
    if response:
        res = response
    # return result
    return in_combat, res


def __received_letter(msg_s) -> bool:
    msg_keywords = [
        "Ein großer Postvogel bringt dir ein Paket",
        "bringt dir einen Brief",
        "Ein Schattenwesen eilt herbei und überbringt eine Nachricht von",
    ]
    # we received letter but not from auction house
    return (
        any(key in msg_s for key in msg_keywords)
        and not "bringt dir einen Brief vom Markthändler" in msg_s
    )


def __close_message(res):
    # retrieve area and field
    soup = BeautifulSoup(res.text, "lxml")
    links = soup.find_all("a")
    for link in links:
        # get link ref
        href = str(link.get("href"))
        # store messages and end the screen
        if href and "read_msg=" in href and "&msg_isreport" in href:
            # wait a bit
            wait = random.uniform(1, 1.5)
            time.sleep(wait)
            # close all messages ingame
            url = config.URL_INTERNAL_BASE + href
            res = session_handler.get(url)
            # wait a bit
            wait = random.uniform(1, 1.5)
            time.sleep(wait)
            # break loop
            break
    return res


def __got_attacked(msg_s, player: Player) -> bool:
    # list of keywords of messages appearing while getting attacked with items or spells
    attack_not_keywords = [
        "Gegengift",
        "Schlange",
        "Giftbeißer",
        "Seelenkapsel",
        "Markthändler",
        "Giftschlange",
    ]
    # attack keywords
    attack_keywords = [
        "Brand",
        "Gewebewurm",
        "starke Schmerzen in deiner Brust",
        "Du wurdest vergiftet von",
        "Du verlierst",
        "Aus dem Nichts taucht ein Schwarm Killerbienen auf",
        "wurde der Zauber Erdbeben angewendet",
        "Zauber der dunklen Lebensübertragung",
        "Leicht benommen fragst du dich",
        "Goldmünze fällt vom Himmel und landet direkt auf deinem Kopf",
        "klatscht ein bestialisch stinkendes Steak in dein Gesicht",
        "Kaktuspfeil",
        "Ein kleines Mädchen kommt zu dir und hält dich für kurze Zeit fest",
    ]
    # we found a direct attack keywoard?
    critical_attack_keywords = [
        "Hautbrand",
        "Feuerball",
        "Wellenblitz",
        "Herzauber",
        "Verängstigt bleibst du stehen und erblickst",
        "Seelen stürzen sich",
        "Der Boden unter dir vibriert kurz, bevor es einen lauten Knall gibt",
        "über dir siehst du noch einen gewaltigen Affen",
    ]
    # keywords for a stunning attack
    stun_keywords = [
        "Zauber der Starre",
        "hat seine Entscheidung gefällt und verkündet",
    ]
    # check critical attack status
    critical_attack = any(key in msg_s for key in critical_attack_keywords) and not any(
        key in msg_s for key in attack_not_keywords
    )
    # check for people stealing from you
    thief = "Du fühlst dich seltsam, als ob etwas fehlt" in msg_s
    # check for freezing or stunning attacks
    stun_attack = any(key in msg_s for key in stun_keywords)
    #
    normal_attack = False
    if any(key in msg_s for key in attack_keywords) and not any(
        key in msg_s for key in attack_not_keywords
    ):
        # update player mainly for hp value
        player.update_player()
        #
        low_hp = (
            player.get_hp() <= math.ceil(player.get_max_hp() * 0.5)
            and "Gewebewurm" not in msg_s
        )
        if low_hp:
            normal_attack = True
    #
    getting_attacked = normal_attack or critical_attack or thief or stun_attack
    # check if we meet any criteria
    if getting_attacked:
        #
        investments.finish_selected_invest(player, random.randint(750, 2500))
        #
        now = int(time.time())
        dbg_msg = "ATTACK: " + msg_s
        botrax_logger.MAIN_LOGGER.warning(dbg_msg)
        #
        config.LAST_ATTACK_MSG.append(now)
        #
        deletion_amount = 0
        # get indexes which should be deleted
        for item in config.LAST_ATTACK_MSG:
            if item < int(now - ATTACK_THRESHOLD):
                deletion_amount += 1
        # delete selected indexes
        for _ in range(deletion_amount):
            config.LAST_ATTACK_MSG.pop(0)
        # check if we want to use GZK
        if len(config.LAST_ATTACK_MSG) > 1 or stun_attack or critical_attack:
            # flee from attacker
            _flee_from_attack(player, stun_attack or critical_attack)
    #
    return getting_attacked


def _flee_from_attack(player, stun_attack):
    #
    time.sleep(random.uniform(1, 2))
    #
    __dump_chatlog()
    #
    if not player.is_save_pos():
        #
        if player.use_gzk(["73", "1079"]):
            # debug
            dbg_msg = "Getting attacked, used Zauberkugel to escape."
            botrax_logger.MAIN_LOGGER.warning(dbg_msg)
            #
    wait = random.uniform(3, 10)
    #
    if stun_attack:
        wait += random.uniform(120, 260)
        #
    time.sleep(wait)
    #
    player.set_travel(Travel.RANDOM)
    player.update_path(None)


def __dump_chatlog():
    # write last messages for debug purpose
    for item in chat.LOCAL_LOGGED_MESSAGES:
        botrax_logger.MAIN_LOGGER.warning(item)
    # log message
