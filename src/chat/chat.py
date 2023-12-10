import datetime
import random
import re
import time
from enum import Enum

from bs4 import BeautifulSoup

import botrax_logger
import chat.chat_config as chat_config
import config
import weather_events as we
from move import movement_functions
from player import Player
from travel import Travel
from util import session_handler

#
teleported_npcs = []
GREETING_THRESHOLD = 20
last_greeting = time.time() - GREETING_THRESHOLD
#
LOCAL_LOGGED_MESSAGES = []
#
ALL_LOGGED_MSG = []
#
LOG_MAX_SIZE = 1000
LOCAL_MAX_SIZE = 20
# list of keywords for dead NPCs
NPC_DEAD_KEYWORD = ["schwebt in großer Eile davon ", "stirbt", "sterben", "tod"]
# seconds from teleport to be still active
NPC_TELEPORT_THRESHOLD = 6


class Chatchannel(Enum):
    """Class representing a channel"""

    GROUP = "Gruppe"
    LOCAL = "Sagen"
    WORLD = "Scream"
    GLOBAL = "Global"


def talk_with_chat(txt, chatchannel: Chatchannel):
    """Chat with a channel"""
    res = session_handler.get(config.URL_CHATFORM)
    # check content
    if not res:
        return
    # get element with ID
    input_element = BeautifulSoup(res.text, "lxml").find(
        "input", {"name": "chatcheckid"}
    )
    # did we get the target element?
    if not input_element:
        # no element -> return
        return
    #
    chatcheckid = input_element.get("value")
    # create login payload data
    chat_channel = chatchannel.value
    #
    chat_post = {
        "chat_text": txt,
        "chatcheckid": chatcheckid,
        "group": chat_channel,
        "chatscroll": "on",
    }
    # post chat text
    res = session_handler.post(config.URL_CHATFORM, chat_post)


def check_chat(player: Player):
    """Check chat frame for messages"""
    # initialize variables
    now = int(time.time())
    # check that enough time has passed
    if now < config.NEXT_CHAT_CHECK and not player.target_npc:
        return False
    # check for group
    if player.is_in_group():
        # set next check timestamp
        config.NEXT_CHAT_CHECK = now + random.uniform(0, 1)
    else:
        # set next check timestamp
        config.NEXT_CHAT_CHECK = now + random.uniform(3, 7)
    # get chat data
    res = session_handler.get(config.URL_CHATTEXT)
    # return in case no response
    if not res:
        return False
    # check if we want to port to player
    teleport = __check_group_teleport(res, player)
    # log the chats
    __log_chats(res, player)
    #
    return teleport


def __log_chats(res, player):
    # init variables, create chat keywords
    keywords = [str(config.PLAYER_DATA["username"]), " bot ", "bot ", " bot"]
    #
    soup = BeautifulSoup(res.text, "lxml")
    messages = soup.find_all("p", {"class": "chattextscream"})
    messages.extend(soup.find_all("p", {"class": "chattextglobal"}))
    messages.extend(soup.find_all("p", {"class": "chattextwhisper"}))
    messages.extend(soup.find_all("p", {"class": "chattext"}))
    messages.extend(soup.find_all("p", {"class": "chattextinfo"}))
    messages.extend(soup.find_all("p", {"class": "chattextgroup"}))
    messages.extend(soup.find_all("p", {"class": "chattextclan"}))
    #
    action = False
    #
    for msg in messages:
        # get message
        msg_class = msg.get("class")
        message_txt = msg.text
        local_txt = player.get_pos() + " " + message_txt
        # set conditions to skip work on this message
        if (
            not msg_class
            or message_txt in ALL_LOGGED_MSG
            or "Aktuelle Clan-Nachricht:" in message_txt
        ):
            continue
        # check for information messages
        if "chattextinfo" in msg_class:
            # check for weather event
            we.check_weather(msg, player)
            # no logging needed
            continue
            #
        if "chattext" in msg_class:
            #
            action &= __check_target_npc(msg, player)
            #
            if local_txt not in LOCAL_LOGGED_MESSAGES:
                #
                LOCAL_LOGGED_MESSAGES.append(local_txt)
        # check message content
        elif any(key in msg_class for key in ["chattextclan", "chattextgroup"]):
            # check for group greetings
            __group_greetings(msg)
            # log message
            botrax_logger.CHAT_LOGGER.warning(message_txt)
        elif (
            any(key.casefold() in message_txt.casefold() for key in keywords)
            or "chattextwhisper" in msg_class
        ):
            botrax_logger.CHAT_LOGGER.critical(message_txt)
        else:
            botrax_logger.CHAT_LOGGER.info(message_txt)
        #
        ALL_LOGGED_MSG.append(message_txt)
        # trim array for scream chats
        if len(ALL_LOGGED_MSG) > LOG_MAX_SIZE:
            ALL_LOGGED_MSG.pop(0)
        # trim the array if exceeding length
        if len(LOCAL_LOGGED_MESSAGES) > LOCAL_MAX_SIZE:
            LOCAL_LOGGED_MESSAGES.pop(0)
    #
    return action


################################
#
################################
def __check_target_npc(msg, player: Player):
    #
    msg_text = msg.text
    #
    if not player.target_npc or str(player.target_npc) not in msg_text:
        return False
    #
    if str(player.target_npc).casefold() in msg_text.casefold() and any(
        key.casefold() in msg_text.casefold() for key in NPC_DEAD_KEYWORD
    ):
        # log
        botrax_logger.MAIN_LOGGER.warning("NPC %s died!", player.target_npc)
        player.target_npc = None
        player.update_path(None)
        player.set_travel(Travel.RANDOM)
        # time.sleep(random.uniform(1, 3))
        return True
    #
    if all(
        key.casefold() in msg_text.casefold()
        for key in [str(player.target_npc), "verlässt den Ort", "Richtung"]
    ):
        #
        spot = movement_functions.get_direction_spot(msg_text, player)
        #
        player.update_path([spot])
        #
        return True
    #
    return False


def __group_greetings(msg):
    msg_text = msg.text
    #
    if (
        config.PLAYER_DATA["username"] not in msg_text
        and "offene Gruppe gewählt" in msg_text
        and msg_text not in chat_config.GREETED_PLAYERS
    ):
        #
        full_msg = msg
        chat_msg_time = full_msg.contents[0].text
        test = datetime.datetime.strptime(chat_msg_time, "%H:%M:%S")
        now = datetime.datetime.now()
        test.replace(year=now.year, month=now.month, day=now.day)
        delta = now - test
        seconds = delta.seconds
        if seconds > 30:
            return
        # wait a bit
        time.sleep(random.uniform(10, 20))
        # greet the player
        talk_with_chat(random.choice(chat_config.GREETINGS), Chatchannel.GROUP)
        # add message to avoid duplicate greetings
        chat_config.GREETED_PLAYERS.append(msg_text)


def __check_group_teleport(res, player):
    # init variables
    teleport = False
    #
    if (
        not player.is_in_group()
        or player.get_travel().value >= Travel.GROUP_HUNTING.value
        or not player.get_item_by_name("Gruppen-Hinzauber")
        or player.target_npc
    ):
        return teleport
    #
    links = BeautifulSoup(res.text, "lxml").find_all(
        "a", {"href": re.compile(r"action=placeinc&place=")}
    )
    # walk
    for link in links:
        # get parent element text
        parent = link.parent.text
        pparent = link.parent.parent.text
        if "Gruppen-NPC" not in parent or config.PLAYER_DATA["username"] in pparent:
            continue
        # get npc name
        npc_name = parent[0 : parent.find("(Gruppen-NPC)")].strip()
        #
        if npc_name in teleported_npcs or any(
            key in parent for key in ["Terbat", "Tanien"]
        ):
            continue
        # get the time since the message has been posted
        full_msg = link.parent.parent
        chat_msg_time = full_msg.contents[0].text
        #
        test = datetime.datetime.strptime(chat_msg_time, "%H:%M:%S")
        now = datetime.datetime.now()
        #
        test = test.replace(year=now.year, month=now.month, day=now.day)
        seconds = (now - test).seconds
        #
        if seconds > NPC_TELEPORT_THRESHOLD:
            continue
        #
        teleported_npcs.append(npc_name)
        player.target_npc = npc_name.strip()
        # simulate some time to react
        time.sleep(random.uniform(3, 6))
        #
        botrax_logger.MAIN_LOGGER.warning("Porting to group NPC: %s", npc_name)
        # request teleport
        session_handler.get(config.URL_INTERNAL_BASE + link.get("href"))
        # set flag true
        teleport = True
        # change travel mode
        player.set_travel(Travel.GROUP_HUNTING)
        player.update_path(None)
        #
        break
    #
    return teleport
