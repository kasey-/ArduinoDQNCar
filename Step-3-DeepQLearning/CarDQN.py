# Original Sources: 
# * https://github.com/harvitronix/reinforcement-learning-car
# * https://github.com/keon/deep-q-learning

from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K
import time

import random
import math
import numpy as np
from datetime import datetime

import pygame
from pygame.color import THECOLORS

import pymunk
from pymunk.vec2d import Vec2d
import pymunk.pygame_util

PENALTY_TURN  = 0.8
PENALTY_DIST  = 0.7
PENALTY_CRASH = 500.0
BONUS_MOVE    = 0.5
BATCH_SIZE    = 128

EPISODES = 10000
STEPS    = 500

class GameState:
    def __init__(self):

        # Physics stuff.
        self.render = True
        self.width = 1280
        self.height = 980
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0.0, 0.0)
        handler = self.space.add_default_collision_handler()
        handler.begin = self.handle_collision

        # Create walls.
        self.create_boundaries()

        # Create some obstacles, semi-randomly.
        # We'll create three and they'll move around to prevent over-fitting.
        self.obstacles = []
        self.obstacles.append(self.create_obstacle(100, 350, 20))
        self.obstacles.append(self.create_obstacle(700, 200, 30))
        self.obstacles.append(self.create_obstacle(600, 660, 50))
        self.obstacles.append(self.create_obstacle(950, 900, 50))

        self.create_fourLegs_obstacles(300, 800, 120, 120)
        self.create_fourLegs_obstacles(450, 800, 120, 120)
        self.create_fourLegs_obstacles(600, 800, 120, 120)
        self.create_fourLegs_obstacles(750, 800, 120, 120)

        self.create_fourLegs_obstacles(500, 100, 300, 300)
        self.create_fourLegs_obstacles(820, 100, 300, 300)

        # Create Car
        self.car_init_x = 1000
        self.car_init_y = 600
        self.car_init_r = 3.1456/2
        self.create_car()

        # ML stuff.
        self.score = 0
        self.crashed = False

    def handle_collision(self, arbiter, space, data):
            self.crashed = True
            self.score -= PENALTY_CRASH
            return True

    def create_fourLegs_obstacles(self, x, y, width, height):
        self.obstacles.append(self.create_obstacle(x, y, 10))
        self.obstacles.append(self.create_obstacle(x, y+height, 10))
        self.obstacles.append(self.create_obstacle(x+width, y, 10))
        self.obstacles.append(self.create_obstacle(x+width, y+height, 10))

    def create_car(self):
        inertia = pymunk.moment_for_circle(1.0, 0.0, 25.0, (0.0, 0.0))
        self.car_body = pymunk.Body(1, inertia)
        self.car_body.position = self.car_init_x, self.car_init_y
        self.car_shape = pymunk.Circle(self.car_body, 25.0)
        self.car_shape.color = THECOLORS["green"]
        self.car_shape.elasticity = 1.0
        self.car_body.angle = self.car_init_r
        driving_direction = Vec2d(1.0, 0.0).rotated(self.car_body.angle)
        self.car_body.apply_impulse_at_local_point(driving_direction, (0.0,0.0))
        self.space.add(self.car_body, self.car_shape)

    def reset_env(self):
        # random pop
        pop_sites = [[300,300],[200,500],[1000,600]]
        pop_site = random.choice(pop_sites)

        new_x = pop_site[0] + random.randrange(-100, +100, 1)
        new_y = pop_site[1] + random.randrange(-100, +100, 1)
        new_r = random.randrange(-31456, 31456) / 10000.0

        self.score = 0
        self.crashed = False
        self.car_body.position = new_x, new_y
        self.car_body.angle = new_r
        driving_direction = Vec2d(1.0, 0.0).rotated(self.car_body.angle)
        self.car_body.apply_impulse_at_local_point(driving_direction, (0.0,0.0))

    def create_boundaries(self):
        static_body = self.space.static_body
        static_lines = [pymunk.Segment(static_body, (1.0, 1.0), (self.width-1, 1.0),  1.0),
                        pymunk.Segment(static_body, (1.0, 1.0), (1.0, self.height-1), 1.0),
                        pymunk.Segment(static_body, (1.0, self.height-1), (self.width-1, self.height-1), 1.0),
                        pymunk.Segment(static_body, (self.width-1, 1.0),  (self.width-1, self.height-1), 1.0)]
        for line in static_lines:
            line.elasticity = 1.0
            line.friction = 0.0
        self.space.add(static_lines)

    def create_obstacle(self, x, y, r):
        c_body = pymunk.Body(10000000, pymunk.inf)
        c_shape = pymunk.Circle(c_body, r)
        c_shape.elasticity = 1.0
        c_body.position = x, y
        c_shape.color = THECOLORS["blue"]
        self.space.add(c_body, c_shape)
        return c_body

    def frame_step(self, action):
        if action == 0:  # Turn left.
            self.car_body.angle -= 0.2
            self.score -= PENALTY_TURN
        elif action == 1:  # Turn right.
            self.car_body.angle += 0.2
            self.score -= PENALTY_TURN
        else:
            self.score += BONUS_MOVE

        driving_direction = Vec2d(1, 0).rotated(self.car_body.angle)
        self.car_body.velocity = 50 * driving_direction

        # Update the screen and stuff.
        screen.fill(THECOLORS["black"])
        self.space.debug_draw(draw_options)
        self.space.step(1./10.0)
        if self.render:
            pygame.display.flip()
        clock.tick()

        # Get the current location and the readings there.
        readings = self.get_sonar_readings()
        for r in readings:
            self.score += (r - PENALTY_DIST) / 5.0
            #print("Reading penalty {}".format(r/39.0 - 1))

        return readings, self.score, self.crashed

    def get_sonar_readings(self):
        x, y = self.car_body.position
        angle = self.car_body.angle
        readings = []
        readings_tmp = []

        # Make our arm
        arm = self.make_sonar_arm(x, y)

        # Rotate them and get readings.
        pi = 3.14159265359
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  pi/2.5))    # 0
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  pi/3.0))    # 1
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  pi/4.0))    # 2
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  pi/6.0))    # 3
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  pi/13.0))   # 4
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  0.0))       # 5
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  -pi/13.0))  # 6
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  -pi/6.0))   # 7
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  -pi/4.0))   # 8
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  -pi/3.0))   # 9
        readings_tmp.append(self.get_arm_distance(arm,  x, y, angle,  -pi/2.5))   # 10

        readings.append(np.min(readings_tmp[0:3])/39.0)
        readings.append(np.min(readings_tmp[2:5])/39.0)
        readings.append(np.min(readings_tmp[4:7])/39.0)
        readings.append(np.min(readings_tmp[6:9])/39.0)
        readings.append(np.min(readings_tmp[8:])/39.0)

        if self.render:
            pygame.display.update()

        return readings

    def get_arm_distance(self, arm, x, y, angle, offset):
        i = 0
        for point in arm:
            i += 1
            rotated_p = self.get_rotated_point(
                x, y, point[0], point[1], angle + offset
            )
            if rotated_p[0] <= 0 or rotated_p[1] <= 0 \
                    or rotated_p[0] >= self.width or rotated_p[1] >= self.height:
                return i  # Sensor is off the screen.
            else:
                obs = screen.get_at(rotated_p)
                if self.get_track_or_not(obs) != 0:
                    return i
            pygame.draw.circle(screen, (255, 255, 255), (rotated_p), 2)
        return i

    def make_sonar_arm(self, x, y):
        spread = 10  # Default spread.
        distance = 20  # Gap before first sensor.
        arm_points = []
        # Make an arm. We build it flat because we'll rotate it about the center later.
        for i in range(1, 40):
            arm_points.append((distance + x + (spread * i), y))

        return arm_points

    def get_rotated_point(self, x_1, y_1, x_2, y_2, radians):
        # Rotate x_2, y_2 around x_1, y_1 by angle.
        x_change = (x_2 - x_1) * math.cos(radians) + \
            (y_2 - y_1) * math.sin(radians)
        y_change = (y_1 - y_2) * math.cos(radians) - \
            (x_1 - x_2) * math.sin(radians)
        new_x = x_change + x_1
        new_y = self.height - (y_change + y_1)
        return int(new_x), int(new_y)

    def get_track_or_not(self, reading):
        if reading == THECOLORS['black']:
            return 0
        else:
            return 1


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0   # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995
        self.learning_rate = 0.01
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(32, input_dim=self.state_size, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='logcosh', optimizer=Adam(lr=self.learning_rate))
        return model

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        #print(state, np.argmax(act_values[0]), act_values[0])
        out = [0.5,0.5]
        if np.argmax(act_values[0]) == 0:
            out = [1.0,0.5]
        elif np.argmax(act_values[0]) == 1:
            out = [0.5,1.0]
        else:
            out = [1.0,1.0]
        #print(state[0][0],state[0][1],state[0][2],state[0][3],state[0][4], 0.0, 0.0, out[0], out[1])
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = self.model.predict(state)
            if done:
                target[0][action] = reward
            else:
                t = self.target_model.predict(next_state)[0]
                target[0][action] = reward + self.gamma * np.amax(t)
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

if __name__ == "__main__":
    game_state = GameState()
    # PyGame init
    pygame.init()
    screen = pygame.display.set_mode((game_state.width, game_state.height))
    clock  = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Turn off alpha since we don't use it.
    screen.set_alpha(None)

    # Create agent
    batch_size  = BATCH_SIZE
    input_size  = 5
    output_size = 3
    done  = False
    agent = DQNAgent(input_size, output_size)
    agent.load("models/990_113-t1.model")
    agent.epsilon = 0.2

    for e in range(EPISODES):
        game_state.reset_env()
        state = game_state.get_sonar_readings()
        state = np.reshape(state, [1, input_size])
        survived = True
        for s in range(STEPS):            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        quit()
                    if event.key == pygame.K_r:
                        game_state.render = False if game_state.render else True
                    if event.key == pygame.K_s:
                        agent.save("models/{}.model".format(e))
                    if event.key == pygame.K_f:
                        time.sleep(30)

            action = agent.act(state)
            next_state, reward, done = game_state.frame_step(action)
            next_state = np.reshape(next_state, [1, input_size])
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            if done:
                agent.update_target_model()
                if s == 0:
                    s = 1
                print("{}\t{}\t{}\t{:.2f}\t{:.2}\tcrash"
                      .format(e, int(reward), s, float(reward/s), agent.epsilon))
                survived = False
                break
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
        if survived:
            s = STEPS
            print("{}\t{}\t{}\t{:.2f}\t{:.2}"
                    .format(e, int(reward), s, float(reward/s), agent.epsilon))
        if e % 10 == 0:
            agent.save("models/{}_{}.model".format(e, int(reward)))
