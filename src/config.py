"""Configuration module"""
import json
import os
import pathlib
import random
import shutil
import time
import traceback

import botrax_logger
from util import functions

# File paths
CONF_FILE = "config.json"
LOCATION_DATA_FILE = "data/locations.json"
NPC_DATA_FILE = "data/npc_data.json"
ATT_WEAPON_DATA_FILE = "data/att_weapon_data.json"
DEF_WEAPON_DATA_FILE = "data/def_weapon_data.json"
# JSON data objects
COORD_DATA = None
PLAYER_DATA = None
LOCATION_DATA = None
NPC_DATA = None
ITEM_DATA = None
ATT_WEAPON_DATA = None
DEF_WEAPON_DATA = None
# FLAGS
LOGOUT_FLAG = False
# SESSION DATA
SESSION_OBJECT = None
SESSION_COOKIE = ""
USER_AGENT = ""
# BANKING TIMESTAMPS
NEXT_BANKING_CHECK = int(time.time())
NEXT_BANK_PORT = int(time.time())
NEXT_DEPOSIT = int(time.time()) + random.randint(0, 20)
NEXT_WITHDRAW = int(time.time()) + random.randint(10, 20)
NEXT_REPAIR = int(time.time()) + random.randint(20, 60)
# Lists
CRATER_LIST = {}
BLOCKED_LIST = {}
#
UNAVAILABLE_ITEMS = {}
UNAVAILABLE_ITEM_THRESHOLD = random.randint(1800, 3600)
#
RE_LOGIN_WAIT_TIME = 0
CUSTOM_USER_DATA_FILES = ["coordinates", "items"]
# logout timestamp values
LOGOUT_TARGET_HOUR = random.choice([22, 23])
LOGOUT_TARGET_MINUTE = random.randint(1, 59)
# Player task variables
NEXT_QUEST_CHECK = int(time.time()) - 800
#
NEXT_GROUP_CHECK = int(time.time()) + random.randint(10, 20)
# been hunting in this hunting ground
BEEN_HUNTING_THERE = []
# previously stored no cango data
NCG_PREV_AMOUNT = 0
# junk item auction house threshold
AUCTION_PRICE_THRESHOLD = int(30)
#
ITEM_DATA_SIZE_LIMIT = int(10)
#
NEXT_SHOP_PRICE_CHECK = int(time.time()) - 100
#
NEXT_TOWER_ABILITY_USE = int(time.time()) + random.randint(15, 30)
#
NEXT_MISSING_ABILITY_CHECK = int(time.time())
# set next time for config save of json data back to file system
NEXT_CFG_SAVE = int(time.time()) + random.randint(60, 600)
#
SELL_SHOPS = []
#
REPAIR_SHOPS = []
#
GUI_ACTIVE_MODE = False
#
AUTOMOVE = True
#
DEVELOPER_MODE = False
#
LAST_ATTACK_MSG = []
#
NEXT_CHAT_CHECK = int(time.time())
# next timestamp to scan auction house
NEXT_AUCTION_ITEM_SCAN = int(time.time())
# prepay limits
PREPAY_MIN = 4000
PREPAY_MAX = 9001
PREPAY_STEP_SIZE = 500
# amount to prepay on investments
PREPAY_AMOUNT = int(random.randrange(PREPAY_MIN, PREPAY_MAX, PREPAY_STEP_SIZE))
# repair threshold
REPAIR_THRESHOLD = random.randint(50, 80)
#
AVOID_THRESHOLD = random.randint(3600, 4200)
AVOID_NEXT_CHECK = int(time.time()) - 1000
#
INVEST_PICKUP_LOCATIONS = []

def set_shops(player):
    """Set shops based on player's race"""
    #
    for loop_shop in LOCATION_DATA["shops"]:
        if loop_shop["faction"] == player.get_faction().value or loop_shop["faction"] == 3:
            if loop_shop["sell"]:
                SELL_SHOPS.append(str(loop_shop["position"]))
            if loop_shop["repair"]:
                REPAIR_SHOPS.append(str(loop_shop["position"]))


def save():
    """Saves the config files back to drive."""
    # data has been loaded?
    if PLAYER_DATA and LOCATION_DATA and COORD_DATA and ITEM_DATA:
        try:
            # save to file
            with open(CONF_FILE, "w", encoding="utf-8") as player_file:
                # dump json data into the file and save it back to disk
                json.dump(PLAYER_DATA, player_file, ensure_ascii=False, indent=4)
                # close the file after writing
                player_file.close()
            #
            for file_name in CUSTOM_USER_DATA_FILES:
                #
                target_file_path = get_custom_data_file_path(file_name)
                with open(target_file_path, "w", encoding="utf-8") as custom_data_file:
                    #
                    target_data = None
                    # check which data to load
                    if file_name == "coordinates":
                        # get data
                        target_data = COORD_DATA
                    elif file_name == "items":
                        # get data
                        target_data = ITEM_DATA
                    #
                    json.dump(
                        target_data, custom_data_file, ensure_ascii=False, indent=4
                    )
                    # close the file after writing
                    custom_data_file.close()
            #
            with open(LOCATION_DATA_FILE, "w", encoding="utf-8") as loc_file:
                json.dump(LOCATION_DATA, loc_file, ensure_ascii=False, indent=4)
                # close the file after writing
                loc_file.close()
            #
            botrax_logger.DEBUG_LOGGER.debug("Saved JSON data back to files")
        except (
            FileNotFoundError,
            IOError,
            TypeError,
            NameError,
            IndexError,
            BrokenPipeError,
        ):
            # error output
            dbg_msg = "Error during config file save process:\n" + str(
                traceback.print_exc()
            )
            #
            botrax_logger.DEBUG_LOGGER.error(dbg_msg)
            print(dbg_msg)


def load_all_data():
    """Load all json files"""
    global PLAYER_DATA, LOCATION_DATA, LOCATION_DATA_FILE, NPC_DATA, ITEM_DATA, ATT_WEAPON_DATA, DEF_WEAPON_DATA
    #
    PLAYER_DATA = __load(CONF_FILE)
    #
    for custom_file_name in CUSTOM_USER_DATA_FILES:
        #
        __create_user_specific_file(custom_file_name)
        #
        __load_user_files(custom_file_name)
    #
    LOCATION_DATA = __load(LOCATION_DATA_FILE)
    #
    NPC_DATA = __load(NPC_DATA_FILE)
    #
    ATT_WEAPON_DATA = __load(ATT_WEAPON_DATA_FILE)
    #
    DEF_WEAPON_DATA = __load(DEF_WEAPON_DATA_FILE)
    # init values
    __init_user_data_defaults()


def get_custom_data_file_path(file_name):
    """Get custome file path"""
    target_file_path = (
        str(pathlib.Path().resolve())
        + os.sep
        + "usr/"
        + file_name
        + "_"
        + str(PLAYER_DATA["username"])
        + ".json"
    )
    #
    return target_file_path


def __create_user_specific_file(file_name):
    #
    target_file_path = get_custom_data_file_path(file_name)
    #
    if not os.path.exists(target_file_path):
        #
        new_dir_path = str(pathlib.Path().resolve()) + os.sep + "usr"
        if not os.path.exists(new_dir_path):
            os.mkdir(new_dir_path)
        #
        base_path = str(pathlib.Path().resolve())
        #
        shutil.copy2(
            base_path + os.sep + "templates" + os.sep + file_name + ".json",
            target_file_path,
        )
        #
        print("Created user specific data file at %s", target_file_path)


def __load_user_files(file_name):
    global COORD_DATA, ITEM_DATA
    # read data if not already done
    try:
        file_path = "usr/" + file_name + "_" + str(PLAYER_DATA["username"]) + ".json"
        with open(file_path, "r", encoding="utf-8") as file:
            # check which data to load
            if file_name == "coordinates":
                # load json data and save it to global variable
                COORD_DATA = json.load(file)
            elif file_name == "items":
                # load json data and save it to global variable
                ITEM_DATA = json.load(file)
            #
            file.close()
    except (
        FileNotFoundError,
        RuntimeError,
        TypeError,
        NameError,
        IndexError,
        json.JSONDecodeError,
    ):
        # write error to console
        print(traceback.format_exc())


def __init_user_data_defaults():
    # reset player data to default values for current session
    # char gold values
    PLAYER_DATA["banking"]["min_char_gold"] = functions.get_min_char_gold()
    #
    PLAYER_DATA["banking"]["max_char_gold"] = functions.get_max_char_gold()
    #
    now = int(time.time())
    #
    next_logout = int(PLAYER_DATA["breaks"]["next_logout"])
    if next_logout == 0 or now > next_logout:
        PLAYER_DATA["breaks"]["next_logout"] = functions.get_next_logout()
    #
    next_break = int(PLAYER_DATA["breaks"]["next_break"])
    if next_break == 0 or now > next_break:
        PLAYER_DATA["breaks"]["next_break"] = functions.get_next_break()
    # init new for every session
    next_xp_sell = PLAYER_DATA["academy"]["next_xp_sell"]
    #
    if not next_xp_sell or next_xp_sell == 0 or now > next_xp_sell:
        PLAYER_DATA["academy"]["next_xp_sell"] = int(time.time()) + random.randint(
            90, 1900
        )
    # check investments
    for invest in PLAYER_DATA["investments"]:
        if "next_pickup" in invest and (
            invest["next_pickup"] == 0 or now > invest["next_pickup"]
        ):
            invest["next_pickup"] = time.time() + random.randint(400, 800)
    #
    adjusted_farms = 0
    # init farm timings new to avoid farming from the beginning
    for farm in PLAYER_DATA["farming"]:
        # check for farms to be done again
        if "next_farm" in farm and now > farm["next_farm"] and farm["amount_default"] > 0:
            # set new time to farm
            farm["next_farm"] = adjusted_farms * random.randint(500, 2500)
            #
            adjusted_farms += 1
    # reset avoid data
    for item in COORD_DATA.items():
        item[1]["avoid"] = 0


def __load(file_name):
    json_data = None
    # read data
    try:
        with open(file_name, "r", encoding="utf8") as file:
            # load json data
            json_data = json.load(file)
            # close the file after loading the data
            file.close()
    except (IOError, FileNotFoundError, RuntimeError, TypeError, NameError, IndexError):
        # create debug message
        dbg_msg = (
            "Error loading config file: "
            + str(file_name)
            + " :: "
            + str(traceback.print_exc())
        )
        #
        print(dbg_msg)
    return json_data


#
# Healing
#
healing_items = {
    "energetischer Heilzauber": -1,
    "Pilzsuppe": 80,
    "gebratenes Kaktusfleisch": 82,
    "saftiger Apfel": 5,
    "gebratenes Kaktusfleisch ": 82,
    "Flasche Taunektarbier": 30,
    "großer Heiltrank": 15,
    "Nolulawurzel": 7,
    "heilender Schlamm": 40,
}
#
# Junk item keywords
#
junk_item_keywords = [
    "starker Rückangriff",
    "Gewebeprobe von",
    "Seelenstein von",
    "Zeichnung von",
    "Zauber der gefrorenen Rache"
]
#
no_pickup_items = [
    "Fallenentschärfer",
    "Pyramide der Seelen",
    "virenverseuchter Schleim",
    "Pergament der goldenen Einladung",
    "Klopfstock",
    "Wurmfutter",
    "Messsender",
    "Kühlbox mit Gewebeproben",
    "Zauberöl: roter Donner",
    "Auffangschale",
    "ausgelaufenes Öl",
    "Nylfon-Magnet",
    "Schattensplitter",
    "Geisterfunke",
    "heiße Lava"
]
#
# Banking locations
#
BANKING_LOCATIONS = ["109|91", "53|76", "74|101", "98|120", "92|105"]
#
# TRADE Locations
#
# Lardikia: "117|113"
# Konlir: "96|101"
AH_LOCATIONS = ["117|113", "96|101"]
#
no_drinking_pos = ["95|108","99|100", "99|103", "79|103", "96|84", "88|105"]
#
special_consume_items = [
    "Zauber des schnellen Wissens",
    "Taschenuhr des Unermüdlichen",
    "Elixier der Bewegung",
    "Erfahrungszauber des Unermüdlichen",
    "Geldbeutel des Unermüdlichen",
    "Truhe des Unermüdlichen",
    "Wissenszauber aus Reikan",
    "Wissenszauber des Wissbegierigen",
    "Wissenszauber des Unermüdlichen",
    "Zauber des begrenzten Wissens",
]
#
world_uniques = ["Talisman der Blubberheilung"]
#
# URLS
# Base
URL_INTERNAL_BASE = "http://weltxyz.freewar.de/freewar/internal/"
# Specifics
URL_AUTHENTICATION = URL_INTERNAL_BASE + "index.php"
URL_ITEM = URL_INTERNAL_BASE + "item.php"
URL_MAP = URL_INTERNAL_BASE + "map.php"
URL_MAP_RELOAD = URL_INTERNAL_BASE + "map.php?&reload=1"
URL_FRAMESET = URL_INTERNAL_BASE + "friset.php"
URL_MAIN = URL_INTERNAL_BASE + "main.php"
URL_REFRESH = URL_INTERNAL_BASE + "refresh.php"
URL_LOGOUT = URL_INTERNAL_BASE + "logout.php"
URL_LOGOUT_MENU = URL_INTERNAL_BASE + "logout.php?unconfirmed"
URL_ABILITY = URL_INTERNAL_BASE + "ability.php"
URL_FIGHT = URL_INTERNAL_BASE + "fight.php"
URL_QUESTS = URL_INTERNAL_BASE + "quests.php"
URL_CLAN_MENU = URL_INTERNAL_BASE + "clanmenu.php"
URL_CHATFORM = URL_INTERNAL_BASE + "chatform.php"
URL_CHATTEXT = URL_INTERNAL_BASE + "chattext.php"
URL_USE_ITEM = URL_INTERNAL_BASE + "item.php?action=activate&act_item_id="
URL_DEPOSIT_MENU = URL_MAIN + "?arrive_eval=einzahlen"
URL_DEPOSIT_MONEY = URL_MAIN + "?arrive_eval=einzahlen2"
URL_WITHDRAW_MENU = URL_MAIN + "?arrive_eval=abheben"
URL_WITHDRAW_MONEY = URL_MAIN + "?arrive_eval=abheben2"
URL_REPAIR_MENU = URL_MAIN + '?arrive_eval=repair'
URL_REPAIR_ALL_GEAR = URL_MAIN + "?arrive_eval=dorepairall"
URL_PUT_ITEMS_IN_STORAGE_MENU = URL_MAIN + "?arrive_eval=itemabgabe"
URL_EMPTY_STORAGE_MENU = URL_MAIN + "?arrive_eval=itemmitnahme&kat=6&fastback=1"
URL_PURCHASE_MENU = URL_MAIN + "?arrive_eval=einkaufen"
URL_SELL_MENU = URL_MAIN + "?arrive_eval=verkaufen"
URL_AUCTION_SELL_MENU = URL_MAIN + "?arrive_eval=itemabgabe"
URL_STATSMAP = URL_INTERNAL_BASE + "statsmap.php"
