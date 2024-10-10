# graphics_display.py
# ------------------
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


from contest.graphics_utils import *
import math, time
from contest.game import Directions

###########################
#  GRAPHICS DISPLAY CODE  #
###########################

# Most code by Dan Klein and John Denero written or rewritten for cs188, UC Berkeley.
# Some code from a Pacman implementation by LiveWires, and used / modified with permission.

DEFAULT_GRID_SIZE = 30.0
INFO_PANE_HEIGHT = 35
BACKGROUND_COLOR = format_color(0, 0, 0)
WALL_COLOR = format_color(0.0 / 255.0, 51.0 / 255.0, 255.0 / 255.0)
INFO_PANE_COLOR = format_color(.4, .4, 0)
SCORE_COLOR = format_color(.9, .9, .9)
PACMAN_OUTLINE_WIDTH = 2
PACMAN_CAPTURE_OUTLINE_WIDTH = 4

GHOST_COLORS = [format_color(.9, 0, 0), format_color(0, .3, .9), format_color(.98, .41, .07), format_color(.1, .75, .7),
                format_color(1.0, 0.6, 0.0), format_color(.4, 0.13, 0.91)]

TEAM_COLORS = GHOST_COLORS[:2]

GHOST_SHAPE = [
    (0, 0.3),
    (0.25, 0.75),
    (0.5, 0.3),
    (0.75, 0.75),
    (0.75, -0.5),
    (0.5, -0.75),
    (-0.5, -0.75),
    (-0.75, -0.5),
    (-0.75, 0.75),
    (-0.5, 0.3),
    (-0.25, 0.75)
]
GHOST_SIZE = 0.65
SCARED_COLOR = format_color(1, 1, 1)

# GHOST_VEC_COLORS = map(color_to_vector, GHOST_COLORS)
GHOST_VEC_COLORS = [color_to_vector(c) for c in GHOST_COLORS]

PACMAN_COLOR = format_color(255.0 / 255.0, 255.0 / 255.0, 61.0 / 255)
PACMAN_SCALE = 0.5
# pacman_speed = 0.25

# Food
FOOD_COLOR = format_color(1, 1, 1)
FOOD_SIZE = 0.1

# Laser
LASER_COLOR = format_color(1, 0, 0)
LASER_SIZE = 0.02

# Capsule graphics
CAPSULE_COLOR = format_color(1, 1, 1)
CAPSULE_SIZE = 0.25

# Drawing walls
WALL_RADIUS = 0.15


class InfoPane:
    def __init__(self, layout, grid_size):
        self.team_text = None
        self.ghost_distance_text = None
        self.score_text = None
        self.gridSize = grid_size
        self.width = layout.width * grid_size
        self.base = (layout.height + 1) * grid_size
        self.height = INFO_PANE_HEIGHT
        self.fontSize = 24
        self.text_color = PACMAN_COLOR
        self.draw_pane()

    def to_screen(self, pos, y=None):
        """
          Translates a point relative from the bottom left of the info pane.
        """
        if y is None:
            x, y = pos
        else:
            x = pos

        x = self.gridSize + x  # Margin
        y = self.base + y
        return x, y

    def draw_pane(self):
        self.score_text = create_text(self.to_screen(0, 0), self.text_color, "SCORE:    0", "Times", self.fontSize,
                                      "bold")

    def initialize_ghost_distances(self, distances):
        self.ghost_distance_text = []

        size = 20
        if self.width < 240:
            size = 12
        if self.width < 160:
            size = 10

        for i, d in enumerate(distances):
            t = create_text(self.to_screen(self.width / 2 + self.width / 8 * i, 0), GHOST_COLORS[i + 1], d, "Times",
                            size, "bold")
            self.ghost_distance_text.append(t)

    def update_score(self, score):
        change_text(self.score_text, "SCORE: % 4d" % score)

    def set_team(self, is_blue):
        text = "RED TEAM"
        if is_blue: text = "BLUE TEAM"
        self.team_text = create_text(self.to_screen(300, 0), self.text_color, text, "Times", self.fontSize, "bold")

    def update_ghost_distances(self, distances):
        if len(distances) == 0: return
        if 'ghost_distance_text' not in dir(self):
            self.initialize_ghost_distances(distances)
        else:
            for i, d in enumerate(distances):
                change_text(self.ghost_distance_text[i], d)

    def draw_ghost(self):
        pass

    def draw_pacman(self):
        pass

    def draw_warning(self):
        pass

    def clear_icon(self):
        pass

    def update_message(self, message):
        pass

    def clear_message(self):
        pass


class PacmanGraphics:
    def __init__(self, zoom=1.0, frame_time=0.0, capture=False):
        self.expanded_cells = None
        self.agent_images = None
        self.capsules = None
        self.previous_state = None
        self.food = None
        self.current_state = None
        self.info_pane = None
        self.width = None
        self.height = None
        self.layout = None
        self.is_blue = None
        self.have_window = 0
        self.current_ghost_images = {}
        self.pacman_image = None
        self.zoom = zoom
        self.grid_size = DEFAULT_GRID_SIZE * zoom
        self.capture = capture
        self.frame_time = frame_time

    @staticmethod
    def check_null_display():
        return False

    def initialize(self, state, is_blue=False):
        self.is_blue = is_blue
        self.start_graphics(state)

        # self.drawDistributions(state)
        self.distribution_images = None  # Initialized lazily
        self.draw_static_objects(state)
        self.draw_agent_objects(state)

        # Information
        self.previous_state = state

    def start_graphics(self, state):
        self.layout = state.layout
        layout = self.layout
        self.width = layout.width
        self.height = layout.height
        self.make_window(self.width, self.height)
        self.info_pane = InfoPane(layout, self.grid_size)
        self.current_state = layout

    def draw_distributions(self, state):
        walls = state.layout.walls
        dist = []
        for x in range(walls.width):
            dist_x = []
            dist.append(dist_x)
            for y in range(walls.height):
                (screen_x, screen_y) = self.to_screen((x, y))
                block = square((screen_x, screen_y),
                               0.5 * self.grid_size,
                               color=BACKGROUND_COLOR,
                               filled=1, behind=2)
                dist_x.append(block)
        self.distribution_images = dist

    def draw_static_objects(self, state):
        layout = self.layout
        self.draw_walls(layout.walls)
        self.food = self.draw_food(layout.food)
        self.capsules = self.draw_capsules(layout.capsules)
        refresh()

    def draw_agent_objects(self, state):
        self.agent_images = []  # (agent_state, image)
        for index, agent in enumerate(state.agent_states):
            if agent.is_pacman:
                agent_image = self.draw_pacman(agent, index)
                self.agent_images.append((agent, agent_image))
            else:
                agent_image = self.draw_ghost(agent, index)
                self.agent_images.append((agent, agent_image))
        refresh()

    def swap_images(self, agent_index, new_state):
        """
          Changes an image from a ghost to a pacman or vis versa (for capture)
        """
        prev_state, prev_image = self.agent_images[agent_index]
        for item in prev_image: remove_from_screen(item)
        if new_state.is_pacman:
            agent_image = self.draw_pacman(new_state, agent_index)
            self.agent_images[agent_index] = (new_state, agent_image)
        else:
            agent_image = self.draw_ghost(new_state, agent_index)
            self.agent_images[agent_index] = (new_state, agent_image)
        refresh()

    def update(self, new_state):
        agent_index = new_state._agent_moved
        agent_state = new_state.agent_states[agent_index]

        if self.agent_images[agent_index][0].is_pacman != agent_state.is_pacman:
            self.swap_images(agent_index, agent_state)
        prev_state, prev_image = self.agent_images[agent_index]
        if agent_state.is_pacman:
            self.animate_pacman(agent_state, prev_state, prev_image)
        else:
            self.move_ghost(agent_state, agent_index, prev_state, prev_image)
        self.agent_images[agent_index] = (agent_state, prev_image)

        if new_state._food_eaten is not None:
            self.remove_food(new_state._food_eaten, self.food)
        if new_state._capsule_eaten is not None:
            self.remove_capsule(new_state._capsule_eaten, self.capsules)
        self.info_pane.update_score(new_state.score)
        if 'ghost_distances' in dir(new_state):
            self.info_pane.update_ghost_distances(new_state.ghost_distances)

    def make_window(self, width, height):
        grid_width = (width - 1) * self.grid_size
        grid_height = (height - 1) * self.grid_size
        screen_width = 2 * self.grid_size + grid_width
        screen_height = 2 * self.grid_size + grid_height + INFO_PANE_HEIGHT

        begin_graphics(screen_width,
                       screen_height,
                       BACKGROUND_COLOR,
                       "CS188 Pacman")

    def draw_pacman(self, pacman, index):
        position = self.get_position(pacman)
        screen_point = self.to_screen(position)
        endpoints = self.get_endpoints(self.get_direction(pacman))

        width = PACMAN_OUTLINE_WIDTH
        outline_color = PACMAN_COLOR
        fill_color = PACMAN_COLOR

        if self.capture:
            outline_color = TEAM_COLORS[index % 2]
            fill_color = GHOST_COLORS[index]
            width = PACMAN_CAPTURE_OUTLINE_WIDTH

        return [circle(screen_point, PACMAN_SCALE * self.grid_size,
                       fill_color=fill_color, outline_color=outline_color,
                       endpoints=endpoints,
                       width=width)]

    @staticmethod
    def get_endpoints(direction, position=(0, 0)):
        x, y = position
        pos = x - int(x) + y - int(y)
        width = 30 + 80 * math.sin(math.pi * pos)

        delta = width / 2
        if direction == 'West':
            endpoints = (180 + delta, 180 - delta)
        elif direction == 'North':
            endpoints = (90 + delta, 90 - delta)
        elif direction == 'South':
            endpoints = (270 + delta, 270 - delta)
        else:
            endpoints = (0 + delta, 0 - delta)
        return endpoints

    def move_pacman(self, position, direction, pacman_image):
        screen_position = self.to_screen(position)
        endpoints = self.get_endpoints(direction, position)
        r = PACMAN_SCALE * self.grid_size
        move_circle(pacman_image[0], screen_position, r, endpoints)
        refresh()

    def animate_pacman(self, pacman, prev_pacman, pacman_image):
        if self.frame_time < 0:
            print('Press any key to step forward, "q" to play')
            keys = wait_for_keys()
            if 'q' in keys:
                self.frame_time = 0.1
        if self.frame_time > 0.01 or self.frame_time < 0:
            start = time.time()
            fx, fy = self.get_position(prev_pacman)
            px, py = self.get_position(pacman)
            frames = 4.0
            for i in range(1, int(frames) + 1):
                pos = px * i / frames + fx * (frames - i) / frames, py * i / frames + fy * (frames - i) / frames
                self.move_pacman(pos, self.get_direction(pacman), pacman_image)
                refresh()
                sleep(abs(self.frame_time) / frames)
        else:
            self.move_pacman(self.get_position(pacman), self.get_direction(pacman), pacman_image)
        refresh()

    def get_ghost_color(self, ghost, ghost_index):
        if ghost.scared_timer > 0:
            return SCARED_COLOR
        else:
            return GHOST_COLORS[ghost_index]

    def draw_ghost(self, ghost, agent_index):
        pos = self.get_position(ghost)
        direction = self.get_direction(ghost)
        (screen_x, screen_y) = (self.to_screen(pos))
        coordinates = []
        for (x, y) in GHOST_SHAPE:
            coordinates.append((x * self.grid_size * GHOST_SIZE + screen_x, y * self.grid_size * GHOST_SIZE + screen_y))

        colour = self.get_ghost_color(ghost, agent_index)
        body = polygon(coordinates, colour, filled=1)
        white_color = format_color(1.0, 1.0, 1.0)
        black_color = format_color(0.0, 0.0, 0.0)

        dx = 0
        dy = 0
        if direction == 'North':
            dy = -0.2
        if direction == 'South':
            dy = 0.2
        if direction == 'East':
            dx = 0.2
        if direction == 'West':
            dx = -0.2
        left_eye = circle((screen_x + self.grid_size * GHOST_SIZE * (-0.3 + dx / 1.5),
                           screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy / 1.5)),
                          self.grid_size * GHOST_SIZE * 0.2, white_color, white_color)
        right_eye = circle((screen_x + self.grid_size * GHOST_SIZE * (0.3 + dx / 1.5),
                            screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy / 1.5)),
                           self.grid_size * GHOST_SIZE * 0.2, white_color, white_color)
        left_pupil = circle((screen_x + self.grid_size * GHOST_SIZE * (-0.3 + dx),
                             screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy)),
                            self.grid_size * GHOST_SIZE * 0.08, black_color, black_color)
        right_pupil = circle((screen_x + self.grid_size * GHOST_SIZE * (0.3 + dx),
                              screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy)),
                             self.grid_size * GHOST_SIZE * 0.08, black_color, black_color)
        ghost_image_parts = [body, left_eye, right_eye, left_pupil, right_pupil]

        return ghost_image_parts

    def move_eyes(self, pos, direction, eyes):
        (screen_x, screen_y) = (self.to_screen(pos))
        dx = 0
        dy = 0
        if direction == 'North':
            dy = -0.2
        if direction == 'South':
            dy = 0.2
        if direction == 'East':
            dx = 0.2
        if direction == 'West':
            dx = -0.2
        move_circle(eyes[0], (screen_x + self.grid_size * GHOST_SIZE * (-0.3 + dx / 1.5),
                              screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy / 1.5)),
                    self.grid_size * GHOST_SIZE * 0.2)
        move_circle(eyes[1], (screen_x + self.grid_size * GHOST_SIZE * (0.3 + dx / 1.5),
                              screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy / 1.5)),
                    self.grid_size * GHOST_SIZE * 0.2)
        move_circle(eyes[2], (screen_x + self.grid_size * GHOST_SIZE * (-0.3 + dx),
                              screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy)),
                    self.grid_size * GHOST_SIZE * 0.08)
        move_circle(eyes[3], (screen_x + self.grid_size * GHOST_SIZE * (0.3 + dx),
                              screen_y - self.grid_size * GHOST_SIZE * (0.3 - dy)),
                    self.grid_size * GHOST_SIZE * 0.08)

    def move_ghost(self, ghost, ghost_index, prev_ghost, ghost_image_parts):
        old_x, old_y = self.to_screen(self.get_position(prev_ghost))
        new_x, new_y = self.to_screen(self.get_position(ghost))
        delta = new_x - old_x, new_y - old_y

        for ghostImagePart in ghost_image_parts:
            move_by(ghostImagePart, delta)
        refresh()

        if ghost.scared_timer > 0:
            color = SCARED_COLOR
        else:
            color = GHOST_COLORS[ghost_index]
        edit(ghost_image_parts[0], ('fill', color), ('outline', color))
        self.move_eyes(self.get_position(ghost), self.get_direction(ghost), ghost_image_parts[-4:])
        refresh()

    def get_position(self, agent_state):
        if agent_state.configuration is None: return -1000, -1000
        return agent_state.get_position()

    @staticmethod
    def get_direction(agent_state):
        if agent_state.configuration is None: return Directions.STOP
        return agent_state.configuration.get_direction()

    @staticmethod
    def finish():
        end_graphics()

    def to_screen(self, point):
        (x, y) = point
        # y = self.height - y
        x = (x + 1) * self.grid_size
        y = (self.height - y) * self.grid_size
        return x, y

    # Fixes some TK issue with off-center circles
    def to_screen2(self, point):
        (x, y) = point
        # y = self.height - y
        x = (x + 1) * self.grid_size
        y = (self.height - y) * self.grid_size
        return x, y

    def draw_walls(self, wall_matrix):
        wall_color = WALL_COLOR
        for xNum, x in enumerate(wall_matrix):
            if self.capture and (xNum * 2) < wall_matrix.width: wall_color = TEAM_COLORS[0]
            if self.capture and (xNum * 2) >= wall_matrix.width: wall_color = TEAM_COLORS[1]

            for yNum, cell in enumerate(x):
                if cell:  # There's a wall here
                    pos = (xNum, yNum)
                    screen = self.to_screen(pos)
                    screen2 = self.to_screen2(pos)

                    # draw each quadrant of the square based on adjacent walls
                    w_is_wall = self.is_wall(xNum - 1, yNum, wall_matrix)
                    e_is_wall = self.is_wall(xNum + 1, yNum, wall_matrix)
                    n_is_wall = self.is_wall(xNum, yNum + 1, wall_matrix)
                    s_is_wall = self.is_wall(xNum, yNum - 1, wall_matrix)
                    nw_is_wall = self.is_wall(xNum - 1, yNum + 1, wall_matrix)
                    sw_is_wall = self.is_wall(xNum - 1, yNum - 1, wall_matrix)
                    ne_is_wall = self.is_wall(xNum + 1, yNum + 1, wall_matrix)
                    se_is_wall = self.is_wall(xNum + 1, yNum - 1, wall_matrix)

                    # NE quadrant
                    if (not n_is_wall) and (not e_is_wall):
                        # inner circle
                        circle(screen2, WALL_RADIUS * self.grid_size, wall_color, wall_color, (0, 91), 'arc')
                    if n_is_wall and (not e_is_wall):
                        # vertical line
                        line(add(screen, (self.grid_size * WALL_RADIUS, 0)),
                             add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * (-0.5) - 1)), wall_color)
                    if (not n_is_wall) and e_is_wall:
                        # horizontal line
                        line(add(screen, (0, self.grid_size * (-1) * WALL_RADIUS)),
                             add(screen, (self.grid_size * 0.5 + 1, self.grid_size * (-1) * WALL_RADIUS)), wall_color)
                    if n_is_wall and e_is_wall and (not ne_is_wall):
                        # outer circle
                        circle(add(screen2, (self.grid_size * 2 * WALL_RADIUS, self.grid_size * (-2) * WALL_RADIUS)),
                               WALL_RADIUS * self.grid_size - 1, wall_color, wall_color, (180, 271), 'arc')
                        line(add(screen, (self.grid_size * 2 * WALL_RADIUS - 1, self.grid_size * (-1) * WALL_RADIUS)),
                             add(screen, (self.grid_size * 0.5 + 1, self.grid_size * (-1) * WALL_RADIUS)), wall_color)
                        line(add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * (-2) * WALL_RADIUS + 1)),
                             add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * (-0.5))), wall_color)

                    # NW quadrant
                    if (not n_is_wall) and (not w_is_wall):
                        # inner circle
                        circle(screen2, WALL_RADIUS * self.grid_size, wall_color, wall_color, (90, 181), 'arc')
                    if n_is_wall and (not w_is_wall):
                        # vertical line
                        line(add(screen, (self.grid_size * (-1) * WALL_RADIUS, 0)),
                             add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size*(-0.5) - 1)), wall_color)
                    if (not n_is_wall) and w_is_wall:
                        # horizontal line
                        line(add(screen, (0, self.grid_size * (-1) * WALL_RADIUS)),
                             add(screen, (self.grid_size * (-0.5) - 1, self.grid_size * (-1)*WALL_RADIUS)), wall_color)
                    if n_is_wall and w_is_wall and (not nw_is_wall):
                        # outer circle
                        circle(add(screen2, (self.grid_size * (-2) * WALL_RADIUS, self.grid_size * (-2)*WALL_RADIUS)),
                               WALL_RADIUS * self.grid_size - 1, wall_color, wall_color, (270, 361), 'arc')
                        line(add(screen, (self.grid_size * (-2) * WALL_RADIUS + 1, self.grid_size * (-1)*WALL_RADIUS)),
                             add(screen, (self.grid_size * (-0.5), self.grid_size * (-1) * WALL_RADIUS)), wall_color)
                        line(add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size * (-2)*WALL_RADIUS + 1)),
                             add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size * (-0.5))), wall_color)

                    # SE quadrant
                    if (not s_is_wall) and (not e_is_wall):
                        # inner circle
                        circle(screen2, WALL_RADIUS * self.grid_size, wall_color, wall_color, (270, 361), 'arc')
                    if s_is_wall and (not e_is_wall):
                        # vertical line
                        line(add(screen, (self.grid_size * WALL_RADIUS, 0)),
                             add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * 0.5 + 1)), wall_color)
                    if (not s_is_wall) and e_is_wall:
                        # horizontal line
                        line(add(screen, (0, self.grid_size * 1 * WALL_RADIUS)),
                             add(screen, (self.grid_size * 0.5 + 1, self.grid_size * 1 * WALL_RADIUS)), wall_color)
                    if s_is_wall and e_is_wall and (not se_is_wall):
                        # outer circle
                        circle(add(screen2, (self.grid_size * 2 * WALL_RADIUS, self.grid_size * 2 * WALL_RADIUS)),
                               WALL_RADIUS * self.grid_size - 1, wall_color, wall_color, (90, 181), 'arc')
                        line(add(screen, (self.grid_size * 2 * WALL_RADIUS - 1, self.grid_size * 1 * WALL_RADIUS)),
                             add(screen, (self.grid_size * 0.5, self.grid_size * 1 * WALL_RADIUS)), wall_color)
                        line(add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * 2 * WALL_RADIUS - 1)),
                             add(screen, (self.grid_size * WALL_RADIUS, self.grid_size * 0.5)), wall_color)

                    # SW quadrant
                    if (not s_is_wall) and (not w_is_wall):
                        # inner circle
                        circle(screen2, WALL_RADIUS * self.grid_size, wall_color, wall_color, (180, 271), 'arc')
                    if s_is_wall and (not w_is_wall):
                        # vertical line
                        line(add(screen, (self.grid_size * (-1) * WALL_RADIUS, 0)),
                             add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size * 0.5 + 1)), wall_color)
                    if (not s_is_wall) and w_is_wall:
                        # horizontal line
                        line(add(screen, (0, self.grid_size * 1 * WALL_RADIUS)),
                             add(screen, (self.grid_size * (-0.5) - 1, self.grid_size * 1 * WALL_RADIUS)), wall_color)
                    if s_is_wall and w_is_wall and (not sw_is_wall):
                        # outer circle
                        circle(add(screen2, (self.grid_size * (-2) * WALL_RADIUS, self.grid_size * 2 * WALL_RADIUS)),
                               WALL_RADIUS * self.grid_size - 1, wall_color, wall_color, (0, 91), 'arc')
                        line(add(screen, (self.grid_size * (-2) * WALL_RADIUS + 1, self.grid_size * 1 * WALL_RADIUS)),
                             add(screen, (self.grid_size * (-0.5), self.grid_size * 1 * WALL_RADIUS)), wall_color)
                        line(add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size * 2 * WALL_RADIUS - 1)),
                             add(screen, (self.grid_size * (-1) * WALL_RADIUS, self.grid_size * 0.5)), wall_color)

    def is_wall(self, x, y, walls):
        if x < 0 or y < 0:
            return False
        if x >= walls.width or y >= walls.height:
            return False
        return walls[x][y]

    def draw_food(self, food_matrix):
        food_images = []
        color = FOOD_COLOR
        for xNum, x in enumerate(food_matrix):
            if self.capture and (xNum * 2) < food_matrix.width: color = TEAM_COLORS[0]
            if self.capture and (xNum * 2) >= food_matrix.width: color = TEAM_COLORS[1]
            image_row = []
            food_images.append(image_row)
            for yNum, cell in enumerate(x):
                if cell:  # There's food here
                    screen = self.to_screen((xNum, yNum))
                    dot = circle(screen,
                                 FOOD_SIZE * self.grid_size,
                                 outline_color=color, fill_color=color,
                                 width=1)
                    image_row.append(dot)
                else:
                    image_row.append(None)
        return food_images

    def draw_capsules(self, capsules):
        capsule_images = {}
        for capsule in capsules:
            (screen_x, screen_y) = self.to_screen(capsule)
            dot = circle((screen_x, screen_y),
                         CAPSULE_SIZE * self.grid_size,
                         outline_color=CAPSULE_COLOR,
                         fill_color=CAPSULE_COLOR,
                         width=1)
            capsule_images[capsule] = dot
        return capsule_images

    def remove_food(self, cell, food_images):
        x, y = cell
        remove_from_screen(food_images[x][y])

    def remove_capsule(self, cell, capsule_images):
        x, y = cell
        remove_from_screen(capsule_images[(x, y)])

    def draw_expanded_cells(self, cells):
        """
        Draws an overlay of expanded grid positions for search agents
        """
        n = float(len(cells))
        base_color = [1.0, 0.0, 0.0]
        self.clear_expanded_cells()
        self.expanded_cells = []
        for k, cell in enumerate(cells):
            screen_pos = self.to_screen(cell)
            cell_color = format_color(*[(n - k) * c * .5 / n + .25 for c in base_color])
            block = square(screen_pos, 0.5 * self.grid_size, color=cell_color, filled=1, behind=2)
            self.expanded_cells.append(block)
            if self.frame_time < 0:
                refresh()

    def clear_expanded_cells(self):
        if 'expanded_cells' in dir(self) and len(self.expanded_cells) > 0:
            for cell in self.expanded_cells:
                remove_from_screen(cell)

    def update_distributions(self, distributions):
        """Draws an agent's belief distributions"""
        # copy all distributions so we don't change their state
        distributions = map(lambda x: x.copy(), distributions)
        if self.distribution_images is None:
            self.draw_distributions(self.previous_state)
        for x in range(len(self.distribution_images)):
            for y in range(len(self.distribution_images[0])):
                current_image = self.distribution_images[x][y]
                weights = [dist[(x, y)] for dist in distributions]

                if sum(weights) != 0:
                    pass
                # Fog of war
                color = [0.0, 0.0, 0.0]
                colors = GHOST_VEC_COLORS[1:]  # With Pacman
                if self.capture: colors = GHOST_VEC_COLORS
                for weight, gcolor in zip(weights, colors):
                    color = [min(1.0, c + 0.95 * g * weight ** .3) for c, g in zip(color, gcolor)]
                change_color(current_image, format_color(*color))
        refresh()


class FirstPersonPacmanGraphics(PacmanGraphics):
    def __init__(self, zoom=1.0, show_ghosts=True, capture=False, frame_time=0):
        PacmanGraphics.__init__(self, zoom=zoom, frame_time=frame_time, capture=capture)
        self.showGhosts = show_ghosts
        self.capture = capture

    def initialize(self, state, is_blue=False):

        self.is_blue = is_blue
        PacmanGraphics.start_graphics(self, state)
        # Initialize distribution images
        # walls = state.layout.walls
        # dist = []
        self.layout = state.layout

        # Draw the rest
        self.distribution_images = None  # initialize lazily
        self.draw_static_objects(state)
        self.draw_agent_objects(state)

        # Information
        self.previous_state = state

    def look_ahead(self, config, state):
        if config.get_direction() == 'Stop':
            return
        else:
            pass
            # Draw relevant ghosts
            all_ghosts = state.get_ghost_states()
            visible_ghosts = state.getVisibleGhosts()
            for i, ghost in enumerate(all_ghosts):
                if ghost in visible_ghosts:
                    self.draw_ghost(ghost, i)
                else:
                    self.current_ghost_images[i] = None

    def get_ghost_color(self, ghost, ghost_index):
        return GHOST_COLORS[ghost_index]

    def get_position(self, ghost_state):
        if not self.showGhosts and not ghost_state.is_pacman and ghost_state.get_position()[1] > 1:
            return -1000, -1000
        else:
            return PacmanGraphics.get_position(self, ghost_state)


def add(x, y):
    return x[0] + y[0], x[1] + y[1]


# Saving graphical output
# -----------------------
# Note: to make an animated gif from this postscript output, try the command:
# convert -delay 7 -loop 1 -compress lzw -layers optimize frame* out.gif
# convert is part of imagemagick (freeware)

SAVE_POSTSCRIPT = False
POSTSCRIPT_OUTPUT_DIR = 'frames'
FRAME_NUMBER = 0
import os


def save_frame():
    """Saves the current graphical output as a postscript file"""
    global SAVE_POSTSCRIPT, FRAME_NUMBER, POSTSCRIPT_OUTPUT_DIR
    if not SAVE_POSTSCRIPT: return
    if not os.path.exists(POSTSCRIPT_OUTPUT_DIR): os.mkdir(POSTSCRIPT_OUTPUT_DIR)
    name = os.path.join(POSTSCRIPT_OUTPUT_DIR, 'frame_%08d.ps' % FRAME_NUMBER)
    FRAME_NUMBER += 1
    write_postscript(name)  # writes the current canvas
