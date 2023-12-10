"""Module for fight specific funtions"""
import re


def get_npc_att_p(npc_s):
    """Retrieves NPC attack power from given string."""
    search_txt = "Angriffsstärke: "
    npc_att_p = 999999
    # get attack power of NPC
    if search_txt in npc_s:
        pos = npc_s.find(search_txt)
        npc_s = npc_s[pos + len(search_txt) : len(npc_s)]
        npc_att = re.sub("[^0-9]", "", npc_s)
        if npc_att and npc_att != "":
            npc_att_p = int(npc_att)
    # return value
    return npc_att_p
