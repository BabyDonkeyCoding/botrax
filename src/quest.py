"""Quest Module"""
from bs4 import BeautifulSoup

import config
from util import session_handler


def claim_quests():
    """Claim quests rewards"""
    # get the quests page
    res = session_handler.get(config.URL_QUESTS)
    # success?
    if res:
        # parse the page
        soup = BeautifulSoup(res.text, "lxml")
        # go through all links on the page
        for link in soup.find_all("a"):
            # save href in variable
            url = link.get("href")
            # check for quest completion link
            if "action=claim" in url:
                # complete quest
                session_handler.get(config.URL_QUESTS + url)
