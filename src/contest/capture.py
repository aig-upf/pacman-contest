# capture.py
# ----------
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


# capture.py
# ----------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

"""
Capture.py holds the logic for Pacman capture the flag.

    (i) Your interface to the pacman world:
            Pacman is a complex environment.  You probably don't want to
            read through all the code we wrote to make the game runs
            correctly.  This section contains the parts of the code
            that you will need to understand in order to complete the
            project.  There is also some code in game.py that you should
            understand.

    (ii)  The hidden secrets of pacman:
            This section contains all the logic code that the pacman
            environment uses to decide who can move where, who dies when
            things collide, etc.  You shouldn't need to read this section
            of code, but you can if you want.

    (iii) Framework to start a game:
            The final section contains the code for reading the command
            you use to set up the game, then starting up a new game, along with
            linking in all the external parts (agent functions, graphics).
            Check this section out to see all the options available to you.

    To play your first game, type 'python capture.py' from the command line.
    The keys are
    P1: 'a', 's', 'd', and 'w' to move
    P2: 'l', ';', ',' and 'p' to move
"""
import importlib.util
import importlib.machinery
import os
import pathlib
import random
import sys
import time
import traceback

import contest.keyboard_agents as keyboard_agents
from contest.game import Actions
from contest.game import GameStateData, Game, Grid, Configuration
from contest.util import nearest_point, manhattan_distance

# DIR_SCRIPT = sys.path[0] + "/src/contest/"
import contest

DIR_SCRIPT = '/'.join(contest.__file__.split('/')[:-1])

# If you change these, you won't affect the server, so you can't cheat
KILL_POINTS = 0
SONAR_NOISE_RANGE = 13  # Must be odd
SONAR_NOISE_VALUES = [i - (SONAR_NOISE_RANGE - 1) / 2 for i in range(SONAR_NOISE_RANGE)]
SIGHT_RANGE = 5  # Manhattan distance
MIN_FOOD = 2
TOTAL_FOOD = 60

DUMP_FOOD_ON_DEATH = True  # if we have the gameplay element that dumps dots on death

SCARED_TIME = 40


def compute_noisy_distance(pos1, pos2):
    return int(manhattan_distance(pos1, pos2) + random.choice(SONAR_NOISE_VALUES))


###################################################
# YOUR INTERFACE TO THE PACMAN WORLD: A GameState #
###################################################

class GameState:
    """
  A GameState specifies the full game state, including the food, capsules,
  agent configurations and score changes.

  GameStates are used by the Game object to capture the actual state of the game and
  can be used by agents to reason about the game.

  Much of the information in a GameState is stored in a GameStateData object.  We
  strongly suggest that you access that data via the accessor methods below rather
  than referring to the GameStateData object directly.
  """

    ####################################################
    # Accessor methods: use these to access state data #
    ####################################################

    def get_legal_actions(self, agent_index=0):
        """Returns the legal actions for the agent specified."""
        return AgentRules.get_legal_actions(self, agent_index)

    def generate_successor(self, agent_index, action):
        """Returns the successor state (a GameState object) after the specified agent takes the action."""
        # Copy current state
        state = GameState(self)

        # Find appropriate rules for the agent
        AgentRules.apply_action(state, action, agent_index)
        AgentRules.check_death(state, agent_index)
        AgentRules.decrement_timer(state.data.agent_states[agent_index])

        # Bookkeeping
        state.data._agent_moved = agent_index
        state.data.score += state.data.score_change
        state.data.timeleft = self.data.timeleft - 1
        return state

    def get_agent_state(self, index):
        return self.data.agent_states[index]

    def get_agent_position(self, index):
        """
        Returns a location tuple if the agent with the given index is observable;
        if the agent is unobservable, returns None.
        """
        agent_state = self.data.agent_states[index]
        ret = agent_state.get_position()
        if ret:
            return tuple(int(x) for x in ret)
        return ret

    def get_num_agents(self):
        return len(self.data.agent_states)

    def get_score(self):
        """Returns a number corresponding to the current score."""
        return self.data.score

    def get_red_food(self):
        """
        Returns a matrix of food that corresponds to the food on the red team's side.
        For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
        red (meaning red is protecting it, blue is trying to eat it).
        """
        return make_half_grid(self.data.food, red=True)

    def get_blue_food(self):
        """
        Returns a matrix of food that corresponds to the food on the blue team's side.
        For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
        blue (meaning blue is protecting it, red is trying to eat it).
        """
        return make_half_grid(self.data.food, red=False)

    def get_red_capsules(self):
        return half_list(self.data.capsules, self.data.food, red=True)

    def get_blue_capsules(self):
        return half_list(self.data.capsules, self.data.food, red=False)

    def get_walls(self):
        """Just like get_food but for walls"""
        return self.data.layout.walls

    def has_food(self, x, y):
        """
        Returns true if the location (x,y) has food, regardless of
        whether it's blue team food or red team food.
        """
        return self.data.food[x][y]

    def has_wall(self, x, y):
        """Returns true if (x,y) has a wall, false otherwise."""
        return self.data.layout.walls[x][y]

    def is_over(self):
        return self.data._win

    def get_red_team_indices(self):
        """Returns a list of agent index numbers for the agents on the red team."""
        return self.red_team[:]

    def get_blue_team_indices(self):
        """Returns a list of the agent index numbers for the agents on the blue team."""
        return self.blue_team[:]

    def is_on_red_team(self, agent_index):
        """Returns true if the agent with the given agent_index is on the red team."""
        return self.teams[agent_index]

    def get_agent_distances(self):
        """Returns a noisy distance to each agent."""
        if 'agent_distances' in dir(self):
            return self.agent_distances
        else:
            return None

    @staticmethod
    def get_distance_prob(true_distance, noisy_distance):
        """Returns the probability of a noisy distance given the true distance"""
        if noisy_distance - true_distance in SONAR_NOISE_VALUES:
            return 1.0 / SONAR_NOISE_RANGE
        else:
            return 0

    def get_initial_agent_position(self, agent_index):
        """Returns the initial position of an agent."""
        return self.data.layout.agent_positions[agent_index][1]

    def get_capsules(self):
        """Returns a list of positions (x,y) of the remaining capsules."""
        return self.data.capsules

    #############################################
    #             Helper methods:               #
    # You shouldn't need to call these directly #
    #############################################

    def __init__(self, prev_state=None):
        """Generates a new state by copying information from its predecessor."""
        if prev_state is not None:  # Initial state
            self.data = GameStateData(prev_state.data)
            self.blue_team = prev_state.blue_team
            self.red_team = prev_state.red_team
            self.data.timeleft = prev_state.data.timeleft

            self.teams = prev_state.teams
            self.agent_distances = prev_state.agent_distances
        else:
            self.data = GameStateData()
            self.agent_distances = []

    def deep_copy(self):
        state = GameState(self)
        state.data = self.data.deep_copy()
        state.data.timeleft = self.data.timeleft

        state.blue_team = self.blue_team[:]
        state.red_team = self.red_team[:]
        state.teams = self.teams[:]
        state.agent_distances = self.agent_distances[:]
        return state

    def make_observation(self, index):
        state = self.deep_copy()

        # Adds the sonar signal
        pos = state.get_agent_position(index)
        n = state.get_num_agents()
        distances = [compute_noisy_distance(pos, state.get_agent_position(i)) for i in range(n)]
        state.agent_distances = distances

        # Remove states of distant opponents
        if index in self.blue_team:
            team = self.blue_team
            other_team = self.red_team
        else:
            other_team = self.blue_team
            team = self.red_team

        for enemy in other_team:
            seen = False
            enemy_pos = state.get_agent_position(enemy)
            for teammate in team:
                if manhattan_distance(enemy_pos, state.get_agent_position(teammate)) <= SIGHT_RANGE:
                    seen = True
            if not seen: state.data.agent_states[enemy].configuration = None
        return state

    def __eq__(self, other):
        """Allows two states to be compared."""
        if other is None: return False
        return self.data == other.data

    def __hash__(self):
        """Allows states to be keys of dictionaries."""
        return int(hash(self.data))

    def __str__(self):
        return str(self.data)

    def initialize(self, layout, num_agents):
        """Creates an initial game state from a layout array (see layout.py)."""
        self.data.initialize(layout, num_agents)
        positions = [a.configuration for a in self.data.agent_states]
        self.blue_team = [i for i, p in enumerate(positions) if not self.is_red(p)]
        self.red_team = [i for i, p in enumerate(positions) if self.is_red(p)]
        self.teams = [self.is_red(p) for p in positions]
        # This is usually 60 (always 60 with random maps)
        # However, if layout map is specified otherwise, it could be less
        global TOTAL_FOOD
        TOTAL_FOOD = layout.total_food

    def is_red(self, config_or_pos):
        width = self.data.layout.width
        if config_or_pos is tuple:
            return config_or_pos[0] < width // 2
        else:
            return config_or_pos.pos[0] < width // 2


def make_half_grid(grid, red):
    halfway = grid.width // 2
    half_grid = Grid(grid.width, grid.height, False)
    if red:
        xrange = range(halfway)
    else:
        xrange = range(halfway, grid.width)

    for y in range(grid.height):
        for x in xrange:
            if grid[x][y]: half_grid[x][y] = True

    return half_grid


def half_list(locations, grid, red):
    halfway = grid.width // 2
    new_list = []
    for x, y in locations:
        if red and x < halfway:
            new_list.append((x, y))
        elif not red and x >= halfway:
            new_list.append((x, y))
    return new_list


############################################################################
#                     THE HIDDEN SECRETS OF PACMAN                         #
#                                                                          #
# You shouldn't need to look through the code in this section of the file. #
############################################################################

COLLISION_TOLERANCE = 0.7  # How close ghosts must be to Pacman to kill


class CaptureRules:
    """
  These game rules manage the control flow of a game, deciding when
  and how the game starts and ends.
  """

    def __init__(self, quiet=False):
        self._init_blue_food = None
        self._init_red_food = None
        self.quiet = quiet

    def new_game(self, layout, agents, display, length, mute_agents, catch_exceptions):
        init_state = GameState()
        init_state.initialize(layout, len(agents))
        starter = random.randint(0, 1)
        print('%s team starts' % ['Red', 'Blue'][starter])
        game = Game(agents, display, self, starting_index=starter, mute_agents=mute_agents,
                    catch_exceptions=catch_exceptions)
        game.state = init_state
        game.length = length
        game.state.data.timeleft = length
        if 'drawCenterLine' in dir(display):
            display.drawCenterLine()
        self._init_blue_food = init_state.get_blue_food().count()
        self._init_red_food = init_state.get_red_food().count()
        return game

    @staticmethod
    def process(state, game):
        """Checks to see whether it is time to end the game."""
        if 'move_history' in dir(game):
            if len(game.move_history) == game.length:
                state.data._win = True

        if state.is_over():
            game.game_over = True
            if not game.rules.quiet:
                red_count = 0
                blue_count = 0
                food_to_win = (TOTAL_FOOD / 2) - MIN_FOOD
                for index in range(state.get_num_agents()):
                    agent_state = state.data.agent_states[index]
                    if index in state.get_red_team_indices():
                        red_count += agent_state.num_returned
                    else:
                        blue_count += agent_state.num_returned

                if blue_count >= food_to_win:  # state.getRedFood().count() == MIN_FOOD:
                    print(f'The Blue team has returned at least {food_to_win} of the opponents\' dots.')
                elif red_count >= food_to_win:  # state.getBlueFood().count() == MIN_FOOD:
                    print(f'The Red team has returned at least {food_to_win} of the opponents\' dots.')
                else:  # if state.getBlueFood().count() > MIN_FOOD and state.getRedFood().count() > MIN_FOOD:
                    print('Time is up.')
                    if state.data.score == 0:
                        print('Tie game!')
                    else:
                        winner = 'Red'
                        if state.data.score < 0: winner = 'Blue'
                        print(f'The {winner} team wins by {abs(state.data.score)} points.')

    def get_progress(self, game):
        blue = 1.0 - (game.state.get_blue_food().count() / float(self._init_blue_food))
        red = 1.0 - (game.state.get_red_food().count() / float(self._init_red_food))
        moves = len(self.move_history) / float(game.length)  # FIXME: self.move never assigned

        # return the most likely progress indicator, clamped to [0, 1]
        return min(max(0.75 * max(red, blue) + 0.25 * moves, 0.0), 1.0)

    @staticmethod
    def agent_crash(game, agent_index):
        if agent_index % 2 == 0:
            print("Red agent crashed", file=sys.stderr)
            game.state.data.score = -1
        else:
            print("Blue agent crashed", file=sys.stderr)
            game.state.data.score = 1

    @staticmethod
    def get_max_total_time():
        return 900  # Move limits should prevent this from ever happening

    @staticmethod
    def get_max_startup_time():
        return 15  # 15 seconds for register_initial_state

    @staticmethod
    def get_move_warning_time():
        return 1  # One second per move

    @staticmethod
    def get_move_timeout():
        return 3  # Three seconds results in instant forfeit

    @staticmethod
    def get_max_time_warnings():
        return 2  # Third violation loses the game


class AgentRules:
    """
    These functions govern how each agent interacts with her environment.
    """

    @staticmethod
    def get_legal_actions(state, agent_index):
        """
        Returns a list of legal actions (which are both possible & allowed)
        """
        agent_state = state.get_agent_state(agent_index)
        conf = agent_state.configuration
        possible_actions = Actions.get_possible_actions(conf, state.data.layout.walls)
        return AgentRules.filter_for_allowed_actions(possible_actions)

    @staticmethod
    def filter_for_allowed_actions(possible_actions):
        return possible_actions

    @staticmethod
    def apply_action(state, action, agent_index):
        """Edits the state to reflect the results of the action."""
        legal = AgentRules.get_legal_actions(state, agent_index)
        if action not in legal:
            raise Exception("Illegal action " + str(action))

        # Update Configuration
        agent_state = state.data.agent_states[agent_index]
        speed = 1.0
        # if agent_state.is_pacman: speed = 0.5
        vector = Actions.direction_to_vector(action, speed)
        old_config = agent_state.configuration
        agent_state.configuration = old_config.generate_successor(vector)

        # Eat
        current_position = agent_state.configuration.get_position()
        nearest = nearest_point(current_position)

        if current_position == nearest:
            is_red = state.is_on_red_team(agent_index)
            # Change agent type
            agent_state.is_pacman = [is_red, state.is_red(agent_state.configuration)].count(True) == 1
            # if he's no longer pacman, he's on his own side, so reset the num carrying timer
            # agent_state.numCarrying *= int(agent_state.is_pacman)
            if agent_state.num_carrying > 0 and not agent_state.is_pacman:
                score = agent_state.num_carrying if is_red else -1 * agent_state.num_carrying
                state.data.score_change += score

                agent_state.num_returned += agent_state.num_carrying
                agent_state.num_carrying = 0

                red_count = 0
                blue_count = 0
                for index in range(state.get_num_agents()):
                    agent = state.data.agent_states[index]
                    if index in state.get_red_team_indices():
                        red_count += agent.num_returned
                    else:
                        blue_count += agent.num_returned
                if red_count >= (TOTAL_FOOD / 2) - MIN_FOOD or blue_count >= (TOTAL_FOOD / 2) - MIN_FOOD:
                    state.data._win = True

        if agent_state.is_pacman and manhattan_distance(nearest, current_position) <= 0.9:
            AgentRules.consume(nearest, state, state.is_on_red_team(agent_index))

    @staticmethod
    def consume(position, state, is_red):
        x, y = position
        # Eat food
        if state.data.food[x][y]:

            # blue case is the default
            team_indices_func = state.get_blue_team_indices
            # score = -1
            if is_red:
                # switch if its red
                # score = 1
                team_indices_func = state.get_red_team_indices

            # go increase the variable for the pacman who ate this
            agents = [state.data.agent_states[agentIndex] for agentIndex in team_indices_func()]
            for agent in agents:
                if agent.get_position() == position:
                    agent.num_carrying += 1
                    break  # the above should only be true for one agent...

            # do all the score and food grid maintenance
            # state.data.scoreChange += score
            state.data.food = state.data.food.copy()
            state.data.food[x][y] = False
            state.data._food_eaten = position
            # if (isRed and state.get_blue_food().count() == MIN_FOOD) or
            # (not isRed and state.get_red_food().count() == MIN_FOOD):
            #  state.data._win = True

        # Eat capsule
        if is_red:
            my_capsules = state.get_blue_capsules()
        else:
            my_capsules = state.get_red_capsules()
        if position in my_capsules:
            state.data.capsules.remove(position)
            state.data._capsule_eaten = position

            # Reset all ghosts' scared timers
            if is_red:
                other_team = state.get_blue_team_indices()
            else:
                other_team = state.get_red_team_indices()
            for index in other_team:
                state.data.agent_states[index].scared_timer = SCARED_TIME

    @staticmethod
    def decrement_timer(state):
        timer = state.scared_timer
        if timer == 1:
            state.configuration.pos = nearest_point(state.configuration.pos)
        state.scared_timer = max(0, timer - 1)

    @staticmethod
    def dump_food_from_death(state, agent_state):
        if not DUMP_FOOD_ON_DEATH:
            # this feature is not turned on
            return

        if not agent_state.is_pacman:
            raise Exception('something is seriously wrong, this agent isn\'t a pacman!')

        # ok so agent_state is this:
        if agent_state.num_carrying == 0:
            return

        # first, score changes!
        # we HACK pack that ugly bug by just determining if its red based on the first position
        # to die...
        dummy_config = Configuration(agent_state.get_position(), 'North')
        is_red = state.is_red(dummy_config)

        # the score increases if red eats dots, so if we are refunding points,
        # the direction should be -1 if the red agent died, which means he dies
        # on the blue side
        # score_direction = (-1) ** (int(is_red) + 1)

        # state.data.scoreChange += scoreDirection * agent_state.numCarrying

        def on_right_side(from_state, from_x, from_y):
            new_dummy_config = Configuration((from_x, from_y), 'North')
            return from_state.is_red(new_dummy_config) == is_red

        # we have food to dump
        # -- expand out in BFS. Check:
        #   - that it's within the limits
        #   - that it's not a wall
        #   - that no other agents are there
        #   - that no power pellets are there
        #   - that it's on the right side of the grid
        def all_good(from_state, from_x, from_y):
            width, height = from_state.data.layout.width, from_state.data.layout.height
            food, walls = from_state.data.food, from_state.data.layout.walls

            # bounds check
            if from_x >= width or from_y >= height or from_x <= 0 or from_y <= 0:
                return False

            if walls[from_x][from_y]:
                return False
            if food[from_x][from_y]:
                return False

            # dots need to be on the side where this agent will be a pacman :P
            if not on_right_side(from_state, from_x, from_y):
                return False

            if (from_x, from_y) in from_state.data.capsules:
                return False

            # loop through agents
            agent_poses = [from_state.get_agent_position(i) for i in range(from_state.get_num_agents())]
            if (from_x, from_y) in agent_poses:
                return False

            return True

        num_to_dump = agent_state.num_carrying
        state.data.food = state.data.food.copy()
        food_added = []

        def gen_successors(from_x, from_y):
            dirs_x = [-1, 0, 1]
            dirs_y = [-1, 0, 1]
            return [(from_x + dx, from_y + dy) for dx in dirs_x for dy in dirs_y]

        # BFS graph search
        position_queue = [agent_state.get_position()]
        seen = set()
        while num_to_dump > 0:
            if not len(position_queue):
                raise Exception('Exhausted BFS! uh oh')
            # pop one off, graph check
            popped = position_queue.pop(0)
            if popped in seen:
                continue
            seen.add(popped)

            x, y = popped[0], popped[1]
            x = int(x)
            y = int(y)
            if all_good(state, x, y):
                state.data.food[x][y] = True
                food_added.append((x, y))
                num_to_dump -= 1

            # generate successors
            position_queue = position_queue + gen_successors(x, y)

        if state.data._food_added is None:
            state.data._food_added = food_added
        else:
            state.data._food_added.extend(food_added)
        # now our agent_state is no longer carrying food
        agent_state.num_carrying = 0
        pass

    @staticmethod
    def check_death(state, agent_index):
        agent_state = state.data.agent_states[agent_index]
        if state.is_on_red_team(agent_index):
            other_team = state.get_blue_team_indices()
        else:
            other_team = state.get_red_team_indices()
        if agent_state.is_pacman:
            for index in other_team:
                other_agent_state = state.data.agent_states[index]
                if other_agent_state.is_pacman: continue
                ghost_position = other_agent_state.get_position()
                if ghost_position is None: continue
                if manhattan_distance(ghost_position, agent_state.get_position()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if other_agent_state.scared_timer <= 0:
                        AgentRules.dump_food_from_death(state, agent_state)

                        score = KILL_POINTS
                        if state.is_on_red_team(agent_index):
                            score = -score
                        state.data.score_change += score
                        agent_state.is_pacman = False
                        agent_state.configuration = agent_state.start
                        agent_state.scared_timer = 0
                    else:
                        score = KILL_POINTS
                        if state.is_on_red_team(agent_index):
                            score = -score
                        state.data.score_change += score
                        other_agent_state.is_pacman = False
                        other_agent_state.configuration = other_agent_state.start
                        other_agent_state.scared_timer = 0
        else:  # Agent is a ghost
            for index in other_team:
                other_agent_state = state.data.agent_states[index]
                if not other_agent_state.is_pacman: continue
                pac_pos = other_agent_state.get_position()
                if pac_pos is None: continue
                if manhattan_distance(pac_pos, agent_state.get_position()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if agent_state.scared_timer <= 0:
                        AgentRules.dump_food_from_death(state, other_agent_state)

                        score = KILL_POINTS
                        if not state.is_on_red_team(agent_index):
                            score = -score
                        state.data.score_change += score
                        other_agent_state.is_pacman = False
                        other_agent_state.configuration = other_agent_state.start
                        other_agent_state.scared_timer = 0
                    else:
                        score = KILL_POINTS
                        if state.is_on_red_team(agent_index):
                            score = -score
                        state.data.score_change += score
                        agent_state.is_pacman = False
                        agent_state.configuration = agent_state.start
                        agent_state.scared_timer = 0

    @staticmethod
    def place_ghost(ghost_state):
        ghost_state.configuration = ghost_state.start


#############################
# FRAMEWORK TO START A GAME #
#############################


def default(input_str):
    return input_str + ' [Default: %default]'


def parse_agent_args(input_str):
    if input_str is None or input_str == '': return {}
    pieces = input_str.split(',')
    opts = {}
    for p in pieces:
        if '=' in p:
            key, val = p.split('=')
        else:
            key, val = p, 1
        opts[key] = val
    return opts


def read_command(argv):
    """Processes the command used to run pacman from the command line."""
    from optparse import OptionParser
    usage_str = """
    USAGE:      python pacman.py <options>
    EXAMPLES:   (1) python capture.py
                    - starts a game with two baseline agents
                (2) python capture.py --keys0
                    - starts a two-player interactive game where the arrow keys control agent 0, and all other agents 
                    are baseline agents
                (3) python capture.py -r baseline_team -b my_team
                    - starts a fully automated game where the red team is a baseline team and blue team is my_team
    """
    parser = OptionParser(usage_str)

    parser.add_option('-r', '--red', help=default('Red team'), default=os.path.join(DIR_SCRIPT, 'baseline_team')),
    parser.add_option('-b', '--blue', help=default('Blue team'), default=os.path.join(DIR_SCRIPT, 'baseline_team')),
    parser.add_option('--red-name', dest="red_name", help=default('Red team name'), default='Red')
    parser.add_option('--blue-name', dest="blue_name", help=default('Blue team name'), default='Blue')
    parser.add_option('--redOpts', dest="red_opts", help=default('Options for red team (e.g. first=keys)'), default='')
    parser.add_option('--blueOpts', dest="blue_opts", help=default('Options for blue team (e.g. first=keys)'),
                      default='')
    parser.add_option('--keys0', help='Make agent 0 (first red player) a keyboard agent', action='store_true',
                      default=False)
    parser.add_option('--keys1', help='Make agent 1 (second red player) a keyboard agent', action='store_true',
                      default=False)
    parser.add_option('--keys2', help='Make agent 2 (first blue player) a keyboard agent', action='store_true',
                      default=False)
    parser.add_option('--keys3', help='Make agent 3 (second blue player) a keyboard agent', action='store_true',
                      default=False)
    parser.add_option('-l', '--layout', dest='layout',
                      help=default('the LAYOUT_FILE from which to load the map layout; use RANDOM for a random maze; '
                                   'use RANDOM<seed> to use a specified random seed, e.g., RANDOM23'),
                      metavar='LAYOUT_FILE', default=os.path.join(DIR_SCRIPT, 'layouts', 'defaultCapture'))
    parser.add_option('-t', '--textgraphics', action='store_true', dest='textgraphics',
                      help='Display output as text only', default=False)

    parser.add_option('-q', '--quiet', action='store_true',
                      help='Display minimal output and no graphics', default=False)

    parser.add_option('-Q', '--super-quiet', action='store_true', dest="super_quiet",
                      help='Same as -q but agent output is also suppressed', default=False)

    parser.add_option('-z', '--zoom', type='float', dest='zoom',
                      help=default('Zoom in the graphics'), default=1)
    parser.add_option('-i', '--time', type='int', dest='time',
                      help=default('TIME limit of a game in moves'), default=1200, metavar='TIME')
    parser.add_option('-n', '--num_games', type='int', dest="num_games", help=default('Number of games to play'),
                      default=1)
    parser.add_option('-f', '--fix_random_seed', dest="fix_random_seed", action='store_true',
                      help='Fixes the random seed to always play the same game', default=False)
    parser.add_option('--setRandomSeed', dest="set_random_seed", type='str',
                      help='Sets the random seed to a the given string')
    parser.add_option('--record', action='store_true',
                      help='Writes game histories to a file (named by the time they were played)', default=False)

    parser.add_option('--record-log', dest="record_log", action='store_true',
                      help='Writes game log  to a file (named by the time they were played)', default=False)
    parser.add_option('--replay', default=None,
                      help='Replays a recorded game file.')
    parser.add_option('--replayq', default=None,
                      help='Replays a recorded game file without display to generate result log.')
    parser.add_option('--delay-step', type='float', dest='delay_step',
                      help=default('Delay step in a play or replay.'), default=0.03)
    parser.add_option('-x', '--num_training', dest='num_training', type='int',
                      help=default('How many episodes are training (suppresses output)'), default=0)
    parser.add_option('-c', '--catch-exceptions', dest='catch_exceptions', action='store_true', default=False,
                      help='Catch exceptions and enforce time limits')
    parser.add_option('-m', '--match-identifier', dest='match_id', type='int', default=0,
                      help='Set the gameplay identifier')
    parser.add_option('-u', '--contest-name', dest='contest_name', type=str, default="default",
                      help="Set the contest name")

    parsed_options, other_junk = parser.parse_args(argv)
    assert len(other_junk) == 0, "Unrecognized options: " + str(other_junk)
    args = dict()

    # Choose a display format
    # if options.pygame:
    #   import pygameDisplay
    #    args['display'] = pygameDisplay.PacmanGraphics()
    if parsed_options.textgraphics:
        import contest.text_display as text_display
        args['display'] = text_display.PacmanGraphics()
    elif parsed_options.quiet or parsed_options.replayq:
        import contest.text_display as text_display
        args['display'] = text_display.NullGraphics()
    elif parsed_options.super_quiet:
        import contest.text_display as text_display
        args['display'] = text_display.NullGraphics()
        args['mute_agents'] = True
    else:
        import contest.capture_graphics_display as capture_graphics_display
        # Hack for agents writing to the display
        capture_graphics_display.FRAME_TIME = 0
        args['display'] = capture_graphics_display.PacmanGraphics(parsed_options.red, parsed_options.red_name,
                                                                  parsed_options.blue,
                                                                  parsed_options.blue_name, parsed_options.zoom, 0,
                                                                  capture=True)
        import __main__
        __main__.__dict__['_display'] = args['display']

    args['red_team_name'] = parsed_options.red_name
    args['blue_team_name'] = parsed_options.blue_name

    # Special case: recorded games don't use the run_games method or args structure
    if parsed_options.replay is not None:
        print(f'Replaying recorded game {parsed_options.replay}.')
        import pickle
        recorded = pickle.load(open(parsed_options.replay, 'rb'), encoding="utf-8")
        recorded['display'] = args['display']
        recorded['delay'] = parsed_options.delay_step
        recorded['red_team_name'] = parsed_options.red
        recorded['blue_team_name'] = parsed_options.blue
        recorded['wait_end'] = False
        replay_game(**recorded)
        sys.exit(0)

    # Special case: recorded games don't use the run_games method or args structure
    if parsed_options.replayq is not None:
        print(f'Replaying recorded game {parsed_options.replay}.')
        import pickle
        recorded = pickle.load(open(parsed_options.replayq, 'rb'), encoding="utf-8")
        recorded['display'] = args['display']
        recorded['delay'] = 0.0
        recorded['red_team_name'] = parsed_options.red
        recorded['blue_team_name'] = parsed_options.blue
        recorded['wait_end'] = False

        replay_game(**recorded)
        sys.exit(0)

    if parsed_options.fix_random_seed:
        random.seed('cs188')

    if parsed_options.set_random_seed:
        random.seed(parsed_options.set_random_seed)

    if parsed_options.record_log:
        sub_folder = f'www/contest_{parsed_options.contest_name}/logs'
        os.makedirs(name=sub_folder, exist_ok=True)
        sys.stdout = open(f'{sub_folder}/match_{parsed_options.match_id}.log', 'w')
        sys.stderr = sys.stdout

    # Choose a pacman agent
    red_args, blue_args = parse_agent_args(parsed_options.red_opts), parse_agent_args(parsed_options.blue_opts)
    if parsed_options.num_training > 0:
        red_args['num_training'] = parsed_options.num_training
        blue_args['num_training'] = parsed_options.num_training
    # no_keyboard = parsed_options.textgraphics or parsed_options.quiet or parsed_options.num_training > 0
    print(f'\nRed team {parsed_options.red} with {red_args}:')
    red_agents = load_agents(True, parsed_options.red, red_args)
    print(f'\nBlue team {parsed_options.blue} with {blue_args}:')
    blue_agents = load_agents(False, parsed_options.blue, blue_args)
    args['agents'] = sum([list(el) for el in zip(red_agents, blue_agents)], [])  # list of agents

    if None in blue_agents or None in red_agents:
        if None in blue_agents:
            print('\nBlue team failed to load!\n')
        if None in red_agents:
            print('\nRed team failed to load!\n')
        raise Exception('No teams found!')

    num_keyboard_agents = 0
    for index, val in enumerate(
            [parsed_options.keys0, parsed_options.keys1, parsed_options.keys2, parsed_options.keys3]):
        if not val: continue
        if num_keyboard_agents == 0:
            agent = keyboard_agents.KeyboardAgent(index)
        elif num_keyboard_agents == 1:
            agent = keyboard_agents.KeyboardAgent2(index)
        else:
            raise Exception('Max of two keyboard agents supported')
        num_keyboard_agents += 1
        args['agents'][index] = agent

    # Choose a layout
    import contest.layout as layout
    layouts = []
    for i in range(parsed_options.num_games):
        if parsed_options.layout == 'RANDOM':
            layout_name, layout_text = random_layout()
            layout_generated = layout.Layout(layout_name=layout_name, layout_text=layout_text.split('\n'))
        elif parsed_options.layout.startswith('RANDOM'):
            seed_chosen = int(parsed_options.layout[6:])
            layout_name, layout_text = random_layout(seed=seed_chosen)
            layout_generated = layout.Layout(layout_name=layout_name, layout_text=layout_text.split('\n'))
        elif parsed_options.layout.lower().find('capture') == -1:
            raise Exception('You must use a capture layout with capture.py')
        else:
            layout_generated = layout.get_layout(parsed_options.layout)
        if layout_generated is None: raise Exception(f"The layout {parsed_options.layout} cannot be found")

        layouts.append(layout_generated)

    args['layouts'] = layouts
    args['length'] = parsed_options.time
    args['num_games'] = parsed_options.num_games
    args['num_training'] = parsed_options.num_training
    args['record'] = parsed_options.record
    args['catch_exceptions'] = parsed_options.catch_exceptions
    args['delay_step'] = parsed_options.delay_step
    args['match_id'] = parsed_options.match_id
    args['contest_name'] = parsed_options.contest_name
    return args


def random_layout(seed=None):
    if not seed:
        seed = random.randint(0, 99999999)
    # layout = 'layouts/random%08dCapture.lay' % seed
    # print 'Generating random layout in %s' % layout
    import contest.maze_generator as maze_generator
    return f'RANDOM{seed}', maze_generator.generate_maze(seed)


def load_agents(is_red, agent_file, cmd_line_args):
    """Calls agent factories and returns lists of agents"""
    try:
        if not agent_file.endswith(".py"):
            agent_file += ".py"

        module_name = pathlib.Path(agent_file).stem
        agent_file = os.path.abspath(agent_file)

        # just in case other files not in the distribution are loaded
        sys.path.append(os.path.split(agent_file)[0])

        print(f"Loading agent team: {agent_file}")

        # SS: new way of loading Python modules - Python 3.4+
        loader = importlib.machinery.SourceFileLoader(module_name, agent_file)
        spec = importlib.util.spec_from_loader(module_name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)  # will be added to sys.modules dict

    except (NameError, ImportError):
        print('Error: The team "' + agent_file + '" could not be loaded! ', file=sys.stderr)
        traceback.print_exc()
        return [None] * 2
    except IOError:
        print('Error: The team "' + agent_file + '" could not be loaded! ', file=sys.stderr)
        traceback.print_exc()
        return [None] * 2

    args = dict()
    args.update(cmd_line_args)  # Add command line args with priority

    print("\tArguments:", args)

    # if textgraphics and factoryClassName.startswith('Keyboard'):
    #   raise Exception('Using the keyboard requires graphics (no text display, quiet or training games)')

    try:
        create_team_func = getattr(module, 'create_team')
    except AttributeError:
        print('Error: The team "' + agent_file + '" could not be loaded! ', file=sys.stderr)
        traceback.print_exc()
        return [None] * 2

    index_addend = 0
    if not is_red:
        index_addend = 1
    indices = [2 * i + index_addend for i in range(2)]
    return create_team_func(indices[0], indices[1], is_red, **args)


def replay_game(layout, agents, actions, display, length, red_team_name, blue_team_name, wait_end=True, delay=1):
    rules = CaptureRules()
    game = rules.new_game(layout, agents, display, length, False, False)
    state = game.state
    display.red_team = red_team_name
    display.blue_team = blue_team_name
    display.initialize(state.data)

    for action in actions:
        # Execute the action
        state = state.generate_successor(*action)
        # Change the display
        display.update(state.data)
        # Allow for game specific conditions (winning, losing, etc.)
        rules.process(state, game)
        time.sleep(delay)

    game.game_over = True
    if not game.rules.quiet:
        red_count = 0
        blue_count = 0
        food_to_win = (TOTAL_FOOD / 2) - MIN_FOOD
        for index in range(state.get_num_agents()):
            agent_state = state.data.agent_states[index]
            if index in state.get_red_team_indices():
                red_count += agent_state.num_returned
            else:
                blue_count += agent_state.num_returned

        if blue_count >= food_to_win:  # state.getRedFood().count() == MIN_FOOD:
            print(f'The Blue team has returned at least {food_to_win} of the opponents\' dots.')
        elif red_count >= food_to_win:  # state.getBlueFood().count() == MIN_FOOD:
            print(f'The Red team has returned at least {food_to_win} of the opponents\' dots.')
        else:  # if state.getBlueFood().count() > MIN_FOOD and state.getRedFood().count() > MIN_FOOD:
            print('Time is up.')
            if state.data.score == 0:
                print('Tie game!')
            else:
                winner = 'Red'
                if state.data.score < 0: winner = 'Blue'
                print(f'The {winner} team wins by {abs(state.data.score)} points.')

    if wait_end is True:
        print("END")
        try:
            input("PRESS ENTER TO CONTINUE")
        except:
            print("END")

    display.finish()


def run_games(layouts, agents, display, length, num_games, record, num_training, red_team_name, blue_team_name,
              contest_name="default", mute_agents=False, catch_exceptions=False, delay_step=0, match_id=0):
    rules = CaptureRules()
    games_list = []

    if num_training > 0:
        print(f'Playing {num_training} training games')

    for i in range(num_games):
        be_quiet = i < num_training
        layout = layouts[i]
        if be_quiet:
            # Suppress output and graphics
            import contest.text_display as text_display
            game_display = text_display.NullGraphics()
            rules.quiet = True
        else:
            game_display = display
            rules.quiet = False
        g = rules.new_game(layout, agents, game_display, length, mute_agents, catch_exceptions)
        g.run(delay=delay_step)
        if not be_quiet: games_list.append(g)

        g.record = None
        if record:
            import time
            import pickle
            import contest.game as game
            components = {'layout': layout, 'agents': [game.Agent() for _ in agents], 'actions': g.move_history,
                          'length': length, 'red_team_name': red_team_name, 'blue_team_name': blue_team_name}
            print("recorded")
            g.record = pickle.dumps(components)
            sub_folder = f'www/contest_{contest_name}/replays'
            os.makedirs(name=sub_folder, exist_ok=True)
            with open(f'{sub_folder}/match_{match_id}.replay', 'wb') as f:
                f.write(g.record)

    if num_games > 1:
        scores = [game.state.data.score for game in games_list]
        red_win_rate = [s > 0 for s in scores].count(True) / float(len(scores))
        blue_win_rate = [s < 0 for s in scores].count(True) / float(len(scores))
        print(f'Average Score:', sum(scores) / float(len(scores)))
        print('Scores:       ', ', '.join([str(score) for score in scores]))
        print(f'Red Win Rate:  {[s > 0 for s in scores].count(True)}/{len(scores)} ({red_win_rate:.2f})')
        print(f'Blue Win Rate: {[s < 0 for s in scores].count(True)}/{len(scores)} ({blue_win_rate:.2f})')
        print('Record:       ', ', '.join([('Blue', 'Tie', 'Red')[max(0, min(2, 1 + s))] for s in scores]))
    return games_list


def get_games_data(games, red_name, blue_name, time_taken, match_id):
    # (n1, n2, layout, score, winner, time_taken)
    games_data = []
    for game in games:
        layout_name = game.state.data.layout.layout_name
        score = game.state.data.score
        if score > 0:
            winner, score = red_name, score
        elif score < 0:
            winner, score = blue_name, -score
        else:
            winner, score = None, 0
        games_data.append((red_name, blue_name, layout_name, score, winner, time_taken, match_id))
    return games_data


def compute_team_stats(games_data, team_name):
    wins, draws, loses, score = 0, 0, 0, 0
    for gd in games_data:  # gd[4] is the winner
        if gd[4] is None:
            draws += 1
        elif gd[4] is team_name:
            wins += 1
            score += gd[3]  # gd[3] is the final score
        else:
            loses += 1
    points = (wins * 3) + draws
    return [
        ((points * 100) / (3 * (wins + draws + loses))) if wins + draws + loses > 0 else 0,
        points,
        wins,
        draws,
        loses,
        0,  # errors not counted
        score,
    ]


def save_score(games, total_time, *, contest_name, match_id, **kwargs):
    assert games
    sub_folder = f'www/contest_{contest_name}/scores'
    os.makedirs(name=sub_folder, exist_ok=True)
    games_data = get_games_data(games=games,
                                red_name=kwargs['red_team_name'],
                                blue_name=kwargs['blue_team_name'],
                                time_taken=total_time,
                                match_id=match_id)
    teams_stats = {
        kwargs['red_team_name']: compute_team_stats(games_data=games_data, team_name=kwargs['red_team_name']),
        kwargs['blue_team_name']: compute_team_stats(games_data=games_data, team_name=kwargs['blue_team_name']),
    }
    match_data = {
        'games': games_data,
        'max_steps': games[0].length,
        'teams_stats': teams_stats,
        'layouts': [game.state.data.layout.layout_name for game in games],
    }

    import json
    with open(f'{sub_folder}/match_{match_id}.json', 'w') as f:
        # print(games.state.data.score, file=f)
        f.write(json.dumps(match_data, sort_keys=True, indent=4))


def run(args):
    """
    The main function called when pacman.py is run from the command line:
    > python capture.py

    See the usage string for more details.
    > python capture.py --help
    """
    start_time = time.time()
    options = read_command(args)  # Get game components based on input
    print(options, file=sys.stdout)

    games = run_games(**options)
    total_time = round(time.time() - start_time, 0)

    if games:
        # save_score(games=games, contest_name=options['contest_name'], match_id=options['match_id'])
        save_score(games=games, total_time=total_time, **options)
    print(f'\nTotal Time Game: {total_time}', file=sys.stdout)


def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    main()
