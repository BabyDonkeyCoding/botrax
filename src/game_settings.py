"""Module to init game settings"""
from util import session_handler
import config

def init_settings():
    """ Sets the default settings we want"""
    # deactivate fight reports
    session_handler.get(config.URL_INTERNAL_BASE+'profil.php?action=skipreports')
    # activate time stamps in the chat
    session_handler.get(config.URL_INTERNAL_BASE+'profil.php?action=enabletimestamps')
    
