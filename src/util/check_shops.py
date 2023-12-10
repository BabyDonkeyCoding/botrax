"""Get shop prices from the website https://freewar.zocker.eu/ """
import random

import requests
from bs4 import BeautifulSoup

import botrax_logger
import config


def _get_header():
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "freewar.zocker.eu",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    return header


def update_shops():
    """Check the website with shop prices"""
    with requests.Session() as session:
        # set user agent
        user_agent_list = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
        ]
        # set user agent to mask python traces
        session.headers.update(_get_header())
        session.headers.update({"User-Agent": str(random.choice(user_agent_list))})
        #
        res = session.get("https://freewar.zocker.eu/")
        # get soup
        soup = BeautifulSoup(res.text, "lxml")
        # get all tables
        table = soup.find_all("table", {"class": "shops"})
        # get target table
        table_soup = table[0]
        # reset old data
        if "best_shop" in config.PLAYER_DATA:
            del config.PLAYER_DATA["best_shop"]
        if "okay_shops" in config.PLAYER_DATA:
            del config.PLAYER_DATA["okay_shops"]
        # define variables
        tar_td = ""
        loop_shop = ""
        okay_shops = []
        #
        for idx, table_row in enumerate(table_soup.contents):
            # skip first row
            if (
                idx == 0
                or len(table_row.contents) < 3
                or table_row.contents[3].text == ""
            ):
                continue
            # get values
            loop_shop = table_row.contents[2].text.replace("/", "|")
            start_array = loop_shop.split("|")
            # get start and end coordinates
            pos_x = int(start_array[0])
            posy_y = int(start_array[1])
            if 0 < pos_x > 180 or 0 < posy_y > 180:
                continue
            tar_td = float(table_row.contents[3].text)
            # check values
            if tar_td <= 1.1 and len(okay_shops) > 1:
                break
            #
            if tar_td > 1 and loop_shop in config.SELL_SHOPS:
                okay_shops.append(loop_shop)
        #
        if len(okay_shops) > 0:
            config.PLAYER_DATA["okay_shops"] = okay_shops
            # log acitivty
            botrax_logger.DEBUG_LOGGER.debug("Updated best shop")
