# layout.py
# ---------
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


from contest.util import manhattan_distance
from contest.game import Grid
import os
import random
from functools import reduce

VISIBILITY_MATRIX_CACHE = {}


class Layout:
    """
    A Layout manages the static information about the game board.
    """

    def __init__(self, layout_name, layout_text):
        self.layout_name = layout_name
        self.width = len(layout_text[0])
        self.height = len(layout_text)
        self.walls = Grid(self.width, self.height, False)
        self.food = Grid(self.width, self.height, False)
        self.capsules = []
        self.agent_positions = []
        self.num_ghosts = 0
        self.process_layout_text(layout_text)
        self.layout_text = layout_text
        self.total_food = len(self.food.as_list())
        # self.initializeVisibilityMatrix()

    def get_num_ghosts(self):
        return self.num_ghosts

    def initialize_visibility_matrix(self):
        global VISIBILITY_MATRIX_CACHE
        if reduce(str.__add__, self.layout_text) not in VISIBILITY_MATRIX_CACHE:
            from contest.game import Directions
            vecs = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
            dirs = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
            vis = Grid(self.width, self.height,
                       {Directions.NORTH: set(), Directions.SOUTH: set(), Directions.EAST: set(),
                        Directions.WEST: set(), Directions.STOP: set()})
            for x in range(self.width):
                for y in range(self.height):
                    if not self.walls[x][y]:
                        for vec, direction in zip(vecs, dirs):
                            dx, dy = vec
                            next_x, next_y = x + dx, y + dy
                            while (((next_x + next_y) != int(next_x) + int(next_y)) or
                                   not self.walls[int(next_x)][int(next_y)]):
                                vis[x][y][direction].add((next_x, next_y))
                                next_x, next_y = x + dx, y + dy
            self.visibility = vis
            VISIBILITY_MATRIX_CACHE[reduce(str.__add__, self.layout_text)] = vis
        else:
            self.visibility = VISIBILITY_MATRIX_CACHE[reduce(str.__add__, self.layout_text)]

    def is_wall(self, pos):
        x, col = pos
        return self.walls[x][col]

    def get_random_legal_position(self):
        x = random.choice(range(self.width))
        y = random.choice(range(self.height))
        while self.is_wall((x, y)):
            x = random.choice(range(self.width))
            y = random.choice(range(self.height))
        return x, y

    def get_random_corner(self):
        poses = [(1, 1), (1, self.height - 2), (self.width - 2, 1), (self.width - 2, self.height - 2)]
        return random.choice(poses)

    def get_furthest_corner(self, pac_pos):
        poses = [(1, 1), (1, self.height - 2), (self.width - 2, 1), (self.width - 2, self.height - 2)]
        dist, pos = max([(manhattan_distance(p, pac_pos), p) for p in poses])
        return pos

    def is_visible_from(self, ghost_pos, pac_pos, pac_direction):
        row, col = [int(x) for x in pac_pos]
        return ghost_pos in self.visibility[row][col][pac_direction]

    def __str__(self):
        return "\n".join(self.layout_text)

    def deep_copy(self):
        return Layout(layout_name=self.layout_name, layout_text=self.layout_text[:])

    def process_layout_text(self, layout_text):
        """
        Coordinates are flipped from the input format to the (x,y) convention here

        The shape of the maze.  Each character
        represents a different type of object.
         % - Wall
         . - Food
         o - Capsule
         G - Ghost
         P - Pacman
        Other characters are ignored.
        """
        max_y = self.height - 1
        for y in range(self.height):
            for x in range(self.width):
                layout_char = layout_text[max_y - y][x]
                self.process_layout_char(x, y, layout_char)
        self.agent_positions.sort()
        self.agent_positions = [(i == 0, pos) for i, pos in self.agent_positions]

    def process_layout_char(self, x, y, layout_char):
        if layout_char == '%':
            self.walls[x][y] = True
        elif layout_char == '.':
            self.food[x][y] = True
        elif layout_char == 'o':
            self.capsules.append((x, y))
        elif layout_char == 'P':
            self.agent_positions.append((0, (x, y)))
        elif layout_char in ['G']:
            self.agent_positions.append((1, (x, y)))
            self.num_ghosts += 1
        elif layout_char in ['1', '2', '3', '4']:
            self.agent_positions.append((int(layout_char), (x, y)))
            self.num_ghosts += 1


def get_layout(name, back=2):
    if name.endswith('.lay'):
        layout = try_to_load('layouts/' + name)
        if layout is None: layout = try_to_load(name)
    else:
        layout = try_to_load('layouts/' + name + '.lay')
        if layout is None: layout = try_to_load(name + '.lay')
    if layout is None and back >= 0:
        current_dir = os.path.abspath('.')
        os.chdir('..')
        layout = get_layout(name, back - 1)
        os.chdir(current_dir)
    return layout


def try_to_load(fullname):
    if not os.path.exists(fullname): return None
    with open(fullname, 'r') as f:
        return Layout(layout_name=fullname[fullname.rfind('/') + 1:], layout_text=[line.strip() for line in f])
