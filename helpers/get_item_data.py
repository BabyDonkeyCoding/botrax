import json
import random
import re
import traceback

import requests
from bs4 import BeautifulSoup, NavigableString

JSON_DATA = None
# read data if not already done
BASE_URL = "https://fwwiki.de"
BASE_ITEM_URL = "https://fwwiki.de/index.php?title=Kategorie:Alle_Items&pagefrom="
LETTERS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]

try:
    with open(
        "templates/items.json", "r", encoding="utf8"
    ) as file, requests.Session() as session:
        JSON_DATA = json.load(file)
        file.close()
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
        for letter in LETTERS:
            url = BASE_ITEM_URL + letter
            res = session.get(url)
            if not res:
                raise ValueError(f"Could not open webpage: {url}")
            #
            soup = BeautifulSoup(res.text, "lxml")
            #
            links = soup.find_all("a", {"href": re.compile(r"/index.php/")})
            #
            for link in links:
                href = link.get("href")
                title = link.get("title")
                if not title or href != "/index.php/" + title or ":" in href:
                    continue
                #
                json_item = {}
                if title in JSON_DATA:
                    json_item = JSON_DATA[title]
                #
                print(href)
        # open file again to write the data
        with open("templates/items.json", "w", encoding="utf-8") as file:
            # write data
            json.dump(JSON_DATA, file, ensure_ascii=False, indent=4)
            # debug output to user
            print("File saved")
        #
except (IOError, FileNotFoundError, RuntimeError, TypeError, NameError, IndexError):
    print("No config file found. Error: " + str(traceback.print_exc()))
