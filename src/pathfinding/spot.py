"""
Module for navigation support classes.
"""
import config


class Spot:
    """Class for navigaton handling"""

    def __init__(self, x, y):
        self.x_coord = int(x)
        self.y_coord = int(y)
        self.neighbors = []

    def get_neighbors(self):
        """Returns neighboring spots"""
        return self.neighbors

    def get_pos(self):
        """Returns position"""
        return self.x_coord, self.y_coord

    def to_string(self):
        """Returns string of the spot coordinates"""
        return f"{self.x_coord}|{self.y_coord}"

    def update_neighbors(self, spots):
        """Updates neighbor spots"""
        self.neighbors = []
        # RIGHT
        go_right = str(self.x_coord + 1) + "|" + str(self.y_coord)
        if (
            go_right in config.COORD_DATA
            and config.COORD_DATA[go_right]["cango"]
            and config.COORD_DATA[go_right]["avoid"] == 0
        ):
            spot = spots[go_right]
            self.neighbors.append(spot)
        # RIGHT UP
        go_right_up = str(self.x_coord + 1) + "|" + str(self.y_coord - 1)
        if (
            go_right_up in config.COORD_DATA
            and config.COORD_DATA[go_right_up]["cango"]
            and config.COORD_DATA[go_right_up]["avoid"] == 0
        ):
            spot = spots[go_right_up]
            self.neighbors.append(spot)
        # RIGHT DOWN
        go_right_down = str(self.x_coord + 1) + "|" + str(self.y_coord + 1)
        if (
            go_right_down in config.COORD_DATA
            and config.COORD_DATA[go_right_down]["cango"]
            and config.COORD_DATA[go_right_down]["avoid"] == 0
        ):
            spot = spots[go_right_down]
            self.neighbors.append(spot)
        # LEFT
        go_left = str(self.x_coord - 1) + "|" + str(self.y_coord)
        if (
            go_left in config.COORD_DATA
            and config.COORD_DATA[go_left]["cango"]
            and config.COORD_DATA[go_left]["avoid"] == 0
        ):
            spot = spots[go_left]
            self.neighbors.append(spot)
        # LEFT UP
        left_up = str(self.x_coord - 1) + "|" + str(self.y_coord - 1)
        if (
            left_up in config.COORD_DATA
            and config.COORD_DATA[left_up]["cango"]
            and config.COORD_DATA[left_up]["avoid"] == 0
        ):
            spot = spots[left_up]
            self.neighbors.append(spot)
        # LEFT DOWN
        go_left_down = str(self.x_coord - 1) + "|" + str(self.y_coord + 1)
        if (
            go_left_down in config.COORD_DATA
            and config.COORD_DATA[go_left_down]["cango"]
            and config.COORD_DATA[go_left_down]["avoid"] == 0
        ):
            spot = spots[go_left_down]
            self.neighbors.append(spot)
        # DOWN
        go_down = str(self.x_coord) + "|" + str(self.y_coord + 1)
        if (
            go_down in config.COORD_DATA
            and config.COORD_DATA[go_down]["cango"]
            and config.COORD_DATA[go_down]["avoid"] == 0
        ):
            spot = spots[go_down]
            self.neighbors.append(spot)
        # UP
        go_up = str(self.x_coord) + "|" + str(self.y_coord - 1)
        if (
            go_up in config.COORD_DATA
            and config.COORD_DATA[go_up]["cango"]
            and config.COORD_DATA[go_up]["avoid"] == 0
        ):
            spot = spots[go_up]
            self.neighbors.append(spot)
