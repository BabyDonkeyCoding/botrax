import json

import requests
from bs4 import BeautifulSoup


def main():
    """
    Test comments
    TODO: Remove this deprecated method
    ! deprecated
    """
    length = 0
    with requests.Session() as s:
        res = s.get('https://fwwiki.de/index.php/Koordinaten_(Liste)')
        if res:
            soup = BeautifulSoup(res.text, 'lxml')
            span = soup.find_all('div', {"class": "mw-parser-output"})[0]
            #soup = BeautifulSoup(span.text, 'lxml')
            div_prev = False
            jsondata = {}
            area = ''
            for element in span:
                # find the div
                if div_prev:
                    __parse_koords(jsondata, element.text, area)
                    div_prev = False
                if element.name == 'div':
                    area = element.text.replace('\xa0', '')
                    div_prev = True
            #
            length = len(jsondata)
            #
            with open('templates/coordinates_raw.json', 'w', encoding='utf-8') as out_file:
                json.dump(jsondata, out_file, ensure_ascii=False, indent=4)
    #
    print("Finished getting map data from website")
    print(f"Worked on {length} items")


def __parse_koords(jsondata, string, area):
    coord_list = string.split(';')
    for listitem in coord_list:
        # new element
        pos = {}
        # set area string
        pos['area'] = area
        # coords
        x_coord = listitem.split(',')[0].replace(' ', '')
        pos['x'] = x_coord
        pos['y'] = listitem.split(',')[1]
        pos["dungeon"] = bool(int(x_coord) < 0)
        pos['cango'] = True
        pos['avoid'] = 0
        #
        jsondata[str(pos['x']+"|"+pos['y'])] = pos


main()
