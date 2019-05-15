# Original source: https://github.com/harvitronix/reinforcement-learning-car

import random
import math
import numpy as np
from datetime import datetime

import pygame
from pygame.color import THECOLORS

import pymunk
from pymunk.vec2d import Vec2d
import pymunk.pygame_util

class GameState:
    def __init__(self):
        # Physics stuff.
        self.width  = 1280
        self.height = 980
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0.0, 0.0)

        # Create walls.
        self.create_boundaries()

        # Create some obstacles, semi-randomly.
        self.obstacles = []
        self.obstacles.append(self.create_obstacle(100, 350, 20))
        self.obstacles.append(self.create_obstacle(700, 200, 30))
        self.obstacles.append(self.create_obstacle(600, 660, 50))
        self.obstacles.append(self.create_obstacle(900, 900, 50))

        # create four chairs in line
        self.create_fourLegs_obstacles(300, 800, 120, 120)
        self.create_fourLegs_obstacles(450, 800, 120, 120)
        self.create_fourLegs_obstacles(600, 800, 120, 120)
        self.create_fourLegs_obstacles(750, 800, 120, 120)

        # create sofa
        self.create_fourLegs_obstacles(500, 100, 300, 300)
        self.create_fourLegs_obstacles(820, 100, 300, 300)

        # Create Car
        self.car_init_x = 100
        self.car_init_y = 100
        self.car_init_r = 0.5
        self.create_car(self.car_init_x, self.car_init_y, self.car_init_r)

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
            self.score -= 0.2
        elif action == 1:  # Turn right.
            self.car_body.angle += 0.2
            self.score -= 0.2
        else:
            self.score += 10

        driving_direction = Vec2d(1, 0).rotated(self.car_body.angle)
        self.car_body.velocity = 50 * driving_direction

        # Update the screen and stuff.
        screen.fill(THECOLORS["black"])
        self.space.debug_draw(draw_options)
        self.space.step(1./25)
        pygame.display.flip()
        clock.tick()

        # Get the current location and the readings there.
        readings = self.get_sonar_readings()

        # Handle car crash
        if self.car_is_crashed(readings):
            self.crashed = True
            self.score = -500
            self.recover_from_crash(driving_direction)
        
        return self.score, readings

    def get_sonar_readings(self):
        x, y = self.car_body.position
        angle = self.car_body.angle
        readings = []

        # Make our arms.
        arm_left_e = self.make_sonar_arm(x, y)
        arm_left_i = arm_left_e
        arm_middle = arm_left_e
        arm_right_i = arm_left_e
        arm_right_e = arm_left_e

        # Rotate them and get readings.
        readings.append(self.get_arm_distance(arm_left_e, x, y, angle, 0.60))
        readings.append(self.get_arm_distance(arm_left_i, x, y, angle, 0.30))
        readings.append(self.get_arm_distance(arm_middle, x, y, angle, 0))
        readings.append(self.get_arm_distance(arm_right_i, x, y, angle, -0.30))
        readings.append(self.get_arm_distance(arm_right_e, x, y, angle, -0.60))

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
        spread = 10     # Default spread.
        distance = 20   # Gap before first sensor.
        arm_points = []
        for i in range(1, 35):
            arm_points.append((distance + x + (spread * i), y))
        return arm_points

    def car_is_crashed(self, readings):
        for r in readings:
            if r == 1:
                return True
        return False

    def recover_from_crash(self, driving_direction):
        while self.crashed:
            # Go backwards.
            self.car_body.velocity = -100 * driving_direction
            self.crashed = False
            for i in range(10):
                self.car_body.angle += .2           # Turn a little.
                screen.fill(THECOLORS["grey7"])     # Red is scary!
                self.space.debug_draw(draw_options)
                self.space.step(1./10)
                pygame.display.flip()
                clock.tick()

    def get_rotated_point(self, x_1, y_1, x_2, y_2, radians):
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

if __name__ == "__main__":
    game_state = GameState()
    # PyGame init
    pygame.init()
    screen = pygame.display.set_mode((game_state.width, game_state.height))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Turn off alpha since we don't use it.
    screen.set_alpha(None)
    run = True
    while run:
        action = 2
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_RIGHT:
                    action = 0 
                elif event.key == pygame.K_LEFT:
                    action = 1
        print(game_state.frame_step(action))
    pygame.quit()
