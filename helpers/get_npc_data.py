import requests
from bs4 import BeautifulSoup
import json


def main():
    with requests.Session() as s:
        res = s.get('http://fwwiki.de/index.php/NPCs_(Liste)')
        if res:
            soup = BeautifulSoup(res.text, 'lxml')
            npcs = {}
            npc_list_1 ={}
            npc_list_2 ={}
            npc_list_3 ={}
            #
            tds = soup.find_all('td', {"class": "npc angreifbar"})
            for npc in tds:
                add_npc_element(npc_list_1, npc, '')
            #
            tds = soup.find_all('td', {"class": "gruppennpc angreifbar"})
            for npc in tds:
                add_npc_element(npc_list_2, npc, 'Group')
            #
            tds = soup.find_all('td', {"class": "uniquenpc angreifbar"})
            for npc in tds:
                add_npc_element(npc_list_3, npc, 'Unique')

            npcs['npcs']= npc_list_1
            npcs['group_npcs'] = npc_list_2
            npcs['unique_npcs'] = npc_list_3
            #
            with open('helpers/npc_data_export.json', 'w', encoding='utf-8') as f:
                json.dump(npcs, f, ensure_ascii=False, indent=4)

def add_npc_element(npc_list, npc, type):
    npc_el = {}
    # npc_el['name']= npc.text
    npc_el['attack'] = int(npc.next_sibling.next_sibling.text)
    npc_el['hp'] = int(npc.next_sibling.next_sibling.next_sibling.next_sibling.text)
    npc_el['xp'] = int(npc.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.text)
    npc_el['gold'] = int(npc.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.text)
    npc_el['type'] = type
                #
    npc_list[npc.text.upper()] = npc_el

main()
