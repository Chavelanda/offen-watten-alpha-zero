import argparse
from EnvironmentSelector import EnvironmentSelector
from core.agents.AgentMCTS import AgentMCTS
from core.utils.utils import serialize, deserialize
from core.World import World

from collections import deque

import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--agent_new", dest="agent_profile_new",
                        help="Agent profile from EnvironmentSelector. Required.")

    parser.add_argument("--agent_old", dest="agent_profile_old",
                        help="Agent profile from EnvironmentSelector. Required.")

    parser.add_argument("--games_num", dest="games_num", type=int,
                        help="Number of games to play. Required.")

    parser.add_argument("--agent_new_path", dest="agent_new_path",
                        help="Path to the new agent's model.")

    parser.add_argument("--agent_old_path", dest="agent_old_path",
                        help="Path to the old agent's model.")

    parser.add_argument('--verbose', dest='verbose', action='store_true', help="Show games outcome")
    parser.set_defaults(verbose=True)

    parser.add_argument('--debug', dest='debug', action='store_true', help="Show games per turn")
    parser.set_defaults(debug=False)

    parser.add_argument("--max_steps", dest="max_steps", type=int,
                        default=None,
                        help="Max steps in each game")

    parser.add_argument('--optimize_for_inference', dest='optimize_for_inference', action='store_true',
                        help="Optimize for inference in self-play and evaluation phases")
    parser.set_defaults(optimize_for_inference=False)

    options = parser.parse_args()

    if not options.agent_profile_new:
        parser.error('Agent profile must be selected')

    if not options.agent_profile_old:
        parser.error('Agent profile must be selected')

    if not options.games_num:
        parser.error('Number of games must be selected')

    env_selector = EnvironmentSelector()
    agent_first = env_selector.get_agent(options.agent_profile_new)
    print("Pit with agent ", agent_first.name)
    agent_first.set_exploration_enabled(False)

    agent_second = env_selector.get_agent(options.agent_profile_old)
    print("Pit with agent ", agent_second.name)
    agent_second.set_exploration_enabled(False)

    agent_profile = env_selector.get_profile(options.agent_profile_new)
    game = env_selector.get_game(agent_profile.game)

    # When playing total watten with humans the def of game has to be changed
    # to inject a sub_watten human agent for the right player
    if options.agent_profile_new == env_selector.TOTAL_WATTEN_AGENT_HUMAN.agent_profile\
            and options.agent_profile_old == env_selector.TOTAL_WATTEN_AGENT_HUMAN.agent_profile:
        # get_game for human_vs_human
        game = env_selector.get_game(env_selector.GAME_TOTAL_WATTEN_H_VS_H)

    elif options.agent_profile_new == env_selector.TOTAL_WATTEN_AGENT_HUMAN.agent_profile:
        # get_game for human_vs_non_human
        game = env_selector.get_game(env_selector.GAME_TOTAL_WATTEN_H_VS_NH)

    elif options.agent_profile_old == env_selector.TOTAL_WATTEN_AGENT_HUMAN.agent_profile:
        # get_game for non_human_vs_human
        game = env_selector.get_game(env_selector.GAME_TOTAL_WATTEN_NH_VS_H)

    agents = [agent_first, agent_second]

    if options.agent_new_path:
        agent_first.load(options.agent_new_path)
        if options.optimize_for_inference:
            agent_first.disable_training_capability(temp_dir="temp", optimize=True)

    if options.agent_old_path:
        agent_second.load(options.agent_old_path)
        if options.optimize_for_inference:
            agent_second.disable_training_capability(temp_dir="temp", optimize=True)

    world = World()

    sess_arena_examples, games_results = world.execute_games(agents,
                                                             game,
                                                             options.games_num,
                                                             max_game_steps_n=options.max_steps,
                                                             verbose=options.verbose,
                                                             show_every_turn=options.debug)
