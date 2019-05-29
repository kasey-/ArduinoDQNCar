import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.simulation_mode = True
        self.action_space = spaces.Box(low=np.array([-1000]), high=np.array([1000]), dtype=np.int32)
        self.observation_space = spaces.Box(low=np.array([-1000]), high=np.array([1000]), dtype=np.int32)
        self.seed()
        self.reset()

    def set_mode(self, simulation):
        self.simulation_mode = bool(simulation)
        print("Simulation mode = {}".format(self.simulation_mode))
    
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.action = 0
        self.life = MAX_LIFE
        self.score = 0
        self.done = False
        self.cursor = random.randint(CUSRSOR-SAFE, CUSRSOR+SAFE)
        self.target = random.randint(MINIMUM+SAFE, MAXIMUM-SAFE)
        self.distance = self.target - self.cursor
        return [self.distance]

    def step(self, action):
        self.action = int(action[0])
        self.score = 0
        self.done = False
        self.cursor += self.action
        self.distance = self.target - self.cursor
        # compute reward
        # Check if still alive
        if self.life == 0:
            self.done = True
            self.score = -1000
        # Check if we are outside of range
        elif((self.cursor < MINIMUM) or (self.cursor > MAXIMUM)):
            self.done = True
            self.score = -1000
        # Check if we are on the target
        elif (self.cursor == self.target):
            self.done = True
            self.score = 1000 / (MAX_LIFE - self.life +1)
        # If not dead nor on the spot we compute the score
        else:
            self.score = 10
        self.life -= 1
        return [self.distance], self.score, self.done, {}

    def render(self, mode='human'):
        print({
            'target':self.target,
            'cursor':self.cursor,
            'distance':self.distance,
            'action':self.action,
            'score':self.score
        })

    def close(self):
        print("close")
        #self.arduino.close()

if __name__ == "__main__":
    env = ArduinoEnv()
    done = False
    while not done:
        action = input("Action: ")
        observation, score, done, _ = env.step([action])
        env.render()
