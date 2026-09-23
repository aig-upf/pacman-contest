#!/usr/bin/env python3
"""
Profile Pacman Capture the Flag games to identify CPU bottlenecks.

Profiles individual games to show cumulative time spent in key functions during
game execution. Outputs KEY BOTTLENECKS aggregated across all profiled games.

Usage:
    python profiler.py [options]
    
Examples:
    python profiler.py
        - Profile 10 games between baseline_team and baseline_team (default)
    
    python profiler.py -r my_team -b baseline_team -n 5
        - Profile 5 games between red (my_team) and blue (baseline_team)
    
    python profiler.py -n 3 -b my_team
        - Profile 3 games with red (baseline_team, default) vs blue (my_team)
    
    python profiler.py -r agents/team1/my_team.py -b agents/team2/my_team.py
        - Profile 10 games (default) between two specific agent files
"""

import sys
import os
import cProfile
import pstats
import argparse
import json
from pathlib import Path
from collections import defaultdict

# Setup paths for contest module imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / 'src'))
sys.path.insert(0, str(script_dir / 'src' / 'contest'))

# Change to contest directory so layouts are found
os.chdir(script_dir / 'src' / 'contest')

import contest.capture as capture
import contest.layout as layout_module
import contest.text_display as text_display


def run_profiled_game(red_team_path, blue_team_path, layout_name='defaultCapture'):
    """
    Run a single game with profiling and return profiler, score, and move count.
    
    Args:
        red_team_path: Path to red team's my_team.py
        blue_team_path: Path to blue team's my_team.py
        layout_name: Name of layout to use (default: 'defaultCapture')
    
    Returns:
        Tuple of (profiler, score, moves) where:
        - profiler: cProfile.Profile object with collected stats
        - score: Final game score (positive = red wins)
        - moves: Number of moves made in the game
    """
    profiler = cProfile.Profile()
    score = 0
    moves = 0
    
    profiler.enable()
    try:
        # Mimic runner.py game execution flow
        layout_obj = layout_module.get_layout(layout_name)
        if layout_obj is None:
            return profiler, score, moves
        
        # Load agents using official capture.load_agents() API
        red_agents = capture.load_agents(True, red_team_path, {})
        blue_agents = capture.load_agents(False, blue_team_path, {})
        
        # Check if agents loaded successfully
        if None in red_agents or None in blue_agents:
            return profiler, score, moves
        
        # Interleave agents in standard contest order
        # Format: [red0, blue0, red1, blue1]
        agents_list = [r for pair in zip(red_agents, blue_agents) for r in pair]
        
        # Create and run game with standard contest settings
        display = text_display.NullGraphics()
        rules = capture.CaptureRules()
        game = rules.new_game(layout_obj, agents_list, display, length=1200,
                             mute_agents=True, catch_exceptions=True)
        
        game.run(delay=0)
        
        # Extract game results with defensive checks
        moves = len(game.move_history) if hasattr(game, 'move_history') else 0
        score = game.state.data.score if hasattr(game.state, 'data') else 0
        
    finally:
        profiler.disable()
    
    return profiler, score, moves


def format_bottleneck(name, cumtime, calls):
    """Format a bottleneck entry for display."""
    if calls > 0:
        percall = (cumtime / calls) * 1000  # Convert to milliseconds
    else:
        percall = 0
    return f"{name:<30} {cumtime:>8.4f}s ({calls:>6d} calls, {percall:>7.2f}ms/call)"


def main():
    parser = argparse.ArgumentParser(
        description='Profile Pacman Capture the Flag games to identify bottlenecks.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('-r', '--red', default='baseline_team',
                       help='Red team (path to my_team.py or team name, default: baseline_team)')
    parser.add_argument('-b', '--blue', default='baseline_team',
                       help='Blue team (path to my_team.py or team name, default: baseline_team)')
    parser.add_argument('-n', '--num-games', type=int, default=10,
                       help='Number of games to profile (default: 10)')
    parser.add_argument('-l', '--layout', default='defaultCapture',
                       help='Layout name (default: defaultCapture)')
    parser.add_argument('--save', type=str, default=None,
                       help='Save profiling results to JSON file for comparison')
    parser.add_argument('--compare', type=str, default=None,
                       help='Compare results with a previous profiling run (JSON file)')
    
    args = parser.parse_args()
    
    # Resolve team paths
    def resolve_team_path(team_arg):
        """Resolve team argument to a valid file path."""
        # If it already ends with .py, use as-is
        if team_arg.endswith('.py'):
            team_path = Path(team_arg)
        else:
            # Add .py extension
            team_path = Path(team_arg + '.py')
        
        # If path exists (absolute or relative), use it
        if team_path.exists():
            return str(team_path.resolve())
        
        # Otherwise, try in src/contest directory
        contest_path = Path(__file__).parent / 'src' / 'contest' / team_path.name
        if contest_path.exists():
            return str(contest_path.resolve())
        
        # If nothing exists, return the original attempt for error reporting
        return str(contest_path.resolve())
    
    red_team = resolve_team_path(args.red)
    blue_team = resolve_team_path(args.blue)
    
    red_name = Path(red_team).stem
    blue_name = Path(blue_team).stem
    
    print(f"Profiling games")
    print(f"Red:  {red_name}")
    print(f"Blue: {blue_name}")
    print(f"Games: {args.num_games}\n")
    
    # Collect profiling data across all games
    all_stats = defaultdict(lambda: {'cumtime': 0, 'tottime': 0, 'calls': 0})
    total_moves = 0
    total_score = 0
    
    for game_num in range(args.num_games):
        print(f"Game {game_num + 1}/{args.num_games}...", end=' ')
        
        profiler, score, moves = run_profiled_game(red_team, blue_team, args.layout)
        
        # Collect stats
        s = pstats.Stats(profiler)
        s.strip_dirs()
        
        for func, (cc, nc, tt, ct, callers) in s.stats.items():
            func_name = func[2]  # Get just the function name
            all_stats[func_name]['cumtime'] += ct
            all_stats[func_name]['tottime'] += tt
            all_stats[func_name]['calls'] += nc
        
        total_moves += moves
        total_score += score
        
        print(f"{moves} moves, score={score:+.0f}")
    
    # Print KEY BOTTLENECKS - dynamically find top functions by cumulative time
    print("\n" + "="*80)
    print("KEY BOTTLENECKS (aggregated across all games)")
    print("="*80)
    
    # Sort all functions by cumulative time and show top bottlenecks
    sorted_funcs = sorted(all_stats.items(), key=lambda x: x[1]['cumtime'], reverse=True)
    
    # Filter to significant bottlenecks (> 0.01s cumtime)
    bottlenecks = [(name, stats) for name, stats in sorted_funcs 
                   if stats['cumtime'] > 0.01 and stats['calls'] > 0]
    
    # Display top 4 bottlenecks
    for name, stats in bottlenecks[:4]:
        print(format_bottleneck(name, stats['cumtime'], stats['calls']))
    
    print("="*80)
    print()
    
    # Print statistics
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total games:     {args.num_games}")
    print(f"Total moves:     {total_moves}")
    print(f"Avg moves/game:  {total_moves // args.num_games if args.num_games > 0 else 0}")
    print(f"Total score:     {total_score:+.0f}")
    print(f"Avg score/game:  {total_score / args.num_games if args.num_games > 0 else 0:+.1f}")
    print("="*80)
    print()
    
    # Prepare data for saving
    profiling_data = {
        'bottlenecks': [{'name': name, 'cumtime': stats['cumtime'], 'calls': stats['calls']} 
                       for name, stats in bottlenecks[:10]],
        'summary': {
            'total_games': args.num_games,
            'total_moves': total_moves,
            'total_score': total_score
        }
    }
    
    # Save results if requested
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(profiling_data, f, indent=2)
        print(f"Results saved to: {args.save}")
        print()
    
    # Compare with previous results if requested
    if args.compare:
        try:
            with open(args.compare, 'r') as f:
                baseline_data = json.load(f)
            
            print("="*80)
            print("COMPARISON WITH BASELINE")
            print("="*80)
            
            # Compare top bottlenecks
            baseline_bottlenecks = {b['name']: b for b in baseline_data['bottlenecks']}
            current_bottlenecks = {b['name']: b for b in profiling_data['bottlenecks']}
            
            print("\nFunction                       | Baseline   | Current    | Change")
            print("-"*80)
            
            for current in profiling_data['bottlenecks'][:4]:
                name = current['name']
                current_time = current['cumtime']
                
                if name in baseline_bottlenecks:
                    baseline_time = baseline_bottlenecks[name]['cumtime']
                    diff = current_time - baseline_time
                    pct = (diff / baseline_time * 100) if baseline_time > 0 else 0
                    
                    # Show improvement with color indication
                    if diff < 0:
                        change_str = f"{-diff:>7.4f}s ({pct:>6.1f}%) ✓ FASTER"
                    else:
                        change_str = f"+{diff:>6.4f}s ({pct:>6.1f}%) ✗ SLOWER"
                    
                    print(f"{name[:28]:<30} | {baseline_time:>8.4f}s | {current_time:>8.4f}s | {change_str}")
                else:
                    print(f"{name[:28]:<30} | {'N/A':>10} | {current_time:>8.4f}s | NEW FUNCTION")
            
            # Show top baseline bottlenecks that were eliminated or improved significantly
            print("\nBaseline top functions status:")
            print("-"*80)
            for i, baseline in enumerate(baseline_data['bottlenecks'][:5], 1):
                name = baseline['name']
                baseline_time = baseline['cumtime']
                
                if name in current_bottlenecks:
                    current_time = current_bottlenecks[name]['cumtime']
                    diff = current_time - baseline_time
                    pct = (diff / baseline_time * 100) if baseline_time > 0 else 0
                    if diff < 0:
                        change_str = f"↓ {-diff:.4f}s ({pct:.1f}%)"
                    else:
                        change_str = f"↑ +{diff:.4f}s ({pct:.1f}%)"
                    print(f"{i}. {name[:28]:<30} | {baseline_time:>8.4f}s → {current_time:>8.4f}s | {change_str}")
                else:
                    print(f"{i}. {name[:28]:<30} | {baseline_time:>8.4f}s → ELIMINATED | ✓ REMOVED")
            
            print("="*80)
        except FileNotFoundError:
            print(f"Error: Comparison file not found: {args.compare}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in comparison file: {args.compare}")
    

if __name__ == '__main__':
    main()
