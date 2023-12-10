"""The player module"""
import random
import re
import time

from bs4 import BeautifulSoup, NavigableString

import botrax_logger
import config
import move.movement_functions as movement_functions
import pathfinding.path
import races
from item import Item, ItemSellType
from travel import Travel
from util import functions, session_handler

HIGH_VALUE_LIMIT = 2500


class Player:
    """Class for players

    Returns:
        Player: The player object
    """

    target_npc = None
    last_slap = time.time()

    last_att_weapon = None
    last_def_weapon = None

    def __init__(self):
        self._xp = 0
        self._hp = 0
        self._max_hp = 0
        self._int = 0
        self._attp = 0
        self._defp = 0
        self._att_weapon = None
        self._att_weapon_p = 0
        self._def_weapon = None
        self._def_weapon_p = 0
        self._gold = 0
        self._gold_bank = -1
        self._posx = 0
        self._posy = 0
        self._items = []
        self._travel = Travel.RANDOM
        self._path = None
        self._amount_items_carried = 0
        self._status = ""
        self._healing_items = []
        self._academy_limit = 0
        self._recent_equipped = []
        self._save_pos = False
        self._farm = None
        self._invest = None
        self._neck = ""
        self._ring = None
        self._ring_ability_ready = False
        self._phase_energy_cur = -1
        self._phase_energy_max = -1
        self._race = None
        self._group = False
        self._race = None
        self._faction = None
        self._has_high_value_item = False
        self._active_training = None
        self._clan = False
        # set players race
        self.__get_race()
        # storage items
        self._storage_items = {}

    def set_active_training(self, act_training):
        """Set the active training value"""
        self._active_training = act_training

    def get_active_training(self):
        """Returns active training ability or None if not training"""
        return self._active_training

    def carries_high_value_item(self):
        """Returns true if the player has a high value item"""
        return self._has_high_value_item

    def is_in_group(self) -> bool:
        """Returns true if player in group."""
        return self._group

    def set_group(self, in_group):
        """Sets player in group status."""
        self._group = in_group

    def get_storage_items(self):
        """Returns dict of all storage items"""
        return self._storage_items

    def get_phase_energy_cur(self):
        """Returns value"""
        return self._phase_energy_cur

    def get_phase_energy_max(self):
        """Returns value"""
        return self._phase_energy_max

    def set_storage_items(self, dictionary):
        """Set the current storage items"""
        self._storage_items = dictionary

    def __get_race(self):
        res = session_handler.get(
            "https://weltxyz.freewar.de/freewar/internal/profil.php"
        )
        soup = BeautifulSoup(res.text, "lxml")
        # class="maincaption2"
        elements = soup.find_all("p", {"class": "maincaption2"})
        for element in elements:
            if element.text == "Rasse":
                race_string = element.next_sibling.next_element.text
                race, faction = races.get_race_and_faction_from_string(race_string)
                self._race = race
                self._faction = faction

    def get_race(self):
        """Returns players race"""
        return self._race

    def get_faction(self):
        """Returns players race"""
        return self._faction

    def get_ring(self):
        """Returns value of _ring"""
        return self._ring

    def get_neck(self):
        """Returns value of _neck"""
        return self._neck

    # function to get value of _farm
    def get_farm(self):
        """Returns value of _farm"""
        return self._farm

    # function to set value of _farm
    def set_farm(self, new_farm):
        """Sets value of _farm"""
        self._farm = new_farm

    # function to get value of _farm
    def get_invest(self):
        """Returns value of _farm"""
        return self._invest

    # function to set value of _invest
    def set_invest(self, new_invest):
        """Sets value of _invest"""
        self._invest = new_invest

    # function to get value of _xp
    def get_xp(self):
        """Returns value of _xp"""
        return self._xp

    # function to get value of _hp
    def get_hp(self):
        """Returns HP of the player"""
        return self._hp

    # function to get value of _max_hp
    def get_max_hp(self):
        """Returns max HP of the player"""
        return self._max_hp

    # function to get value of _int
    def get_int(self):
        """Returns value of _int"""
        return self._int

    # function to get value of _att
    def get_attp(self):
        """Returns value of attack power"""
        return self._attp

    # function to get value of _def
    def get_defp(self):
        """Returns value of defense power"""
        return self._defp

    # function to get value of _att_weapon
    def get_att_weapon(self):
        """Returns equipped attack weapon"""
        return self._att_weapon

    # function to set value of _att_weapon
    def set_att_weapon(self, att_weapon_string):
        """Set the equipped attack weapon"""
        if "keine" in att_weapon_string:
            self._att_weapon = None
        else:
            self._att_weapon = att_weapon_string
            self.last_att_weapon = att_weapon_string

    # function to get value of _att_weapon_p
    def get_att_weapon_p(self):
        """Returns the value of _att_weapon_p"""
        return self._att_weapon_p

    # function to get value of _def_weapon
    def get_def_weapon(self):
        """Returns the value of _def_weapon"""
        return self._def_weapon

    # function to set value of _def_weapon
    def set_def_weapon(self, defense_weapon_string):
        """Sets the value of _def_weapon"""
        if "keine" in defense_weapon_string:
            self._def_weapon = None
        else:
            self._def_weapon = defense_weapon_string
            self.last_def_weapon = defense_weapon_string

    # function to get value of _def_weapon_p

    def get_def_weapon_p(self):
        """Returns the value of the def_weapon power"""
        return self._def_weapon_p

    # function to get value of _gold
    def get_gold(self):
        """Returns the value of the players gold"""
        return self._gold

    # function to get value of _gold_bank
    def get_gold_bank(self):
        """Returns the value of the gold in the bank"""
        return self._gold_bank

    # function to set value of _gold_bank
    def set_gold_bank(self, gold_in_bank):
        """Set value of _gold_bank"""
        self._gold_bank = gold_in_bank

    # function to get value of _posx
    def get_posx(self):
        """Return value of _posx"""
        return self._posx

    # function to set value of _posx
    def set_posx(self, new_posx):
        """set value of _posx"""
        self._posx = new_posx

    # function to get value of _posy
    def get_posy(self):
        """Returns the value of _posy"""
        return self._posy

    # function to set value of _posy
    def set_posy(self, new_posy):
        """set value of _posy"""
        self._posy = new_posy

    def get_pos(self) -> str:
        """Returns current position as a string"""
        return str(int(self._posx)) + "|" + str(int(self._posy))

    # function to get value of _items
    def get_items(self):
        #
        return self._items

    # function to get value of _healing_items
    def get_healing_items(self):
        #
        return self._healing_items

    # function to set value of _healing_items
    def set_healing_items(self, a):
        self._healing_items = a

    # function to get value of _travel
    def get_travel(self):
        return self._travel

    # function to set value of _travel
    def set_travel(self, in_travel):
        """Set value for travel mode"""
        # set the value
        self._travel = in_travel
        # log output message
        botrax_logger.MAIN_LOGGER.debug("Changed travel to: %s", str(self._travel))

    def get_status(self):
        """Return the player status effects"""
        return self._status

    def is_save_pos(self) -> bool:
        """Return True if the current position is save"""
        return self._save_pos

    # function to set value of _save_pos
    def set_save_pos(self, is_save):
        """Set value of _save_pos"""
        self._save_pos = is_save

    # function to get value of _academy_limit
    def get_academy_limit(self):
        """Returns the players academy limit"""
        return self._academy_limit

    def get_path(self):
        """Returns the path the player has to travel on"""
        return self._path

    def needs_repair(self):
        """Returns True if we need to repair our weapons"""
        return (
            not self._att_weapon and self.get_item_by_name(self.last_att_weapon)
        ) or (not self._def_weapon and self.get_item_by_name(self.last_def_weapon))

    def use_gzk(self, location_list: list):
        """Use of item "gepresste Zauberkugel" to teleport"""
        # try to get item from inventory
        item = self.get_item_by_name("gepresste Zauberkugel")
        # we found the item in our inventory
        if not item:
            return False
        #
        wait = random.uniform(0, 1)
        #
        time.sleep(wait)
        # get post data for zauberkugel target location
        tar_gzk_id = random.choice(location_list)
        post_data = {"z_pos_id": tar_gzk_id}
        # create url
        url = config.URL_USE_ITEM + str(item.get_id())
        check_id = item.get_check_id()
        if check_id:
            url += f"&itemcheckid={check_id}"
        # request the url to use item
        session_handler.post(url, post_data)
        #
        dbg_msg = "Jumped to GZK ID: " + str(tar_gzk_id)
        #
        time.sleep(random.uniform(0.5, 0.75))
        #
        botrax_logger.MAIN_LOGGER.info(dbg_msg)
        # get current position
        pos_x, pos_y = movement_functions.get_current_position(None)
        #
        self._posx = int(pos_x)
        self._posy = int(pos_y)
        # debug
        return True

    # get names of equipped items
    def get_equipped_items(self):
        """Returns a list of equipped items"""
        # variables for method
        e_items = []
        #
        e_items.append("Pfeilbeutel")
        e_items.append(self._neck)
        e_items.append(self._ring)
        #
        # attack weapon
        if self.get_att_weapon():
            e_items.append(self.get_att_weapon())
        # defense weapon
        if self.get_def_weapon():
            e_items.append(self.get_def_weapon())
        #
        e_items.extend(self._recent_equipped)
        #
        self._recent_equipped = e_items
        #
        return e_items

    # function to set value of _path
    def set_destination(self, end):
        """Set destination we want to go to"""
        # check for proper value of destination
        if not end:
            return
        # only set a new path if we are not following one
        self.__set_route(f"{self._posx}|{self._posy}", end)

    def __set_route(self, start, end):
        """Set a route we want to go"""
        #
        if start == end:
            return
        # cancle if we already have a path or end is not given
        if not end:
            return
        #
        if end not in config.COORD_DATA or config.COORD_DATA[end]["avoid"] != 0:
            return
        # if we miss start, we use our current location
        if not start:
            start = f"{self._posx}|{self._posy}"
        # set new path
        self._path = pathfinding.path.get_path(start, end)
        # path has been created?
        if self._path:
            return
        #
        if end in config.COORD_DATA:
            config.COORD_DATA[end]["avoid"] = int(time.time())
        #
        jump_locations = [
            "2",
            "68",
            "87",
            "110",
            "196",
            "290",
            "437",
            "538",
            "816",
            "884",
            "988",
            "1321",
            "1715",
            "4304",
            "5810",
        ]
        #
        botrax_logger.MAIN_LOGGER.info("Problem finding a path. Using Zauberkugel.")
        #
        self.use_gzk(jump_locations)

    # function to set value of _path
    def update_path(self, path):
        """Update the path value"""
        self._path = path

    # function to get value of _posy
    def get_amount_items_carried(self):
        """Returns array with all items"""
        # return list
        return self._amount_items_carried

    def get_bank_limit(self):
        """Returns bank limit of the player"""
        # bank limit is calculated based on XP
        return round((self._xp * 50) + 7500)

    def get_item_overview(self):
        """Returns item overview of the player"""
        # init variables
        has_auc_items = has_shop_items = False
        auc_amount = shop_amount = 0
        # loop through all items the player has in inventory
        for loop_item in self._items:
            # get the sell type of the item
            sell_type = loop_item.get_sell_type()
            if sell_type == ItemSellType.AUCTION:
                has_auc_items = True
                auc_amount += 1
            elif sell_type == ItemSellType.SHOP:
                has_shop_items = True
                shop_amount += 1
        # return results
        return has_auc_items, has_shop_items, auc_amount, shop_amount

    def get_item_by_name(self, name):
        """Returns the item object if item exists, None otherwise"""
        # method variable
        item = None
        # loop all items and find the searched item name
        for loop_item in self._items:
            # found item
            if loop_item.get_name() == name:
                item = loop_item
                break
        # loop all items and find the searched item name
        for loop_item in self._healing_items:
            # found item
            if loop_item.get_name() == name:
                item = loop_item
                break
        #
        return item

    def get_speed(self) -> int:
        """Returns the speed value of the player"""
        return int(round(int(self._int) / 5) + 10)

    def update_player(self, res=None):
        """Update player data, items and abilities."""
        # get item frame with opened menu
        if res is None:
            res = session_handler.get(config.URL_ITEM + "?action=openinv")
        # we received a response with content
        if res:
            # PLAYER
            self.__update_player_data(res)
            # ITEMS
            self.__update_items(res)

    def get_amount_by_name(self, item_name: str) -> int:
        """Get amount of items by name."""
        #
        posession = 0
        #
        for item in self._items:
            # found item
            if item.get_name() == item_name:
                posession += item.get_amount()
        # loop all items and find the searched item name
        for heaing_item in self._healing_items:
            # found item
            if heaing_item.get_name() == item_name:
                posession += heaing_item.get_amount()
        #
        return posession

    def init_position(self):
        """get current player position"""
        #
        pos_x, pos_y = movement_functions.get_current_position(None)
        #
        self.set_posx(int(pos_x))
        self.set_posy(int(pos_y))

    def update_profile(self, profile_description: str):
        """Write given string to the profile"""
        # https://weltxyz.freewar.de/freewar/internal/profil.php?action=change_desc2&change_clan_desc=0
        # {
        # 	"user_desc": "[center][b]BDC[/b][/center]",
        # 	"Submit": "Ändern"
        # }
        test = profile_description
        return test

    def __update_items(self, res):
        # temp save all non auctionable items we have on hand
        non_auctionable = []
        if self._items:
            for item in self._items:
                if not item.is_auctionable():
                    non_auctionable.append(item.get_name())
        # reinit values before creating new item list
        self._items = []
        self._healing_items = []
        self._amount_items_carried = 0
        self._has_high_value_item = False
        # retrieve data
        soup = BeautifulSoup(res.content, "lxml")
        items = soup.find_all("p", {"class": "listitemrow"})
        # loop over items
        for item in items:
            item_name = None
            item_amount = 1
            item_id = None
            is_equipped = False
            is_auctionable = True
            item_decay = -1
            #
            if 'id="filterrow"' in str(item):
                continue
            # get item data as new soup
            soup_item = BeautifulSoup(str(item), "lxml")
            # get item decay timestamp
            item_magic = soup_item.find("span", {"class", "itemmagic"})
            if item_magic:
                magic_s = item_magic.get("title")
                item_decay = functions.get_target_timestamp(magic_s)
            # get item amount <span class="itemamount">6x</span>
            item_amount_element = soup_item.find("span", {"class", "itemamount"})
            if item_amount_element:
                item_amount = int(re.sub("[^0-9]", "", item_amount_element.text))
            #
            item_name_e = soup_item.find("b", {"class": "itemname"})
            if item_name_e:
                item_name = item_name_e.text
            else:
                item_name_e = soup_item.find("span", {"class": "itemequipped itemname"})
                if item_name_e:
                    is_equipped = True
                    item_name = item_name_e.text
            #
            if item_name in non_auctionable:
                is_auctionable = False
            # get item id
            first_item_link = soup_item.find(
                "a", {"href": re.compile(r"act_item_id=")}
            )
            # get links where ID is written in
            item_id_raw = first_item_link.get("href")
            #
            if "itemcheckid" in item_id_raw:
                #
                item_id_s = item_id_raw[item_id_raw.find("act_item_id") : item_id_raw.find("itemcheckid")
                ]
            else:
                #
                item_id_s = item_id_raw[
                    item_id_raw.find("act_item_id") : len(item_id_raw)
                ]
            item_id = int(re.sub("[^0-9]", "", item_id_s))
            #
            item_check_id_s = item_id_raw[
                item_id_raw.find("itemcheckid") : len(item_id_raw)
            ]
            item_check_id = None
            if item_check_id_s:
                item_check_id = int(re.sub("[^0-9]", "", item_check_id_s))
            # check if we gathered all data and add the item to the list
            if item_name and item_amount and item_id:
                # add amount to total item count
                self._amount_items_carried += item_amount
                # check if healing item and add
                new_item = Item(
                    item_name,
                    item_amount,
                    item_id,
                    item_check_id,
                    is_equipped,
                    is_auctionable,
                    item_decay,
                )
                # set the sell type for the item
                new_item.define_sell_type(self._storage_items)
                # determine the value of the item
                self._has_high_value_item |= (
                    int(item_amount * new_item.get_auction_value()) >= HIGH_VALUE_LIMIT
                    and new_item.get_sell_type() == ItemSellType.AUCTION
                )
                # append to healing items if it is one
                if item_name in config.healing_items:
                    self._healing_items.append(new_item)
                # add as normal item
                else:
                    self._items.append(new_item)

    def __update_player_data(self, res):
        # check argument
        if not res:
            return
        # retrieve data
        soup = BeautifulSoup(res.text, "lxml")
        # get health values
        element = soup.find("span", id="itemlpdisp")
        if not element:
            return
        # get HP values
        cur_hp = int(re.sub("[^0-9]", "", str(element.span.b.contents[0])))
        self._hp = cur_hp
        max_hp_s = str(soup.find("span", id="itemlpdisp").contents[2])
        max_hp = int(re.sub("[^0-9]", "", max_hp_s))
        self._max_hp = max_hp
        # get experience value
        xp_s = str(soup.find("p", {"class": "listcaption"}))
        xp_s = xp_s.replace(
            '<span class="hidden1000sep" style="display: none;">.</span>', ""
        ).replace("von 100)", "")
        search_cur = "Erfahrung: "
        pos = xp_s.find(search_cur)
        xp_s = xp_s[pos + len(search_cur) : len(xp_s)]
        xp_s = re.sub("[^0-9]", "", xp_s)
        # set value
        self._xp = int(xp_s)
        # check if this available now (new players do not have academy limit yet)
        if "listrow_aka_battlep" in res.text:
            # academy limit
            element = soup.find("p", id="listrow_aka_battlep")
            aca_limit_s = element.next_element.contents[1].replace(".", "")
            self._academy_limit = int(re.sub("[^0-9]", "", aca_limit_s))
        # get gold value
        element = soup.find("p", id="listrow_money")
        if element and element.contents[1]:
            char_gold = int(re.sub("[^0-9]", "", element.contents[1]))
            #
            self._gold = char_gold
        # get int value
        element = soup.find("p", id="listrow_int")
        intel = 0
        if element and element.contents[1]:
            intel = int(re.sub("[^0-9]", "", element.contents[1]))
        #
        self._int = intel
        # get strength value
        att = 0
        att_w_p = 0
        element = soup.find("p", id="listrow_attackp")
        if element and element.contents[1]:
            att = int(re.sub("[^0-9]", "", element.contents[1]))
        soup_item = BeautifulSoup(str(element), "lxml")
        items = soup_item.find("span", {"class": "valueincreased"})
        if items:
            att_w_p = int(items.contents[0].replace("+", ""))
        # set player value
        self._attp = int(att)
        self._att_weapon_p = int(att_w_p)
        # get attack weapon value
        element = soup.find("p", id="listrow_attackw")
        if element and len(element.contents) > 0:
            att_weapon = (
                element.contents[1]
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(".", "")
                .strip()
            )
            #
            self.set_att_weapon(att_weapon)
        #
        # DEFENSE
        #
        def_p = 0
        def_w_p = 0
        # get player value
        element = soup.find("p", id="listrow_defensep")
        def_p = int(re.sub("[^0-9]", "", element.contents[1]))
        # get weapon value
        soup_item = BeautifulSoup(str(element), "lxml")
        items = soup_item.find("span", {"class": "valueincreased"})
        if items:
            def_w_p = int(items.contents[0].replace("+", ""))
        # set values
        self._defp = int(def_p)
        self._def_weapon_p = int(def_w_p)
        # get dfense weapon name
        element = soup.find("p", id="listrow_defensew")
        if element and len(element.contents) > 0:
            def_weapon = (
                element.contents[1]
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(".", "")
                .strip()
            )
            self.set_def_weapon(def_weapon)
        #
        # NECK
        #
        self.__get_neck(soup)
        # Finger
        self.__get_ring(soup)
        # SPECIAL
        # listrow_special TODO: #8 get information if special ability is available
        #
        # STATUS
        #
        self.__get_status(soup)
        #
        # get all scripts within the page
        scripts = soup.findAll("script")
        # define search_text
        search_cur = "var wielang = "
        search_max = "wielang / "
        # go through all scripts
        for script in scripts:
            # if we find a match then read data
            if search_cur in str(script):
                # get pos data
                pos = str(script).find(search_cur)
                # reade data from script
                phase_energy_current = str(script)[
                    pos + len(search_cur) : pos + len(search_cur) + 6
                ]
                # get pos data
                pos = str(script).find(search_max)
                # reade data from script
                phase_energy_max = str(script)[
                    pos + len(search_max) : pos + len(search_max) + 7
                ]
                phase_energy_current = int(re.sub("[^0-9]", "", phase_energy_current))
                phase_energy_max = int(re.sub("[^0-9]", "", phase_energy_max))
                self._phase_energy_cur = phase_energy_current
                self._phase_energy_max = phase_energy_max

    def __get_neck(self, soup):
        element = soup.find("p", id="listrow_neck")
        if (
            element
            and len(element.contents) > 1
            and not isinstance(element.contents[1], NavigableString)
        ):
            neck_s = (
                element.contents[1]
                .text.replace("/", "")
                .replace("(M)", "")
                .replace(".", "")
                .strip()
            )
            #
            if neck_s != "nichts":
                self._neck = neck_s
            else:
                self._neck = None

    def __get_ring(self, soup):
        element = soup.find("p", id="listrow_ring")
        if element:
            ring_s = (
                element.contents[1]
                .text.replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(".", "")
                .strip()
            )
            #
            ring_remain_s = (
                element.contents[3]
                .text.replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(".", "")
                .strip()
            )
            #
            self._ring_ability_ready = int(ring_remain_s) == 0
            #
            self._ring = ring_s

    def __get_status(self, soup):
        #
        element = soup.find("p", id="listrow_status")
        # element given?
        if not element or len(element.contents) < 1:
            return
        self._status = (
            element.contents[0]
            .text.replace("/", "")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
            .strip()
        )

    xp = property(get_xp)
    hp = property(get_hp)
    max_hp = property(get_max_hp)
    int = property(get_int)
    attp = property(get_attp)
    defp = property(get_defp)
    att_weapon = property(get_att_weapon, set_att_weapon)
    att_weapon_p = property(get_att_weapon_p)
    def_weapon = property(get_def_weapon, set_def_weapon)
    def_weapon_p = property(get_def_weapon_p)
    gold = property(get_gold)
    gold_bank = property(get_gold_bank, set_gold_bank)
    posx = property(get_posx, set_posx)
    posy = property(get_posy, get_posy)
    items = property(get_items)
    travel = property(get_travel, set_travel)
    path = property(get_path, set_destination, update_path)
    status = property(get_status)
    healing_items = property(set_healing_items, get_healing_items)
    save_pos = property(is_save_pos, set_save_pos)
    farm = property(get_farm, set_farm)
    invest = property(get_invest, set_invest)
    neck = property(get_neck)
    ring = property(get_ring)
    race = property(get_race)
    faction = property(get_faction)
    storage_items = property(get_storage_items, set_storage_items)
    has_high_value_item = property(carries_high_value_item)
