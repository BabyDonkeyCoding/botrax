import json
import random
import traceback

import requests
from bs4 import BeautifulSoup, NavigableString

JSON_DATA = None
# read data if not already done
SHOP_URL = "https://fwwiki.de/index.php/Shops"

try:
    with open(
        "data/locations.json", "r", encoding="utf8"
    ) as file, requests.Session() as session:
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
        session.headers.update({"User-Agent": str(random.choice(user_agent_list))})
        res = session.get(SHOP_URL)
        if not res:
            raise Exception("Could not open webpage: " + SHOP_URL)
        JSON_DATA = json.load(file)
        file.close()
        #
        shops = []
        #
        soup = BeautifulSoup(res.text, "lxml")
        #
        shop_list = soup.find("table")
        body = shop_list.contents[1]
        #
        area = name = position = ""
        #
        for child in body.children:
            if isinstance(child, NavigableString) or "Gebiet" in child.contents[1].text:
                continue
            #
            loop_shop = {}
            #
            buy = sell = False
            faction = -1
            #
            area = child.contents[1].text.replace("\n", "")
            name = child.contents[3].text.replace("\n", "")
            position = child.contents[5].text.replace("/", "|").replace("\n", "")
            buyorsell = str(child.contents[7])
            if "Spieler kann kaufen\xa0&amp;\xa0verkaufen" in str(buyorsell):
                sell = buy = True
            elif "Spieler kann kaufen" in str(buyorsell) and "&amp" not in str(
                buyorsell
            ):
                buy = True
            elif "Spieler kann verkaufen" in str(buyorsell) and "&amp" not in str(
                buyorsell
            ):
                sell = True
            #
            alliance = child.contents[9].text.replace("\n", "") != "—"
            brotherhood = child.contents[11].text.replace("\n", "") != "—"
            #
            if alliance and brotherhood:
                faction = 3
            elif alliance and not brotherhood:
                faction = 1
            elif not alliance and brotherhood:
                faction = 2
            else:
                faction = -1
            #
            repair = child.contents[13].text.replace("\n", "") == "✓"
            safe = child.contents[15].text.replace("\n", "") == "✓"
            #
            loop_shop["area"] = area
            loop_shop["name"] = name
            loop_shop["buy"] = buy
            loop_shop["sell"] = sell
            loop_shop["faction"] = faction
            loop_shop["repair"] = repair
            loop_shop["safe"] = safe
            loop_shop["position"] = position
            #
            shops.append(loop_shop)
        #
        JSON_DATA["shops"] = shops
        #
        with open("data/locations.json", "w", encoding="utf-8") as file:
            json.dump(JSON_DATA, file, ensure_ascii=False, indent=4)
            print("File saved")
            file.close()
        #
except (IOError, FileNotFoundError, RuntimeError, TypeError, NameError, IndexError):
    print("No config file found. Error: " + str(traceback.print_exc()))
