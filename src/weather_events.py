"""Module to handle weather and world events ingame"""
# Gigantische Lavamassen werden aus dem Vulkan von Anatubien geschleudert und die Rauchsäule ist von überall aus zu sehen.

from player import Player

VULCAN_START_MSG = 'Dicker Qualm steigt aus dem Vulkan von Anatubien auf.'
VULCAN_ACTIVE_MSG = 'Gigantische Lavamassen werden aus dem Vulkan von Anatubien geschleudert und die Rauchsäule ist von überall aus zu sehen.'
VULCAN_END_MSG ='Der Vulkan von Anatubien beruhigt sich langsam und nur die Rauchsäule über dem Vulkan und leises Rumpeln deuten noch auf die Katastrophe hin.'

def check_weather(msg, player: Player):
    """Handle weather events"""
    player.get_pos()
