# distance_calculator.py
# ---------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


"""
This file contains a Distancer object which computes and
caches the shortest path between any two points in the maze.

Example:
distancer = Distancer(game_state.data.layout)
distancer.get_distance( (1,1), (10,10) )
"""

import sys


class Distancer:
    def __init__(self, layout, default=10000):
        """
        Initialize with Distancer(layout).  Changing default is unnecessary.
        """
        self._distances = None
        self.default = default
        self.dc = DistanceCalculator(layout, self, default)

    def get_maze_distances(self):
        self.dc.run()

    def get_distance(self, pos1, pos2):
        """
        The getDistance function is the only one you'll need after you create the object.
        """
        if self._distances is None:
            return manhattan_distance(pos1, pos2)
        if is_int(pos1) and is_int(pos2):
            return self.get_distance_on_grid(pos1, pos2)
        pos1_grids = get_grids_2D(pos1)
        pos2_grids = get_grids_2D(pos2)
        best_distance = self.default
        for pos1_snap, snap1_distance in pos1_grids:
            for pos2_snap, snap2_distance in pos2_grids:
                grid_distance = self.get_distance_on_grid(pos1_snap, pos2_snap)
                distance = grid_distance + snap1_distance + snap2_distance
                if best_distance > distance:
                    best_distance = distance
        return best_distance

    def get_distance_on_grid(self, pos1, pos2):
        key = (pos1, pos2)
        if key in self._distances:
            return self._distances[key]
        else:
            raise Exception("Positions not in grid: " + str(key))

    def is_ready_for_maze_distance(self):
        return self._distances is not None


def manhattan_distance(x, y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


def is_int(pos):
    x, y = pos
    return (x == int(x)) and (y == int(y))


def get_grids_2D(pos):
    grids = []
    for x, x_distance in get_grids_1D(pos[0]):
        for y, yDistance in get_grids_1D(pos[1]):
            grids.append(((x, y), x_distance + yDistance))
    return grids


def get_grids_1D(x):
    int_x = int(x)
    if x == int(x):
        return [(x, 0)]
    return [(int_x, x - int_x), (int_x + 1, int_x + 1 - x)]


##########################################
# MACHINERY FOR COMPUTING MAZE DISTANCES #
##########################################

distanceMap = {}


class DistanceCalculator:
    def __init__(self, layout, distancer, default=10000):
        self.layout = layout
        self.distancer = distancer
        self.default = default

    def run(self):
        global distanceMap

        if self.layout.walls not in distanceMap:
            distances = compute_distances(self.layout)
            distanceMap[self.layout.walls] = distances
        else:
            distances = distanceMap[self.layout.walls]

        self.distancer._distances = distances


def compute_distances(layout):
    """Runs UCS to all other positions from each position"""
    distances = {}
    all_nodes = layout.walls.as_list(False)
    for source in all_nodes:
        dist = {}
        closed = {}
        for node in all_nodes:
            dist[node] = sys.maxsize
        import contest.util as util
        queue = util.PriorityQueue()
        queue.push(source, 0)
        dist[source] = 0
        while not queue.is_empty():
            node = queue.pop()
            if node in closed:
                continue
            closed[node] = True
            node_dist = dist[node]
            adjacent = []
            x, y = node
            if not layout.is_wall((x, y + 1)):
                adjacent.append((x, y + 1))
            if not layout.is_wall((x, y - 1)):
                adjacent.append((x, y - 1))
            if not layout.is_wall((x + 1, y)):
                adjacent.append((x + 1, y))
            if not layout.is_wall((x - 1, y)):
                adjacent.append((x - 1, y))
            for other in adjacent:
                if not (other in dist):
                    continue
                old_dist = dist[other]
                new_dist = node_dist + 1
                if new_dist < old_dist:
                    dist[other] = new_dist
                    queue.push(other, new_dist)
        for target in all_nodes:
            distances[(target, source)] = dist[target]
    return distances


def get_distance_on_grid(distances, pos1, pos2):
    key = (pos1, pos2)
    if key in distances:
        return distances[key]
    return 100000
