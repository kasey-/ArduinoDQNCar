import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.arduino = serial.Serial()
        self.obs   = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.score = 0.0
        self.done  = False

        low  = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        high = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        self.seed()

    def connect_to(self, serial, baudrate=115200, timeout=5.0):
        self.arduino.baudrate = baudrate
        self.arduino.timeout = timeout
        self.arduino.port = serial
        self.arduino.open()
        self.arduino.flush()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.done = False
        self.arduino.write(b'-1')
        _answer = self.arduino.readline()
        _answer = _answer.decode('ascii').strip().split(',')
        return np.array(_answer)

    def step(self, action):
        self.action = "{}".format(action).encode('ascii')
        self.arduino.write(self.action)
        _answer = self.arduino.readline()
        _answer = _answer.decode('ascii').strip().split(',')
        self.obs   = np.array(_answer[:5],dtype=float)
        self.score = float(_answer[5])
        if self.score == -500.0:
            self.done  = True
        return self.obs, self.score, self.done, {}

    def render(self, mode='human'):
        print({
            'action':self.action,
            'obs':self.obs,
            'score':self.score,
            'done':self.done
        })

    def close(self):
        self.arduino.close()

if __name__ == "__main__":
    env = ArduinoEnv()
    env.connect_to('/dev/tty.HC-06-DevB')
    done = False
    while not done:
        action = input("Action: ")
        env.step(action)
        env.render()
