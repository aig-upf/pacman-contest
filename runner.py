import sys
import time
import contest.capture

if __name__ == '__main__':
    """
    The main function called when pacman.py is run from the command line:
    > python capture.py
    
    See the usage string for more details.
    > python capture.py --help
    """
    start_time = time.time()
    options = contest.capture.read_command(sys.argv[1:])  # Get game components based on input
    print(options)

    games = contest.capture.run_games(**options)

    if games:
        contest.capture.save_score(games=games[0], contest_name=options['contest_name'], match_id=options['game_id'])
    print('\nTotal Time Game: %s' % round(time.time() - start_time, 0))

