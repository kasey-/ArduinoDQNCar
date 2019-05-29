import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import serial

class ArduinoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.arduino = serial.Serial()
        self.obs   = [0.0, 0.0, 0.0, 0.0]
        self.score = 0.0
        self.done  = False
        self.seed()

    def connect_to(self, serial, baudrate=9600):
        self.arduino.baudrate = baudrate
        self.arduino.port = serial
        self.arduino.open()
        self.arduino.flush()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self):
        self.arduino.write(b'2')
        answer = self.arduino.readline()
        print(answer)
        #return [obs]

    def step(self, action):
        _cmd = "{}".format(action).encode('ascii')
        print(_cmd)
        self.arduino.write(_cmd)
        _answer = self.arduino.readline()
        print(_answer)
        _answer = _answer.decode('ascii').strip().split(',')
        print(_answer)
        self.obs   = np.array(_answer[:4],dtype=float)
        self.score = float(_answer[4])
        self.done  = bool(int(_answer[5]))
        return self.obs, self.score, self.done, {}

    def render(self, mode='human'):
        print({
            'obs':self.obs,
            'score':self.score,
            'done':self.done
        })

    def close(self):
        self.arduino.close()

if __name__ == "__main__":
    env = ArduinoEnv()
    env.connect_to('COM4')
    done = False
    while not done:
        action = input("Action: ")
        env.step(action)
        env.render()
