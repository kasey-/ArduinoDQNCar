import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.action_space = spaces.Box(low=0, high=1000, shape=(1,), dtype=np.int32)
        self.observation_space = spaces.Box(low=0, high=1000, shape=(1,), dtype=np.int32)
        self.arduino = serial.Serial('/dev/tty.usbmodemFA141', 115200)
        self.seed()
        self.reset()
    
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.obs = 500
        return self.obs

    def step(self, action):
        self.arduino.write(str(int(action)).encode('ascii'))
        self.pobs  = self.obs
        _result = self.arduino.readline()
        _obs, _score, _done = _result.decode('ascii').rstrip().split(',')
        self.obs   = int(_obs)
        self.score = int(_score)
        self.done  = bool(_done)
        return self.obs, self.score, self.done, {}

    def render(self, mode='human'):
        print(self.pobs, self.obs, self.score, self.done)

    def close(self):
        self.arduino.close()