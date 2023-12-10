"""Module for group related tasks and actions"""
import random
import re
import time

from bs4 import BeautifulSoup

import botrax_logger
import config
from chat import chat_config
from chat.chat import Chatchannel, talk_with_chat
from util import functions, session_handler


def manage_group(player):
    """Handles all group related tasks."""
    # check group tasks
    if time.time() <= config.NEXT_GROUP_CHECK:
        return
    # get group menu
    res = session_handler.get(
        config.URL_INTERNAL_BASE + "clanmenu.php?action=groupmenu"
    )
    # problem loading url?
    if not res:
        return
    #
    in_group, grp_admin = __in_grp(res)
    #
    player.set_group(in_group)
    # in case we are leader of the group
    if grp_admin:
        # change the leader to some random group member except us
        __change_leader(res)
    # in case we are in development mode and not in a group
    if not in_group and config.DEVELOPER_MODE:
        # join a group
        __join_existing_group()
    #
    config.NEXT_GROUP_CHECK = _get_next_group_check()


def _get_next_group_check() -> int:
    """Returns the next break time stamp"""
    return int(time.time() + random.randint(60, 120))

def __change_leader(res):
    # get the menu
    res = session_handler.get(
        config.URL_INTERNAL_BASE + "clanmenu.php?action=groupleader"
    )
    # soup the result
    soup = BeautifulSoup(res.text, "lxml")
    # get all player links
    links = soup.find_all("a", {"href": re.compile(r"action=groupleader2")})
    # choose random
    tar = random.choice(links)
    href = tar.get("href")
    #
    time.sleep(random.randint(3, 7))
    #
    session_handler.get(config.URL_INTERNAL_BASE + href)


def __in_grp(res):
    in_grp = False
    grp_admin = False
    # https://weltxyz.freewar.de/freewar/internal/clanmenu.php?action=groupmenu
    if "Gruppe von" in res.text:
        #
        grp_admin = bool(
            "Gruppe von " + str(config.PLAYER_DATA["username"]) in res.text
        )
        #
        in_grp = True
        # check amount of players in group
        soup = BeautifulSoup(res.text, "lxml")
        links = soup.find_all(
            "a", {"href": re.compile(r"action=watchuser&act_user_id")}
        )
        members = len(links)
        #
        if members == 1:
            #
            botrax_logger.MAIN_LOGGER.info("Leaving empty group")
            #
            time.sleep(random.uniform(1, 2))
            #
            session_handler.get(
                config.URL_INTERNAL_BASE + "clanmenu.php?action=groupleave"
            )
            #
            time.sleep(random.uniform(1, 2))
            #
            session_handler.get(
                config.URL_INTERNAL_BASE + "clanmenu.php?action=groupleave2"
            )
            #
            in_grp = grp_admin = False
    #
    return in_grp, grp_admin


def __join_existing_group():
    # open group finder menu
    res = session_handler.get(config.URL_CLAN_MENU + "?action=groupfinder")
    #
    loop_id = -1
    loop_active = 0
    #
    if not res:
        return False
    #
    soup = BeautifulSoup(res.text, "lxml")
    #
    for link in soup.find_all("a"):
        # https://weltxyz.freewar.de/freewar/internal/fight.php?action=groupjoinrand&openid=34
        href = link.get("href")
        # check join link
        if (
            "action=groupjoinrand&openid=" in href
            and "&openid=-1" not in href
            and config.PLAYER_DATA["username"] not in link.text
        ):
            # get number of active players
            parent = link.parent.text
            search = "aktiv:"
            pos_1 = parent.find(search) + len(search)
            active_number = parent[pos_1 : pos_1 + 3]
            active_number = int(re.sub("[^0-9]", "", active_number))
            # get group id
            href = href[href.find("openid=") : len(href)]
            href_id = int(re.sub("[^0-9]", "", href))
            # check against loop values
            if active_number > loop_active:
                loop_active = active_number
                loop_id = href_id
            #
    # check if we found a good group
    if loop_id == -1 or loop_active < 2:
        return False
    # log info
    botrax_logger.MAIN_LOGGER.info("Joining an existing group")
    #
    session_handler.get(
        config.URL_INTERNAL_BASE
        + "fight.php?action=groupjoinrand&openid="
        + str(loop_id)
    )
    #
    wait = random.uniform(8, 14)
    time.sleep(wait)
    #
    talk_with_chat(random.choice(chat_config.GREETINGS), Chatchannel.GROUP)
    # return result
    return True
