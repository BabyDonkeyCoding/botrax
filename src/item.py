""" Item Module"""
import math
from enum import Enum

import config


class Item:
    """Item class for player items"""

    def __init__(
        self,
        in_name,
        in_amount,
        in_id,
        in_check_id,
        in_is_equipped,
        in_is_auctionable=True,
        in_decay=-1,
    ):
        self._name = in_name
        self._amount = int(in_amount)
        self._id = in_id
        self._check_id = in_check_id
        self._is_equipped = in_is_equipped
        self._is_auctionable = in_is_auctionable
        self._sell_type = None
        self._status = 100
        self._decay = in_decay

    def load_data(self):
        a = 1

    def get_decay(self):
        """Returns the sell type of the item"""
        return self._decay

    def get_status(self):
        """Returns the sell type of the item"""
        return self._status

    def get_sell_type(self):
        """Returns the sell type of the item"""
        return self._sell_type

    # function to get value of _name
    def get_name(self):
        """Returns the name of the item"""
        return self._name

    def get_amount(self) -> int:
        """Returns amount of items we have from this type"""
        return int(self._amount)

    def get_id(self):
        """Returns item id"""
        return self._id
    
    def get_check_id(self):
        """Returns item id"""
        return self._check_id

    def is_equipped(self):
        """Returns True if item is equipped, False otherwise"""
        return self._is_equipped

    def is_auctionable(self):
        """Returns True if item is auctionable, False otherwise"""
        return self._is_auctionable

    def set_auctionable(self, auctionable):
        """function to set value of _items"""
        self._is_auctionable = auctionable

    def get_auction_value(self):
        """Returns estimated value at auction"""
        estimated_value = 0
        if self._name in config.ITEM_DATA:
            # get item from config data
            item = config.ITEM_DATA[self._name]
            #
            if "auction" in item:
                #
                if "sold" in item["auction"]:
                    #
                    lst2 = list(item["auction"]["sold"].values())
                    # calculate average offering price
                    estimated_value = sum(lst2) / len(lst2)
                elif "offer" in item["auction"]:
                    # create a list with all values
                    lst = list(item["auction"]["offer"].values())
                    if len(lst) > 0:
                        # calculate average offering price
                        estimated_value = sum(lst) / len(lst)
                # set selling price
                estimated_value = int(math.floor(estimated_value))
        #
        return estimated_value

    def define_sell_type(self, player_storage_items):
        """Returns the type of place we want to sell the item to"""
        # get consumables
        item_is_consumable = False
        for consumable in config.PLAYER_DATA["consumables"]:
            if self._name in consumable["name"]:
                item_is_consumable = True
                break
        # item should not be put in bank storage
        item_should_be_stored = self._name in config.PLAYER_DATA["banking"][
            "storage"
        ] and (
            (
                self._name in player_storage_items
                and int(player_storage_items[self._name])
                < int(config.PLAYER_DATA["banking"]["storage"][self._name])
            )
            or self._name not in player_storage_items
            or int(config.PLAYER_DATA["banking"]["storage"][self._name]) < 0
        )
        # item is not a tool the user wants to use
        item_is_a_tool = (
            "tools" in config.PLAYER_DATA
            and self._name in config.PLAYER_DATA["tools"]
            and self._amount <= 1
        )
        # Not selling items conditions
        if (
            item_is_consumable
            or self._is_equipped
            or item_should_be_stored
            or item_is_a_tool
            or self._name in config.world_uniques
        ):
            self._sell_type = ItemSellType.NONE
            return
        #
        item_is_junk = (
            any(key in self._name for key in config.junk_item_keywords)
            or self._name in config.junk_item_keywords
            or self._name in config.no_pickup_items
            or not self._is_auctionable
        )
        #
        auction_price_too_low = (
            self._name in config.ITEM_DATA
            and "auction" in config.ITEM_DATA[self._name]
            and "sold" in config.ITEM_DATA[self._name]["auction"]
            and "shop_price" in config.ITEM_DATA[self._name]
            and (
                math.floor(
                    sum(list(config.ITEM_DATA[self._name]["auction"]["sold"].values()))
                    / len(config.ITEM_DATA[self._name]["auction"]["sold"].values())
                )
                < (max(list(config.ITEM_DATA[self._name]["shop_price"].values())) + 10)
            )
        )
        # item should be sold
        item_should_not_be_auctioned = (
            self._name in config.ITEM_DATA
            and "auction" in config.ITEM_DATA[self._name]
            and (
                (
                    "sold" not in config.ITEM_DATA[self._name]["auction"]
                    and "no_sell" in config.ITEM_DATA[self._name]["auction"]
                    and len(config.ITEM_DATA[self._name]["auction"]["no_sell"]) > 2
                )
                or (
                    "sold" in config.ITEM_DATA[self._name]["auction"]
                    and "no_sell" in config.ITEM_DATA[self._name]["auction"]
                    and len(config.ITEM_DATA[self._name]["auction"]["sold"])
                    < len(config.ITEM_DATA[self._name]["auction"]["no_sell"])
                )
            )
        ) and (
            "fixed_prices" in config.PLAYER_DATA["auction"]
            and self._name not in config.PLAYER_DATA["auction"]["fixed_prices"]
        )
        # item is a weapon for low levels, usually should be sold to shop
        beginner_weapon = (
            self._name in config.DEF_WEAPON_DATA
            and config.DEF_WEAPON_DATA[self._name]["defense"] < 4
        ) or (
            self._name in config.ATT_WEAPON_DATA
            and config.ATT_WEAPON_DATA[self._name]["attack"] < 4
        )
        #
        if (
            item_is_junk
            or item_should_not_be_auctioned
            or beginner_weapon
            or auction_price_too_low
        ):
            self._sell_type = ItemSellType.SHOP
            return
        #
        self._sell_type = ItemSellType.AUCTION
        return

    name = property(get_name)
    amount = property(get_amount)
    id = property(get_id)


class ItemCategory(Enum):
    """Item category"""

    ATTACK_WEAPON = 1
    DEFENSE_WEAPON = 2
    CONSUMABLES = 3
    OTHER = 4
    NECKLACE = 5
    SPECIAL_MAGIC = 6
    SPECIAL_PLANTS = 7
    SPECIAL_DRAWINGS = 8
    RING = 9


class ItemSellType(Enum):
    """Item selling type"""

    NONE = 0
    SHOP = 1
    AUCTION = 2
