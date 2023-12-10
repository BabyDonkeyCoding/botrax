"""Module to handle the session object"""
import http
import traceback

import requests
import urllib3

import botrax_logger
import config

SESSION_OBJECT = None


def get(url):
    """Requests the given URL and returns a response object"""
    res = None
    #
    referer = config.URL_REFRESH
    if url == config.URL_LOGOUT:
        referer = config.URL_LOGOUT_MENU
    #
    url = url.replace("weltxyz", f"welt{str(config.PLAYER_DATA['world'])}")
    #
    SESSION_OBJECT.headers.update({"Referer": referer})
    #
    try:
        res = SESSION_OBJECT.get(url)
        err_msg = f"Requested: {url}"
        botrax_logger.DEBUG_LOGGER.debug(err_msg)
    except (
        RuntimeError,
        TypeError,
        NameError,
        http.client.HTTPException,
        ConnectionError,
        urllib3.exceptions.ProtocolError,
        requests.exceptions.ReadTimeout,
    ):
        err_msg = f"Error for URL: {url} \n" + str(traceback.format_exc())
        botrax_logger.MAIN_LOGGER.error(err_msg)
    return res


def post(url, post_data):
    """Sends post request to server"""
    res = None
    #
    try:
        url = url.replace("weltxyz", f"welt{str(config.PLAYER_DATA['world'])}")
        post_header = get_header()
        res = SESSION_OBJECT.post(url, data=post_data, headers=post_header)
        err_msg = "Requested: " + str(url)
        botrax_logger.DEBUG_LOGGER.debug(err_msg)
    except (
        RuntimeError,
        TypeError,
        NameError,
        http.client.HTTPException,
        ConnectionError,
        urllib3.exceptions.ProtocolError,
        requests.exceptions.ReadTimeout,
    ):
        err_msg = f"Error for URL: {url} and Post data: {post_data} \n" + str(
            traceback.format_exc()
        )
        botrax_logger.MAIN_LOGGER.error(err_msg)
    return res


def post_login(url, post_data):
    """Posts a request to the given URL and returns a response object"""
    res = None
    #
    try:
        url = url.replace("weltxyz", f"welt{str(config.PLAYER_DATA['world'])}")
        loc_headers = __get_login_header()
        res = SESSION_OBJECT.post(url, headers=loc_headers, data=post_data)
        err_msg = "Requested: " + str(url)
        botrax_logger.DEBUG_LOGGER.debug(err_msg)
    except (
        RuntimeError,
        TypeError,
        NameError,
        http.client.HTTPException,
        ConnectionError,
        urllib3.exceptions.ProtocolError,
        requests.exceptions.ReadTimeout,
    ):
        err_msg = f"Error for URL: {url} and Post data: {post_data} \n" + str(
            traceback.format_exc()
        )
        botrax_logger.MAIN_LOGGER.error(err_msg)
    return res


def get_header():
    """Returns header for connection object"""
    header = {
        "Host": f"welt{str(config.PLAYER_DATA['world'])}.freewar.de",
        "User-Agent": str(config.USER_AGENT),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "41",
        "Origin": "http://weltxyz.freewar.de",
        "Connection": "keep-alive",
        "Referer": config.URL_REFRESH,
        "Cookie": "PHPSESSID=" + str(config.SESSION_COOKIE),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    return header


def __get_login_header():
    header = {
        "Host": f"welt{str(config.PLAYER_DATA['world'])}.freewar.de",
        "User-Agent": str(config.USER_AGENT),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "41",
        "Origin": "http://weltxyz.freewar.de",
        "Connection": "keep-alive",
        "Referer": "http://weltxyz.freewar.de/freewar/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    return header
