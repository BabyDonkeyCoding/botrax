import json
import traceback

JSON_DATA = None
# read data if not already done
try:
    with open("templates/coordinates.json", 'r', encoding='utf8') as file:
        #
        JSON_DATA = json.load(file)
        file.close()
        #
        for item in JSON_DATA["coordinates"]:
            #
            x_coordinate = int(item["x"])
            # set dungeon value
            item["dungeon"] = bool(x_coordinate < 0)
        #
        with open("templates/coordinates_up.json", 'w', encoding='utf-8') as file:
            json.dump(JSON_DATA, file, ensure_ascii=False, indent=4)
            print('Config saved')
            file.close()
        #
except (IOError, FileNotFoundError, RuntimeError, TypeError, NameError, IndexError):
    print('No config file found. Error: ' + str(traceback.print_exc()))
