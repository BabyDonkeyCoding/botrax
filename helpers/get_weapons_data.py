import json
import re

import requests
from bs4 import BeautifulSoup, NavigableString


def main(url, main_att, tar_file):
    with requests.Session() as session:
        res = session.get(url)
        if res:
            soup = BeautifulSoup(res.text, 'lxml')
            weapons = {}
            #
            table = soup.find('tbody')
            for child in table.contents:
                if type(child) == NavigableString or child.contents[1].name == 'th':
                    continue
                # init new item
                weapon = {}
                #
                name = child.contents[1].text.replace('\n', '')
                main_att_p = 0
                strength = 0
                intelligence = 0
                academy = 0
                race = ''
                w_magic = False
                #
                txt = child.contents[3].text
                if txt == '\n':
                    continue
                if '—' not in txt and '-' not in txt:
                    main_att_p = int(txt.replace('\n', '').replace('.', ''))
                txt = child.contents[5].text
                if '—' not in txt and '-' not in txt:
                    strength = int(txt.replace('\n', '').replace('.', ''))
                txt = child.contents[7].text
                if '—' not in txt and '-' not in txt:
                    intelligence = int(txt.replace('\n', '').replace('.', ''))
                txt = child.contents[9].text
                if '—' not in txt and '-' not in txt:
                    academy = int(txt.replace('\n', '').replace('.', ''))
                #
                race = child.contents[11].text.replace('\n', '')
                if race == 'alle Rassen':
                    race = -1
                elif race == 'Taruner':
                    race = 7
                elif race == 'Dunkler Magier':
                    race = 6
                elif race == 'Mensch/Kämpfer':
                    race = 1
                elif race == 'Mensch/Arbeiter':
                    race = 2
                elif race == 'Mensch/Zauberer':
                    race = 3
                elif race == 'Onlo':
                    race = 4
                elif race == 'Serum-Geist':
                    race = 5
                elif race == 'Natla-Händler':
                    race = 9
                elif race == 'Keuroner':
                    race = 8
                # AVG PRICE
                txt = child.contents[13].text
                avg_price = -1
                if '—' not in txt:
                    avg_price = child.contents[13].text.replace('\n', '')
                    avg_price = int(re.sub("[^0-9]", "", avg_price))
                # MAGIC
                txt = child.contents[15].text
                if '—\n' != txt:
                    w_magic = True
                #
                weapon[main_att] = main_att_p
                weapon['strength'] = strength
                weapon['intelligence'] = intelligence
                weapon['academy'] = academy
                weapon['race'] = race
                weapon['avg_price'] = avg_price
                weapon['magic'] = w_magic
                #
                weapons[name] = weapon
            #
            with open(tar_file, 'w', encoding='utf-8') as target_json_file:
                json.dump(weapons, target_json_file,
                          ensure_ascii=False, indent=4)
            target_json_file.close()


main('http://fwwiki.de/index.php/Angriffswaffe',
     'attack', 'data/att_weapon_data.json')
main('http://fwwiki.de/index.php/Verteidigungswaffe',
     'defense', 'data/def_weapon_data.json')
