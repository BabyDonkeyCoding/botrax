"""Module for races and factions"""
from enum import Enum


class Race(Enum):
    """Races within the game Freewar"""
    MENSCH_KAEMPFER = 1
    MENSCH_ARBEITER = 2
    MENSCH_ZAUBERER = 3
    ONLO = 4
    SERUM_GEIST = 5
    DUNKLER_MAGIER = 6
    TARUNER = 7
    KEURONER = 8
    NATLA = 9


def get_race_and_faction_from_string(race_string):
    """Converts Race String to Enum"""
    # init variables
    race = None
    # check string value
    if race_string == 'Taruner':
        race = Race.TARUNER
    elif race_string == 'Dunkler Magier':
        race = Race.DUNKLER_MAGIER
    elif race_string == 'Mensch/Kämpfer':
        race = Race.MENSCH_KAEMPFER
    elif race_string == 'Mensch/Arbeiter':
        race = Race.MENSCH_ARBEITER
    elif race_string == 'Mensch/Zauberer':
        race = Race.MENSCH_ZAUBERER
    elif race_string == 'Onlo':
        race = Race.ONLO
    elif race_string == 'Serum-Geist':
        race = Race.SERUM_GEIST
    elif race_string == 'Natla - Händler':
        race = Race.NATLA
    elif race_string == 'Keuroner':
        race = Race.KEURONER
    #
    faction = __get_faction(race)
    # return result
    return race, faction


class Faction(Enum):
    """Factions within the game Freewar"""
    ALLIANCE = 1
    BROTHERHOOD = 2
    NEUTRAL = 3


def __get_faction(race: Race):
    """Returns the faction of the given race"""
    # check race
    if race.value == Race.NATLA.value:
        return Faction.NEUTRAL
    if race.value < Race.SERUM_GEIST.value:
        return Faction.ALLIANCE
    #
    return Faction.BROTHERHOOD
