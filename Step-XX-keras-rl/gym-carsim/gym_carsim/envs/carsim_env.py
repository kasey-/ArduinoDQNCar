# Sources:
# * https://github.com/openai/gym/blob/master/docs/creating-environments.md
# * https://gist.github.com/iandanforth/bbce05af83fb482f4ffc3fb8570fe50d

import gym
from gym import error, spaces, utils
from gym.utils import seeding

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

class CarSimEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        # Pygame and display setup
        self.screen = None
        self.draw_options = None
        self.screen_width = 1280
        self.screen_height = 980
        self.clock = pygame.time.Clock()
        self.seed()

        # Physics stuff.
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0.0, 0.0)
        handler = self.space.add_default_collision_handler()
        handler.begin = self._handle_collision

        # Create walls.
        self._create_boundaries()

        # Create some obstacles, semi-randomly.
        # We'll create three and they'll move around to prevent over-fitting.
        self.obstacles = []
        self.obstacles.append(self._create_obstacle(100, 350, 20))
        self.obstacles.append(self._create_obstacle(700, 200, 30))
        self.obstacles.append(self._create_obstacle(600, 660, 50))
        self.obstacles.append(self._create_obstacle(950, 900, 50))

        self._create_fourLegs_obstacles(300, 800, 120, 120)
        self._create_fourLegs_obstacles(450, 800, 120, 120)
        self._create_fourLegs_obstacles(600, 800, 120, 120)
        self._create_fourLegs_obstacles(750, 800, 120, 120)

        self._create_fourLegs_obstacles(500, 100, 300, 300)
        self._create_fourLegs_obstacles(820, 100, 300, 300)

        # Create Car
        self.car_init_x = 1000
        self.car_init_y = 600
        self.car_init_r = 3.1456/2
        self._create_car()

        # ML stuff.
        self.score = 0
        self.crashed = False

    def _handle_collision(self, arbiter, space, data):
            self.crashed = True
            self.score -= PENALTY_CRASH
            return True

    def _create_fourLegs_obstacles(self, x, y, width, height):
        self.obstacles.append(self._create_obstacle(x, y, 10))
        self.obstacles.append(self._create_obstacle(x, y+height, 10))
        self.obstacles.append(self._create_obstacle(x+width, y, 10))
        self.obstacles.append(self._create_obstacle(x+width, y+height, 10))

    def _create_car(self):
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

    def _create_boundaries(self):
        static_body = self.space.static_body
        static_lines = [pymunk.Segment(static_body, (1.0, 1.0), (self.width-1, 1.0),  1.0),
                        pymunk.Segment(static_body, (1.0, 1.0), (1.0, self.height-1), 1.0),
                        pymunk.Segment(static_body, (1.0, self.height-1), (self.width-1, self.height-1), 1.0),
                        pymunk.Segment(static_body, (self.width-1, 1.0),  (self.width-1, self.height-1), 1.0)]
        for line in static_lines:
            line.elasticity = 1.0
            line.friction = 0.0
        self.space.add(static_lines)

    def _create_obstacle(self, x, y, r):
        c_body = pymunk.Body(10000000, pymunk.inf)
        c_shape = pymunk.Circle(c_body, r)
        c_shape.elasticity = 1.0
        c_body.position = x, y
        c_shape.color = THECOLORS["blue"]
        self.space.add(c_body, c_shape)
        return c_body

    def _get_sonar_readings(self):
        x, y = self.car_body.position
        angle = self.car_body.angle
        readings = []
        readings_tmp = []

        # Make our arm
        arm = self._make_sonar_arm(x, y)

        # Rotate them and get readings.
        pi = 3.14159265359
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  pi/2.5))    # 0
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  pi/3.0))    # 1
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  pi/4.0))    # 2
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  pi/6.0))    # 3
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  pi/13.0))   # 4
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  0.0))       # 5
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  -pi/13.0))  # 6
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  -pi/6.0))   # 7
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  -pi/4.0))   # 8
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  -pi/3.0))   # 9
        readings_tmp.append(self._get_arm_distance(arm,  x, y, angle,  -pi/2.5))   # 10

        readings.append(np.min(readings_tmp[0:3])/39.0)
        readings.append(np.min(readings_tmp[2:5])/39.0)
        readings.append(np.min(readings_tmp[4:7])/39.0)
        readings.append(np.min(readings_tmp[6:9])/39.0)
        readings.append(np.min(readings_tmp[8:])/39.0)

        #if self.render:
        #    pygame.display.update()

        return readings

    def _get_arm_distance(self, arm, x, y, angle, offset):
        i = 0
        for point in arm:
            i += 1
            rotated_p = self._get_rotated_point(
                x, y, point[0], point[1], angle + offset
            )
            if rotated_p[0] <= 0 or rotated_p[1] <= 0 \
                    or rotated_p[0] >= self.width or rotated_p[1] >= self.height:
                return i  # Sensor is off the screen.
            else:
                obs = screen.get_at(rotated_p)
                if self._get_track_or_not(obs) != 0:
                    return i
            pygame.draw.circle(screen, (255, 255, 255), (rotated_p), 2)
        return i

    def _make_sonar_arm(self, x, y):
        spread = 10  # Default spread.
        distance = 20  # Gap before first sensor.
        arm_points = []
        # Make an arm. We build it flat because we'll rotate it about the center later.
        for i in range(1, 40):
            arm_points.append((distance + x + (spread * i), y))

        return arm_points

    def _get_rotated_point(self, x_1, y_1, x_2, y_2, radians):
        # Rotate x_2, y_2 around x_1, y_1 by angle.
        x_change = (x_2 - x_1) * math.cos(radians) + \
            (y_2 - y_1) * math.sin(radians)
        y_change = (y_1 - y_2) * math.cos(radians) - \
            (x_1 - x_2) * math.sin(radians)
        new_x = x_change + x_1
        new_y = self.height - (y_change + y_1)
        return int(new_x), int(new_y)

    def _get_track_or_not(self, reading):
        if reading == THECOLORS['black']:
            return 0
        else:
            return 1

    def reset(self):
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

    def step(self, action):
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
        #if self.render:
        #    pygame.display.flip()
        clock.tick()

        # Get the current location and the readings there.
        readings = self._get_sonar_readings()
        for r in readings:
            self.score += (r - PENALTY_DIST) / 5.0
            #print("Reading penalty {}".format(r/39.0 - 1))

        return readings, self.score, self.crashed

    def render(self, mode='human'):
        if self.screen == None:
            print('Setting up screen')
            pygame.init()
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height)
            )
            pygame.display.set_caption("Gym CarSim")
            # Debug draw setup (called in render())
            self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
            self.draw_options.flags = 3
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()

    def close(self):
        pygame.quit()

