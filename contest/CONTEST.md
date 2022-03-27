# Contest: Pacman Capture the Flag

This is an adapted version from the [official contest page](http://ai.berkeley.edu/contest.html).

> ![](img/logo-capture_the_flag.png)

> Enough of defense,\
>  Onto enemy terrain.\
>  Capture all their food!

### Table of contents

  * [Introduction](#introduction)
     * [Key files to read:](#key-files-to-read)
     * [Supporting files (do not modify):](#supporting-files-do-not-modify)
  * [Rules of Pacman Capture the Flag](#rules-of-Pacman-capture-the-flag)
     * [Layout:](#layout)
     * [Scoring:](#scoring)
     * [Eating Pacman:](#eating-Pacman)
     * [Power capsules:](#power-capsules)
     * [Observations:](#observations)
     * [Winning:](#winning)
     * [Computation Time:](#computation-time)
  * [Getting Started](#getting-started)
     * [Layouts](#layouts)
  * [Designing Agents](#designing-agents)
     * [Baseline Team:](#baseline-team)
     * [Interface:](#interface)
     * [Distance Calculation:](#distance-calculation)
     * [Restrictions:](#restrictions)
     * [Warning:](#warning)
  * [Official Tournaments](#official-tournaments)
     * [Infrastructure:](#infrastructure)
     * [Software, resources, tips](#software-resources-tips)
     * [Teams:](#teams)
     * [Ranking:](#ranking)
     * [Prize Summary:](#prize-summary)
  * [Acknowledgements](#acknowledgements)

## Introduction

The course contest involves a multi-player capture-the-flag variant of Pacman, where agents control both Pacman and ghosts in coordinated team-based strategies. Your team will try to eat the food on the far side of the map, while defending the food on your home side. 

There are many files in this package, most of them implementing the game itself. The **only** file that you should work on is `myTeam.py` and this will be the only file that you will submit.

### Key files to read:

* `capture.py`: The main file that runs games locally. This file also describes the new capture the flag GameState type and rules.
* `captureAgents.py`: Specification and helper methods for capture agents.
* `baselineTeam.py`: Example code that defines two very basic reflex agents, to help you get started.
* `myTeam.py`: This is where you define your own solution agents (and the only thing used go run the contest).

### Supporting files (do not modify):

* `game.py`: The logic behind how the Pacman world works. This file describes several supporting types like AgentState, Agent, Direction, and Grid.
* `util.py`: Useful data structures for implementing search algorithms.
* `distanceCalculator.py`: Computes shortest paths between all maze positions.
* `graphicsDisplay.py`: Graphics for Pacman.
* `graphicsUtils.py`: Support for Pacman graphics.
* `textDisplay.py`: ASCII graphics for Pacman.
* `keyboardAgents.py`: Keyboard interfaces to control Pacman.
* `layout.py`: Code for reading layout files and storing their contents.


## Rules of Pacman Capture the Flag

### Layout: 

The Pacman map is now divided into two halves: blue (right) and red (left). Red agents (which all have even indices) must defend the red food while trying to eat the blue food. When on the red side, a red
agent is a ghost. When crossing into enemy territory, the agent becomes a Pacman.

### Scoring:

When a Pacman eats a food dot, the food is permanently removed and is scored when that Pacman comes back *home*. Red team scores are positive, while Blue team scores are negative.

### Eating Pacman:

When a Pacman is eaten by an opposing ghost, the Pacman returns to its starting position (as a ghost). No points are awarded for eating an opponent.

### Power capsules:

If Pacman eats a power capsule, agents on the opposing team become "scared" for the next 40 moves, or until they are eaten and respawn, whichever comes sooner. Agents that are "scared" are susceptible while in the form of ghosts (i.e. while on their own team's side) to being eaten by Pacman. Specifically, if Pacman collides with a "scared" ghost, Pacman is unaffected and the ghost respawns at its starting position (no longer in the "scared" state).

### Observations:

Agents can only observe an opponent's configuration (position and direction) if they or their teammate is within 5 squares (Manhattan distance). In addition, an agent always gets a noisy distance reading for each agent on the board, which can be used to approximately locate unobserved opponents.

### Winning:

A game ends when one team eats all but two of the opponents' dots. Games are also limited to 1200 agent moves (300 moves per each of the four agents). If this move limit is reached, whichever team has eaten the most food wins. If the score is zero (i.e., tied) this is recorded as a tie game.

### Computation Time:

We will run your submissions on an Amazon EC2 like instance supported by the Australian [Nectar Cloud](https://nectar.org.au/) , which has a 1.7 Ghz Xeon / Opteron processor equivalent and 1.7gb of RAM. See below for more details.

Each agent has 1 second to return each action. Each move which does not return within one second will incur a warning. After three warnings, or any single move taking more than 3 seconds, the game is forfeit. 

There will be an initial start-up allowance of 15 seconds (use the `register_initial_state` function). 

If you agent times out or otherwise throws an exception, an error message will be present in the log files, which you can download from the results page (see below).


## Getting Started

By default, you can run a game with the simple `baselineTeam` that the staff has provided:

```bash
$ python3 capture.py
```

**Make sure you are using python3**

A wealth of options are available to you:

```bash
$ python3 capture.py --help
```

There are four slots for agents, where agents 0 and 2 are always on the red team, and 1 and 3 are on the blue team. Agents are created by agent factories (one for Red, one for Blue). See the section on designing
agents for a description of the agents invoked above. The only team that we provide is the `baselineTeam`. It is chosen by default as both the red and blue team, but as an example of how to choose teams:

```python
$ python3 capture.py -r baselineTeam -b baselineTeam
```

which specifies that the red team `-r` and the blue team `-b` are both created from `baselineTeam.py`.

To specify agents elsewhere:

```shell
$ python3 capture.py -r path/to/red/team/myTeam.py -b path/to/blue/team/myTeam.py
```

To control one of the four agents with the keyboard, pass the appropriate option:

```shell
$ python capture.py --keys0
```

The arrow keys control your character, which will change from ghost to Pacman when crossing the center line.

### Layouts

By default, all games are run on the `defaultcapture` layout. To test your agent on other layouts, use the `-l` option. In particular, you can generate random layouts by specifying `RANDOM[seed]`. For example, `-l RANDOM13` will use a map randomly generated with seed 13.

## Designing Agents

Unlike project 2, an agent now has the more complex job of trading off offense versus defense and effectively functioning as both a ghost and a Pacman in a team setting. Furthermore, the limited information provided to your agent will likely necessitate some probabilistic tracking (like project 4). Finally, the added time limit of computation introduces new challenges.

### Baseline Team:

To kick-start your agent design, we have provided you with a team of two baseline agents, defined in `baselineTeam.py`. They are both quite bad. The `OffensiveReflexAgent` moves toward the closest food on the opposing side. The `DefensiveReflexAgent` wanders around on its own side and tries to chase down invaders it happens to see.

### Interface:

The `GameState` in `capture.py` should look familiar, but contains new methods like `getRedFood`, which gets a grid of food on the red side (note that the grid is the size of the board, but is only true
for cells on the red side with food). Also, note that you can list a team's indices with `getRedTeamIndices`, or test membership with `isOnRedTeam`.

Finally, you can access the list of noisy distance observations via `getAgentDistances`. These distances are within 6 of the truth, and the noise is chosen uniformly at random from the range [-6, 6] (e.g., if the true distance is 6, then each of {0, 1, ..., 12} is chosen with probability 1/13). You can get the likelihood of a noisy reading using `getDistanceProb`.

### Distance Calculation:

To facilitate agent development, we provide code in `distanceCalculator.py` to supply shortest path maze distances.

To get started designing your own agent, we recommend subclassing the `CaptureAgent` class. This provides access to several convenience methods. Some useful methods are:

```python
      def getFood(self, gameState):
        """
        Returns the food you're meant to eat. This is in the form
        of a matrix where m[x][y]=true if there is food you can
        eat (based on your team) in that square.
        """

      def getFoodYouAreDefending(self, gameState):
        """
        Returns the food you're meant to protect (i.e., that your
        opponent is supposed to eat). This is in the form of a
        matrix where m[x][y]=true if there is food at (x,y) that
        your opponent can eat.
        """

      def getOpponents(self, gameState):
        """
        Returns agent indices of your opponents. This is the list
        of the numbers of the agents (e.g., red might be "1,3,5")
        """

      def getTeam(self, gameState):
        """
        Returns agent indices of your team. This is the list of
        the numbers of the agents (e.g., red might be "1,3,5")
        """

      def getScore(self, gameState):
        """
        Returns how much you are beating the other team by in the
        form of a number that is the difference between your score
        and the opponents score. This number is negative if you're
        losing.
        """

      def getMazeDistance(self, pos1, pos2):
        """
        Returns the distance between two points; These are calculated using the provided
        distancer object.

        If distancer.getMazeDistances() has been called, then maze distances are available.
        Otherwise, this just returns Manhattan distance.
        """

      def getPreviousObservation(self):
        """
        Returns the GameState object corresponding to the last
        state this agent saw (the observed state of the game last
        time this agent moved - this may not include all of your
        opponent's agent locations exactly).
        """

      def getCurrentObservation(self):
        """
        Returns the GameState object corresponding this agent's
        current observation (the observed state of the game - this
        may not include all of your opponent's agent locations
        exactly).
        """

      def debugDraw(self, cells, color, clear=False):
        """
        Draws a colored box on each of the cells you specify. If clear is True,
        will clear all old drawings before drawing on the specified cells.
        This is useful for debugging the locations that your code works with.

        color: list of RGB values between 0 and 1 (i.e. [1,0,0] for red)
        cells: list of game positions to draw on  (i.e. [(20,5), (3,22)])
        """
```

### Restrictions:

You are free to use any techniques you want, but will need to respect the provided APIs to have a valid submission. Agents which compute during the opponent's turn will be disqualified. In particular, any form of multi-threading is disallowed, because we have found it very hard to ensure that no computation takes place on the opponent's turn.

### Warning:

If one of your agents produces any `stdout`/`stderr` output during its games in the any tournament (preliminary or final), that output will be included in the contest results posted on the website. Additionally, in some cases a stack trace may be shown among this output in the event that one of your agents throws an exception. You should design your code in such a way that this does not expose any information that you wish to keep confidential.

## Official Tournaments

### Infrastructure:

The actual competitions will be run using nightly automated tournaments on an Amazon EC2 like cluster (1.7 Ghz Xeon / 1.7GB RAM machines in the [Nectar Cloud](https://nectar.org.au/)), with the final tournament deciding the final contest outcome. See the submission instructions for details of how to enter a team into the tournaments via git tagging.

We will try to run **pre-contest feedback tournaments frequently**, if possible every day. The number of games each team plays every other team will depend on the number of teams. To reduce randomness, the final contest after submission will include more runs.

The **layouts** used in the tournament will be drawn from both the default layouts as well as randomly generated layouts each night. All layouts are symmetric, and the team that moves first is randomly chosen.

The **results** of each tournament (pre-contest, preliminary, and final) will be published on a web-page where you will be able to see the overall rankings and scores for each match. You can also download replays, the layouts used, and the `stdout`/`stderr` logs for each agent.

### Software, resources, tips

* Your code will be run by the following command:

    ```shell
    python3 capture.py --delay 0.0 -r teams/<team1>/myTeam.py -b teams/<team2>/myTeam.py
    ```

    please make sure your `AgentFactory` is defined in `myTeam.py`.

* You may have coded supported files that you will import in your `myTeam.py`, for example a module  `abc.py`. In order for the contest script to find it you need to do it this way:

  ```python
  import os
  import sys

  cd = os.path.dirname(os.path.abspath(__file__))
  sys.path.append(cd)

  import abc 
  ```

If you do not append that to the sys path, your `abc.py` module will not be found and your agent will crash.

* We have added some useful options:
     * `--delay` to slow down the execution if you want to visualize in slow
motion;
     * `--record` or `--replay`. 
     
    Use `--help` to check all the options.

* Check the `replay.py` script to list and replay individual games in a convenient manner.
     
* Do *NOT* use the current working directory to write temporary files; instead, redirect all output to your own folder `./teams/<your_teamname>/`. For example, if you use a planner online, and generate PDDL files and solutions, redirect your planner call, solution outputs, etc., to your own folder. You can use Python code to do it automatically, or you can hardcode it assuming that your team will be located in `./teams/<your_teamname>/` folder.
* If you want to use any other 3rd-party executable please discuss with us before submission. You can assume that `TensorFlow`, `keras`, `py_trees`, `sklearn`, `numpy`, `scipy` and `neat-python` libraries are installed in our running environment, using the latest version available in Ubuntu 18.04. Planner `ff` executable version 2.1 of the [Metric-FF planner](https://fai.cs.uni-saarland.de/hoffmann/metric-ff.html) will be available in `/usr/local/bin`.

### Teams: 

You may work in teams of up to 3/4 people (2 in some cases).

### Ranking: 

Rankings are determined according to the number of points received in a nightly round-robin tournaments, where a win is worth 3 points, a tie is worth 1 point, and losses are worth 0 (Ties are not worth very much to discourage stalemates). 

Extra credit will be awarded according to the final competition, but participating early in the pre-competitions will increase your learning and feedback. 

In addition, dastardly staff members have entered the tournament with their own devious agents, seeking fame and glory. These agents have team names beginning with `Staff-`. 


### Prize Summary:

- **Diplomas** will be awarded to all teams entering the final playoff series.
- **High-quality dark chocolate** will be awarded to those teams reaching semi-finals will further receive one 

The earlier you submit your agents, the better your chances of earning  a high ranking, and the more chances you will have to defeat the staff agents.


## Acknowledgements

This local game was developed by [UC Berkley](http://ai.berkeley.edu/contest.html).
 
The tournament software infrastructure was developed by staff at RMIT University and The University of Melbourne under the direction of [Prof. Sebastian Sardina](https://sites.google.com/view/ssardina/home) and [Dr. Nir Lipovetzky](https://nirlipo.github.io/).

Have fun! Please bring our attention to any problems you discover.


![](img/contestLayout.png)
