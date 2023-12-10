"""Main Bot Module"""
import datetime
import logging
import os
import random
import signal
import sys
import time
import traceback

import requests

import abilities
import bot_tasks
import botrax_logger
import config
import equip
import farming
import field
import game_settings
import healing
import investments
import loot
import messages
import move.movement as movement
import move.movement_functions as movement_functions
import player_tasks
import race_abilities
import repair
import ring
from banking import banking_gold
from chat import chat, chat_config
from dungeons import dungeon
from grouping import group
from npc import npc_check
from player import Player
from trade import auction_house, trade
from util import functions, session_handler
from xp import xp_sell

WORK_PATHS = ["log"]


class Bot:
    """Defines a bot that will play the game on its own"""

    def __init_data(self):
        # init variables
        session = None
        player = None
        # get current working directory
        self.__setup_work_directories()
        # load all config files
        config.load_all_data()
        # set default logging level
        log_level = logging.INFO
        # set debug logging for development environment
        if config.DEVELOPER_MODE:
            log_level = logging.DEBUG
        # init all loggers
        botrax_logger.init(log_level)
        # set user agent
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        ]
        config.USER_AGENT = random.choice(user_agents)
        # request a session
        session = requests.Session()
        # user shall use a proxy list?
        if "connection" in config.PLAYER_DATA:
            # PROXIES
            proxy_list = config.PLAYER_DATA["connection"]["proxy_list"]
            proxy = random.choice(proxy_list)
            session.proxies = {"http://": proxy, "https://": proxy}
            # get user agents
            if "user_agent" in config.PLAYER_DATA["connection"]:
                # USER AGENT
                user_agents = config.PLAYER_DATA["connection"]["user_agent"]
                # set user agent
                config.USER_AGENT = random.choice(user_agents)
        # set user agent to mask python traces
        session.headers.update({"User-Agent": str(config.USER_AGENT)})
        # session could not be created
        if not session:
            return session, player
        #
        session_handler.SESSION_OBJECT = session
        # login to the game
        self.__login(session)
        # new player instance
        player = Player()
        # get current data for the player
        player.update_player(None)
        abilities.update_abilities(None)
        # set custom shops
        config.set_shops(player)
        # start init phase
        botrax_logger.DEBUG_LOGGER.debug(
            "#############  Starting Init Phase #############"
        )
        #
        game_settings.init_settings()
        # update session headers
        session_handler.SESSION_OBJECT.headers.update(
            {"Upgrade-Insecure-Requests": "1"}
        )
        session_handler.SESSION_OBJECT.headers.update({"Sec-Fetch-Dest": "frame"})
        session_handler.SESSION_OBJECT.headers.update({"Sec-Fetch-Mode": "navigate"})
        session_handler.SESSION_OBJECT.headers.update({"Sec-Fetch-Site": "same-origin"})
        # get current position
        pos_x, pos_y = movement_functions.get_current_position(None)
        #
        player.set_posx(int(pos_x))
        player.set_posy(int(pos_y))
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "############# Init Phase Finished #############"
        )
        #
        return session, player

    def __setup_work_directories(self):
        #
        work_dir = os.getcwd()
        # create necessary directories
        for path in WORK_PATHS:
            # create debug path
            dir_path = os.path.join(work_dir, path)
            # check debug path existence
            path_exists = os.path.isdir(dir_path)
            # create if not existing
            if not path_exists:
                # make the directory
                os.mkdir(dir_path)

    def __get_field_time(self, player: Player):
        #
        delay = player.get_amount_items_carried() - player.get_speed()
        #
        delay = max(delay, 0)
        # init variables
        if "Rennen" in player.get_status():
            limit = random.uniform(2, 3)
        #
        elif "schnelle Bewegung" in player.get_status():
            limit = random.uniform(4, 5.5) + delay
        else:
            limit = random.uniform(4.5, 6.5) + delay
        # randomly add some time to walking
        if functions.get_chance(0.02):
            limit += random.uniform(1, 1.5)
        #
        return limit

    def __loop(self, player: Player):
        # init logout variable
        logout = False
        # check position for further actions
        res = session_handler.get(config.URL_MAIN + "?yscroll=0")
        # go into while loop as long as there is no need to logout
        while True:
            try:
                # init loop variables
                count = 0
                delta = 0
                limit = 0
                then = int(time.time())
                limit = self.__get_field_time(player)
                #
                player.update_player()
                #
                botrax_logger.DEBUG_LOGGER.debug(
                    "Timing_00:%s", str(int(time.time() - then))
                )
                # bot specific tasks
                bot_tasks.perform_tasks()
                #
                botrax_logger.DEBUG_LOGGER.debug(
                    "Timing_2:%s", str(int(time.time() - then))
                )
                # repeat field actions while waiting for next move
                while delta < limit:
                    # empty response?
                    response_datetime = datetime.datetime.strptime(
                        res.headers["Date"], "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    #
                    now = datetime.datetime.now()
                    #
                    response_datetime = response_datetime.replace(hour=int(now.hour))
                    #
                    delta = now - response_datetime
                    seconds = delta.seconds
                    #
                    if seconds > 1 or not res:
                        res = session_handler.get(config.URL_MAIN + "?yscroll=0")
                    #
                    field.check_field(res, player)
                    # use tower control ability after we walked
                    race_abilities.tower_control_ability(player)
                    #
                    if chat.check_chat(player):
                        res = session_handler.get(config.URL_MAIN + "?yscroll=0")
                                # get current position
                        pos_x, pos_y = movement_functions.get_current_position(None)
                        #
                        player.set_posx(int(pos_x))
                        player.set_posy(int(pos_y))
                    # take field actions
                    res = self.__field_actions(res, player)
                    #
                    time.sleep(random.uniform(0.6, 0.9))
                    # calculate time difference
                    delta = int(time.time()) - then
                    #
                    count += 1
                #
                botrax_logger.DEBUG_LOGGER.debug("Loops:%s", str(count))
                #
                botrax_logger.DEBUG_LOGGER.debug(
                    "Timing_3:%s", str(int(time.time() - then))
                )
                #
                if not res:
                    continue
                # train your abilities
                abilities.training(player)
                # check investments we want to do
                if config.AUTOMOVE:
                    #
                    investments.check(res, player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_4:%s", str(int(time.time() - then))
                    )
                    #
                    xp_sell.check_xp_sell(res, player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_5:%s", str(int(time.time() - then))
                    )
                    #
                    ring.check_ring(res, player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_6:%s", str(int(time.time() - then))
                    )
                    #
                    farming.handle_farming(player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_9:%s", str(int(time.time() - then))
                    )
                    # player specific tasks
                    logout = player_tasks.handle_tasks(player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_10:%s", str(int(time.time() - then))
                    )
                    if logout:
                        break
                    #
                    dungeon.check_dungeon(res, player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_11:%s", str(int(time.time() - then))
                    )
                    # check chat again before next step
                    if chat.check_chat(player):
                        res = session_handler.get(config.URL_MAIN + "?yscroll=0")
                                # get current position
                        pos_x, pos_y = movement_functions.get_current_position(None)
                        #
                        player.set_posx(int(pos_x))
                        player.set_posy(int(pos_y))
                    #
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_12:%s", str(int(time.time() - then))
                    )
                    # try to walk
                    movement.init_move(player)
                    botrax_logger.DEBUG_LOGGER.debug(
                        "Timing_13:%s", str(int(time.time() - then))
                    )
                # we are in not move mode
                else:
                    # wait random time
                    time.sleep(random.uniform(1, 2))
                    # get current position
                    pos_x, pos_y = movement_functions.get_current_position(None)
                    #
                    player.set_posx(int(pos_x))
                    player.set_posy(int(pos_y))
            # catch any errors occuring during loop
            except:
                botrax_logger.DEBUG_LOGGER.error(traceback.format_exc())
        #
        if logout:
            # log out of the game
            self.__logout(player)

    def __field_actions(self, res, player: Player):
        #
        then = int(time.time())
        # check position for further actions
        if not res or player.get_pos() == "96|99":
            return res
        # check for messages, these are blocking the main frame
        in_combat, res = messages.check_for_messages(res, player)
        # check group related things
        group.handle_grouping(res, player)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_1:%s", str(int(time.time() - then))
        )
        #
        res = npc_check.perform(res, player)
        # check for NPC to kill
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_2:%s", str(int(time.time() - then))
        )
        # empty response?
        if not res:
            # do nothing -> return
            return None
        # check player equipment
        equip.check_equip(player)
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_3:%s", str(int(time.time() - then))
        )
        # heal the character
        healing.heal_player(res, player, in_combat)
        # check if we can repair our gear
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_4:%s", str(int(time.time() - then))
        )
        repair.check(res, player)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_5:%s", str(int(time.time() - then))
        )
        # loot ground
        res = loot.check_field(res, player)
        # empty response?
        if not res:
            # do nothing -> return
            return None
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_6:%s", str(int(time.time() - then))
        )
        # repair and heal if possible
        trade.perform_trade_actions(res, player)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_7:%s", str(int(time.time() - then))
        )
        # do banking if possible
        banking_gold.do_banking(res, player)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_8:%s", str(int(time.time() - then))
        )
        # buy items from auction house
        auction_house.use(res, player)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "InnerTiming_9:%s", str(int(time.time() - then))
        )
        #
        return res

    def __login(self, session):
        # adjust session headers
        session.headers.update({"Host": f"welt{str(config.PLAYER_DATA['world'])}.freewar.de"})
        session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
        )
        session.headers.update({"Accept-Encoding": "gzip, deflate, br"})
        # create login post data
        login_post_data = {
            "name": config.PLAYER_DATA["username"],
            "password": config.PLAYER_DATA["password"],
            "submit": "Einloggen",
        }
        # login on main page with post data
        res = session_handler.post_login(config.URL_AUTHENTICATION, login_post_data)
        # retrieve current session id
        config.SESSION_COOKIE = session.cookies.get_dict().get("PHPSESSID")
        # login will create a session cookie, set it to session headers
        session.headers.update({"Cookie": "PHPSESSID=" + str(config.SESSION_COOKIE)})
        #
        if not res:
            botrax_logger.DEBUG_LOGGER.warning("No connection to game -> Exiting")
            sys.exit(0)
        #
        if "oder PW falsch" in res.text:
            botrax_logger.DEBUG_LOGGER.warning("Wrong password or username -> Exiting")
            sys.exit(0)
        #
        if "gebannt" in res.text:
            botrax_logger.DEBUG_LOGGER.warning("USER BANNED -> Exiting")
            sys.exit(0)
        # debug
        botrax_logger.DEBUG_LOGGER.debug(
            "Login seems okay as %s", str(config.PLAYER_DATA["username"])
        )
        #
        wait = random.uniform(1, 2)
        time.sleep(wait)
        # continue to the iframe version of the game
        session.headers.update({"Referer": config.URL_AUTHENTICATION})
        #
        res = session_handler.get(config.URL_FRAMESET)
        #
        botrax_logger.DEBUG_LOGGER.debug(
            "Was able to continue to non-frameset version of the game"
        )
        # update header after we are inside the iframe version
        session.headers.update({"Referer": config.URL_REFRESH})
        # return the ingame page response
        return res

    def __logout(self, player: Player):
        if config.LOGOUT_FLAG:
            return
        #
        config.LOGOUT_FLAG = True
        #
        if not player.is_save_pos():
            if player.use_gzk(["73", "1079"]):
                #
                dbg_msg = "Jumped to save position for logout."
                #
                botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # save config back to file
        config.save()
        # wait a bit before logging out
        wait = random.uniform(2, 7)
        time.sleep(wait)
        #
        minutes, _ = divmod(config.RE_LOGIN_WAIT_TIME, 60)
        hours, minutes = divmod(minutes, 60)
        #
        if player.is_in_group():
            chat.talk_with_chat(
                random.choice(chat_config.LOGOUT_MESSAGES), chat.Chatchannel.GROUP
            )
        #
        dbg_msg = (
            "Logging out of the game | Waiting for "
            + str(hours)
            + " hours and "
            + str(minutes)
            + " minutes to log back in."
        )
        # logout now
        session_handler.get(config.URL_LOGOUT)
        #
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # wait some time
        time.sleep(config.RE_LOGIN_WAIT_TIME)
        #
        self.startup()

    ################################
    # Starting method
    ################################
    def startup(self):
        """Start the bot

        Args:
            conf (str): path to the configuration file
        """
        signal.signal(signal.SIGTERM, self.handle_iterrupt_bot)
        #
        try:
            #
            config.LOGOUT_FLAG = False
            session, player = self.__init_data()
            if session and player:
                self.__loop(player)
            else:
                #
                config.save()
                print("Init Phase not succesfull")
                botrax_logger.MAIN_LOGGER.error("Init Phase Error")
        except KeyboardInterrupt:
            self.handle_iterrupt_bot(None, None)
        except:
            #
            config.save()
            botrax_logger.DEBUG_LOGGER.error(traceback.format_exc())
            print(traceback.format_exc())

    def handle_iterrupt_bot(self, name, test):
        """Handle external interrupts"""
        config.save()
        #
        dbg_msg = f"Handling Interrupt from: {name} and {test}"
        botrax_logger.DEBUG_LOGGER.error(dbg_msg)
        #
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
