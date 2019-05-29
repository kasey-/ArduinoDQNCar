import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial

PI = 3.14159265

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.arduino = serial.Serial()
        self.obs   = [0.0, 0.0, 0.0, 0.0]
        self.score = 0.0
        self.done  = False

        self.theta_threshold_radians = 12 * 2 * PI / 360
        self.x_threshold = 2.4
        high = np.array([
            self.x_threshold * 2,
            np.finfo(np.float32).max,
            self.theta_threshold_radians * 2,
            np.finfo(np.float32).max])
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        self.seed()

    def connect_to(self, serial, baudrate=115200):
        self.arduino.baudrate = baudrate
        self.arduino.port = serial
        self.arduino.open()
        self.arduino.flush()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.arduino.write(b'2')
        _ = self.arduino.readline()
        return np.array(self.np_random.uniform(low=-0.05, high=0.05, size=(4,)))

    def step(self, action):
        self.action = "{}".format(action).encode('ascii')
        self.arduino.write(self.action)
        _answer = self.arduino.readline()
        _answer = _answer.decode('ascii').strip().split(',')
        self.obs   = np.array(_answer[:4],dtype=float)
        self.score = float(_answer[4])
        self.done  = bool(int(_answer[5]))
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
    env.connect_to('/dev/tty.usbmodemFA141')
    done = False
    while not done:
        action = input("Action: ")
        env.step(action)
        env.render()
