import json
import traceback

JSON_DATA = None
# read data if not already done
try:
    with open("templates/coordinates_raw.json", "r", encoding="utf8") as coord_file:
        #
        COORD_JSON = json.load(coord_file)
        coord_file.close()
        #
        length = len(COORD_JSON)
        print(f"Starting with {length} items")
        #
        ncg_area = "Terbat"
        ncg_list_before_terbat = ["108|97", "112|97"]
        allowed = ["104|100"]
        coord = ""
        #
        for item in COORD_JSON.items():
            #
            coord = str(item[1]["x"]) + "|" + str(item[1]["y"])
            #
            if (
                ncg_area in item[1]["area"] or coord in ncg_list_before_terbat
            ) and coord not in allowed:
                item[1]["cango"] = False
        #
        length = len(COORD_JSON)
        print(f"List now has {length} items")
        #
        with open("templates/coordinates_up.json", "w", encoding="utf-8") as file:
            json.dump(COORD_JSON, file, ensure_ascii=False, indent=4)
            print("Config saved")
            file.close()
        #
except (IOError, FileNotFoundError, RuntimeError, TypeError, NameError, IndexError):
    print("No config file found. Error: " + str(traceback.print_exc()))
