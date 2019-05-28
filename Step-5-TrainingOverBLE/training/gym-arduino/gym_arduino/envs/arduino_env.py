import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial
import random

MINIMUM = 100
MAXIMUM = 900
SAFE    = 100
CUSRSOR = 500

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.action_space = spaces.Box(low=np.array([-1000]), high=np.array([1000]), dtype=np.int32)
        self.observation_space = spaces.Box(low=np.array([-1000]), high=np.array([1000]), dtype=np.int32)
        self.seed()
        self.reset()
    
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.life = 10
        self.score = 0
        self.done = False
        self.cursor = random.randint(CUSRSOR-SAFE, CUSRSOR+SAFE)
        self.target = random.randint(MINIMUM-SAFE, MAXIMUM+SAFE)
        self.distance = self.target - self.cursor
        return [self.distance]

    def step(self, action):
        print(action)
        self.score = 0
        self.done = False
        self.prev_distance = self.distance
        self.cursor += int(action)
        self.distance = self.target - self.cursor
        # compute reward
        # Check if still alive
        if self.life == 0:
            self.done = True
            self.score = -1000
        # Check if we are outside of range
        elif((self.cursor < MINIMUM) or (self.cursor > MAXIMUM)):
            self.done = True
            self.score = -100
        # Check if we are on the target
        elif (self.cursor == self.target):
            self.done = True
            self.score = 1000
        # If not dead nor on the spot we compute the score
        else:
            self.score = self.distance - self.prev_distance
        #print(self.distance, self.score, self.done, self.life)
        self.life -= 1
        return [self.distance], self.score, self.done, {}

    def render(self, mode='human'):
        print(self.prev_distance, self.distance, self.score, self.done)

    def close(self):
        print("close")
        #self.arduino.close()