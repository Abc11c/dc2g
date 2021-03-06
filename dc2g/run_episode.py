from __future__ import division, print_function
from __future__ import absolute_import

import sys
import gym
import time
from optparse import OptionParser

import numpy as np
import argparse
import scipy.signal, scipy.misc

import matplotlib.pyplot as plt

from dc2g.planners.util import instantiate_planner

# TODO: Don't explicitly import this here, register these envs upon install
import dc2g.driveway_env

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

np.set_printoptions(suppress=True, precision=4)
np.warnings.filterwarnings('ignore')
np.set_printoptions(threshold=np.inf)

dir_path = os.path.dirname(os.path.realpath(__file__))

make_individual_figures = False
save_individual_figures = False
save_panel_figures = False
plot_panels = False
make_video = False

import sys, signal
def signal_handler(signal, frame):
    try:
        print("Shutting down environment gracefully...")
        ENVIRONMENT.on_shutdown()
    except:
        print("Environment doesn't support graceful shutdown.")
    print("\nprogram exiting gracefully")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

global ENVIRONMENT

def start_experiment(env_name, env_type):
    global ENVIRONMENT
    if env_type == "MiniGrid":
        import gym_minigrid
        env = gym.make(env_name)
        ENVIRONMENT = env
    elif env_type == "House3D":
        from House3D.common import load_config

        from House3D.house import House
        from House3D.core import Environment, MultiHouseEnv
        from House3D.roomnav import objrender, RoomNavTask
        from House3D.objrender import RenderMode

        api = objrender.RenderAPI(
                w=400, h=300, device=0)
        cfg = load_config('/home/mfe/code/dc2g/House3D/House3D/config.json')

        house = '00a42e8f3cb11489501cfeba86d6a297'
        # houses = ['00065ecbdd7300d35ef4328ffe871505',
        # 'cf57359cd8603c3d9149445fb4040d90', '31966fdc9f9c87862989fae8ae906295', 'ff32675f2527275171555259b4a1b3c3',
        # '7995c2a93311717a3a9c48d789563590', '8b8c1994f3286bfc444a7527ffacde86', '775941abe94306edc1b5820e3a992d75',
        # '32e53679b33adfcc5a5660b8c758cc96', '4383029c98c14177640267bd34ad2f3c', '0884337c703e7c25949d3a237101f060',
        # '492c5839f8a534a673c92912aedc7b63', 'a7e248efcdb6040c92ac0cdc3b2351a6', '2364b7dcc432c6d6dcc59dba617b5f4b',
        # 'e3ae3f7b32cf99b29d3c8681ec3be321', 'f10ce4008da194626f38f937fb9c1a03', 'e6f24af5f87558d31db17b86fe269cf2',
        # '1dba3a1039c6ec1a3c141a1cb0ad0757', 'b814705bc93d428507a516b866efda28', '26e33980e4b4345587d6278460746ec4',
        # '5f3f959c7b3e6f091898caa8e828f110', 'b5bd72478fce2a2dbd1beb1baca48abd', '9be4c7bee6c0ba81936ab0e757ab3d61']
        #env = MultiHouseEnv(api, houses[:3], cfg)  # use 3 houses
        house_env = Environment(api, house, cfg)
        env = RoomNavTask(house_env, hardness=0.6, discrete_action=True)
        ENVIRONMENT = env.house
    elif env_type == "AirSim":
        import gym_airsim
        env = gym.make(env_name)
        ENVIRONMENT = env

    return env

def reset_env(env):
    first_obs = env.reset()
    return first_obs

def run_episode(planner_name, seed, env, env_type, difficulty_level='easy', plot_panels=False):
    # Load the gym environment
    env.seed(seed=int(seed))

    env.use_semantic_coloring = True
    # env.use_semantic_coloring = planner_args[planner_name]['use_semantic_coloring']
    env.set_difficulty_level(difficulty_level)
    obs = reset_env(env)
    planner = instantiate_planner(planner_name, env, env_type, plot_panels=plot_panels)

    while env.step_count < env.max_steps:

        # Use latest observation to choose next action
        if obs['semantic_gridmap'] is None:
            action = 0
        else:
            action = planner.plan(obs)

        # Execute the action in the environment and receive new observation
        obs, reward, done, info = env.step(action)

        print(obs['pos'], obs['theta_ind'])

        # if env.step_count == 10:
        #     # planner.animate_episode(fig_type="observation")
        #     planner.animate_episode()
        #     break

        # env.render('human')
        if done:
            print('Done! Took {} steps.'.format(env.step_count))
            planner.animate_episode(fig_type="observation")
            # planner.animate_episode()
            break
    return done, env.step_count, env.world_id

def main():
    parser = OptionParser()
    parser.add_option(
        "-e",
        "--env-name",
        dest="env_name",
        help="gym environment to load",
        # default='AirSim-v0'
        # default='House3D-RoomNav'
        default='MiniGrid-DrivewayEnv-32x32-v0'
    )
    parser.add_option(
        "-p",
        "--planner",
        dest="planner",
        help="name of planner to use (e.g. dc2g, frontier)",
        # default='dc2g_without_semantics'
        default='dc2g'
        # default='dc2g_rescale'
        # default='frontier'
        # default='oracle'
    )
    parser.add_option(
        "-s",
        "--seed",
        dest="seed",
        help="seed for deterministically defining random environment behavior",
        default='1337'
    )
    (options, args) = parser.parse_args()

    if "MiniGrid" in options.env_name:
        env_type = "MiniGrid"
    elif "House3D" in options.env_name:
        env_type = "House3D"
    elif "AirSim" in options.env_name:
        env_type = "AirSim"

    env = start_experiment(
        env_name=options.env_name,
        env_type=env_type,
        )
    success, num_steps, world_id = run_episode(
        planner_name=options.planner,
        seed=options.seed,
        env=env,
        env_type=env_type,
        difficulty_level='test_scenario',
        )


if __name__ == "__main__":
    main()