# Original Sources: 
# * https://github.com/harvitronix/reinforcement-learning-car
# * https://github.com/keon/deep-q-learning

from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

import random
import math
import numpy as np
from datetime import datetime

import pygame
from pygame.color import THECOLORS

import pymunk
from pymunk.vec2d import Vec2d
import pymunk.pygame_util

EPISODES = 1000

class GameState:
    def __init__(self):

        # Physics stuff.
        self.width = 1280
        self.height = 980
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0.0, 0.0)

        # Create walls.
        self._add_boundaries()

        # Create some obstacles, semi-randomly.
        # We'll create three and they'll move around to prevent over-fitting.
        self.obstacles = []
        self.obstacles.append(self.create_obstacle(100, 350, 20))
        self.obstacles.append(self.create_obstacle(700, 200, 30))
        self.obstacles.append(self.create_obstacle(600, 660, 50))
        self.obstacles.append(self.create_obstacle(900, 900, 50))

        self.create_fourLegs_obstacles(300, 800, 120, 120)
        self.create_fourLegs_obstacles(450, 800, 120, 120)
        self.create_fourLegs_obstacles(600, 800, 120, 120)
        self.create_fourLegs_obstacles(750, 800, 120, 120)

        self.create_fourLegs_obstacles(500, 100, 300, 300)
        self.create_fourLegs_obstacles(820, 100, 300, 300)

        # Create Car
        self.create_car(100, 100, 0.5)

        # ML stuff.
        self.score = 0
        self.crashed = False
    
    def create_fourLegs_obstacles(self, x, y, width, height):
        self.obstacles.append(self.create_obstacle(x, y, 10))
        self.obstacles.append(self.create_obstacle(x, y+height, 10))
        self.obstacles.append(self.create_obstacle(x+width, y, 10))
        self.obstacles.append(self.create_obstacle(x+width, y+height, 10))

    def create_car(self, x, y, r):
        inertia = pymunk.moment_for_circle(1.0, 0.0, 25.0, (0.0, 0.0))
        self.car_body = pymunk.Body(1, inertia)
        self.car_body.position = x, y
        self.car_shape = pymunk.Circle(self.car_body, 25.0)
        self.car_shape.color = THECOLORS["green"]
        self.car_shape.elasticity = 1.0
        self.car_body.angle = r
        driving_direction = Vec2d(1.0, 0.0).rotated(self.car_body.angle)
        self.car_body.apply_impulse_at_local_point(driving_direction, (0.0,0.0))
        self.space.add(self.car_body, self.car_shape)

    def reset_env(self):
        self.score = 0
        self.crashed = False
        self.car_body.position = 100, 100 # /!\ todo: define globals
        self.car_body.angle = 0.5
        driving_direction = Vec2d(1.0, 0.0).rotated(self.car_body.angle)
        self.car_body.apply_impulse_at_local_point(driving_direction, (0.0,0.0))

    def _add_boundaries(self):
        """
        Create the static bodies.
        :return: None
        """
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
            self.score -= 1
        elif action == 1:  # Turn right.
            self.car_body.angle += 0.2
            self.score -= 1
        else:
            self.score += 5

        driving_direction = Vec2d(1, 0).rotated(self.car_body.angle)
        self.car_body.velocity = 50 * driving_direction

        # Update the screen and stuff.
        screen.fill(THECOLORS["black"])
        self.space.debug_draw(draw_options)
        self.space.step(1./2)
        pygame.display.flip()
        clock.tick()

        # Get the current location and the readings there.
        readings = self.get_sonar_readings()

        # Handle car crash
        if self.car_is_crashed(readings):
            self.crashed = True
            self.score = -500
            #self.recover_from_crash(driving_direction)
        
        return readings, self.score, self.crashed

    def get_sonar_readings(self):
        x, y  = self.car_body.position
        angle = self.car_body.angle
        readings = []

        # Make our arms.
        arm_left_e = self.make_sonar_arm(x, y)
        arm_left_i = arm_left_e
        arm_middle = arm_left_e
        arm_right_i = arm_left_e
        arm_right_e = arm_left_e

        # Rotate them and get readings.
        readings.append(self.get_arm_distance(arm_left_e, x, y, angle, 0.80))
        readings.append(self.get_arm_distance(arm_left_i, x, y, angle, 0.40))
        readings.append(self.get_arm_distance(arm_middle, x, y, angle, 0))
        readings.append(self.get_arm_distance(arm_right_i, x, y, angle, -0.40))
        readings.append(self.get_arm_distance(arm_right_e, x, y, angle, -0.80))

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
        # Make an arm. We build it flat because we'll rotate it about the
        # center later.
        for i in range(1, 40):
            arm_points.append((distance + x + (spread * i), y))

        return arm_points

    def car_is_crashed(self, readings):
        if readings[0] == 1 or readings[1] == 1 or readings[2] == 1:
            return True
        else:
            return False

    def recover_from_crash(self, driving_direction):
        """
        We hit something, so recover.
        """
        while self.crashed:
            # Go backwards.
            self.car_body.velocity = -100 * driving_direction
            self.crashed = False
            for i in range(10):
                self.car_body.angle += .2  # Turn a little.
                screen.fill(THECOLORS["grey7"])  # Red is scary!
                self.space.debug_draw(draw_options)
                self.space.step(1./10)
                pygame.display.flip()
                clock.tick()

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
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(6, input_dim=self.state_size, activation='relu'))
        model.add(Dense(4, activation='relu'))
        model.add(Dense(self.action_size, activation='sigmoid'))
        model.compile(loss='mse',
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
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
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Turn off alpha since we don't use it.
    screen.set_alpha(None)

    # Create agent
    done = False
    batch_size = 32
    agent = DQNAgent(5, 3)
    run = True

    for e in range(EPISODES):
        game_state.reset_env()
        state = game_state.get_sonar_readings()
        state = np.reshape(state, [1, 5])
        for time in range(500):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        run = False

            action = agent.act(state)
            next_state, reward, done = game_state.frame_step(action)
            next_state = np.reshape(next_state, [1, 5])
            #print(reward, done)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            if done:
                print("episode: {}/{}, score: {}, e: {:.2}"
                      .format(e, EPISODES, time, agent.epsilon))
                break
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
    pygame.quit()
