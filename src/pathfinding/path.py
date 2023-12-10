"""
Module handles path creation based on A* algorithm
"""
import time
import traceback
from queue import PriorityQueue

import botrax_logger
import config
from pathfinding.spot import Spot


def __h(pos1, pos2):
    x_coord_1, y_coord_1 = pos1
    x_coord_2, y_coord_2 = pos2
    return dist(x_coord_1,y_coord_1,x_coord_2,y_coord_2)

def dist(x1,y1,x2,y2):
    return ((x2-x1)**2 + (y2-y1)**2)**0.5

def __algorithm(spots, start, end):
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = {}
    g_score = {spot[1]: float("inf") for spot in spots.items()}
    g_score[start] = 0
    f_score = {spot[1]: float("inf") for spot in spots.items()}
    f_score[start] = __h(start.get_pos(), end.get_pos())
    open_set_hash = {start}
    #
    while not open_set.empty():
        #
        current = open_set.get()[2]
        open_set_hash.remove(current)
        #
        if current == end:
            #
            path = []
            while current in came_from:
                current = came_from[current]
                path.append(current)
            #
            return path

        for neighbor in current.get_neighbors():
            #
            temp_g_score = g_score[current] + 1
            g_score_neighbor = g_score[neighbor]
            #
            if temp_g_score < g_score_neighbor:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + __h(
                    neighbor.get_pos(), end.get_pos()
                )
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
        #
    return None


def get_path(start, end):
    """Creates a path from start to end"""
    # init variables
    final_path = []
    result = None
    start_spot = None
    end_spot = None
    spots = {}
    # get start time of path calculation
    then = int(time.time())
    # check all neighbors
    try:
        # debug output
        botrax_logger.DEBUG_LOGGER.debug("Starting path creation")
        #
        for item in config.COORD_DATA.items():
            # create a spot instance for current position
            current_spot = Spot(item[1]["x"], item[1]["y"])
            #
            if item[0] == start:
                start_spot = current_spot
            if item[0] == end:
                end_spot = current_spot
            #
            spots[item[0]] = current_spot
        #
        if not start_spot or not end_spot:
            return final_path
        # debug output
        botrax_logger.DEBUG_LOGGER.debug(
            "Spot List creation took %f seconds", int(time.time() - then)
        )
        then = int(time.time())
        #
        for spot in spots.items():
            # update its neighbors
            spot[1].update_neighbors(spots)
        # debug output
        botrax_logger.DEBUG_LOGGER.debug(
            "Neighbor creation took %f seconds", int(time.time() - then)
        )
        then = int(time.time())
        # create the path
        result = __algorithm(spots, start_spot, end_spot)
        # debug output
        botrax_logger.DEBUG_LOGGER.debug(
            "Path creation took %f seconds", int(time.time() - then)
        )
    except (IOError, RuntimeError, TypeError, NameError, KeyError):
        botrax_logger.DEBUG_LOGGER.warning(traceback.print_exc())
    # check for result that has been generated
    if result:
        # reverse the path
        final_path = []
        #
        for step in result:
            final_path.insert(0, step)
        # remove start step
        final_path.pop(0)
        # add end to the path list
        final_path.append(end_spot)
    #
    botrax_logger.DEBUG_LOGGER.debug(
        "Path calculation took %f seconds", int(time.time() - then)
    )
    #
    return final_path
