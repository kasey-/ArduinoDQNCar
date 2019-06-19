import pyglet
import pymunk
from pymunk.pyglet_util import DrawOptions
from pymunk.vec2d import Vec2d

import numpy as np
import random

import gym
from gym import error, spaces, utils
from gym.utils import seeding

class UltrasonicSensor:
    def __init__(self, space, car, offset=0, angle=0, color=(0,255,0,255)):
        self.space = space
        self.car = car
        self.offset = offset
        self.angle = angle
        self.color = color
        self.fov = 60
        self.spread = 2
        self.range = 100

    def sense(self):
        fov = int(self.fov/2)
        car_x, car_y = self.car.body.position
        car_top = Vec2d(0.0, self.car.height/2.0).rotated(self.car.body.angle)
        offset  = Vec2d(self.offset, 1.0).rotated(self.car.body.angle)
        car_x += car_top.x + offset.x
        car_y += car_top.y + offset.y
        distances = []
        for angle in range(-fov+self.angle, fov+self.angle, self.spread):
            ray, distance = self._create_ray(car_x, car_y, angle)
            distances.append(distance)
            self.space.add(ray)
        return np.min(distances)
    
    def _create_ray(self, a_x, a_y, angle):
        kinematic = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        b_x, b_y = Vec2d(0.0, self.range).rotated(self.car.body.angle).rotated_degrees(angle)
        ray = pymunk.Segment(kinematic, (a_x, a_y), (a_x+b_x, a_y+b_y), 1.0)
        ray.position = (a_x, a_y)
        ray.color = self.color
        ray.is_a_ray = True
        hits = self.space.segment_query(ray.a, ray.b, 1.0, pymunk.ShapeFilter())
        distance = [self.range]
        for hit in hits:
            if hasattr(hit.shape, 'is_sensed'):
                x = abs(hit.point.x - ray.a.x)
                y = abs(hit.point.y - ray.a.y)
                distance.append(Vec2d(x, y).get_length())
        return ray, np.min(distance) / self.range

    def _clear_rays(self):
        for shape in self.space.shapes:
            if hasattr(shape, 'is_a_ray'):
                self.space.remove(shape)

class Car:
    def __init__(self, space, pop=(500, 200), angle=0):
        self.height = 50
        self.width = 38
        self.velocity = 50.0
        self.steering_angle = 0.2
        self.is_crashed = False
        _size = (self.width,self.height)
        _mass = 1.0
        _inertia = pymunk.moment_for_box(_mass, _size)
        
        self.space = space
        self.body = pymunk.Body(_mass, _inertia)
        self.reset_body(pop, angle)
        self.shape = pymunk.Poly.create_box(self.body, size=_size)
        self.shape.elasticity = 1.0
        self.space.add(self.body, self.shape)

        self.collision_handler = self.space.add_default_collision_handler()       
        self.collision_handler.begin = self._handle_collision

        self.sensors = []
        self.sensors.append(UltrasonicSensor(self.space, self, -10,  45, (0, 255, 0, 200)))
        self.sensors.append(UltrasonicSensor(self.space, self,   0,   0, (255, 0, 0, 200)))
        self.sensors.append(UltrasonicSensor(self.space, self,  10, -45, (0, 0, 255, 200)))
   
    def reset_body(self, pop, angle):
        self.is_crashed = False
        self.body.position = pop
        self.body.angle = angle
        self.body.velocity = Vec2d(0.0, self.velocity)
        self.body.angular_velocity = 0.0
    
    def read_sensors(self):
        distances = []
        for sensor in self.sensors:
            distances.append(sensor.sense())
        return distances

    def cmd(self,cmd):
        if cmd == 0:    # Turn left.
            self.body.angle += self.steering_angle
        elif cmd == 1:  # Turn right.
            self.body.angle -= self.steering_angle
        
        direction = Vec2d(0, self.velocity).rotated(self.body.angle)
        self.body.velocity = direction

    def _handle_collision(self, arbiter, space, data):
        self.is_crashed = True
        return True

class Obstacle:
    def __init__(self, space, pos, radius):
        body = space.static_body
        body.position = pos
        obs = pymunk.Circle(space.static_body, radius)
        obs.is_sensed = True
        space.add(obs)

class FourLegsObstacle:
    def __init__(self, space, pos, width, height, radius):
        _pos = np.array(pos)
        Obstacle(space, _pos + (0,     0),      radius)
        Obstacle(space, _pos + (0,     height), radius)
        Obstacle(space, _pos + (width, 0),      radius)
        Obstacle(space, _pos + (width, height), radius)

class CarSimEnv(gym.Env):
    def __init__(self):
        self.width  = 1280
        self.height = 720
        self.window = pyglet.window.Window(self.width, self.height, "Car Simulator", resizable=False)
        self.draw_options = DrawOptions()

        self.seed()
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(3,), dtype=np.float32)

        self.space = pymunk.Space()
        self.space.gravity = Vec2d(0.0, 0.0)

        self._create_boundaries()
        self.car = Car(self.space)

        Obstacle(self.space, ( 300, 300), 50)
        Obstacle(self.space, ( 250, 630), 80)
        Obstacle(self.space, (1200, 600), 90)

        FourLegsObstacle(self.space, ( 700, 400), 200, 200, 15)
        
        FourLegsObstacle(self.space, ( 800,  50), 100, 100, 10)
        FourLegsObstacle(self.space, ( 920,  50), 100, 100, 10)
        FourLegsObstacle(self.space, (1040,  50), 100, 100, 10)

        def on_key_press(symbol, modifiers):
            #if symbol == pyglet.window.key.LEFT:
            #    self.car.cmd(0)
            #elif symbol == pyglet.window.key.RIGHT:
            #    self.car.cmd(1)
            #elif symbol == pyglet.window.key.UP:
            #    self.car.cmd(2)
            if symbol == pyglet.window.key.ESCAPE:
                pyglet.app.exit()
                quit()
            #update(0.2)

        #def on_draw():
        #    self.window.clear()
        #    self.space.debug_draw(self.draw_options)

        #def update(dt):
        #    self.car.sensors[0]._clear_rays()
        #    self.space.step(dt)
        #    print(self.car.read_sensors())
        #    if self.car.is_crashed:
        #        self.reset_sim()

        self.window.push_handlers(on_key_press)#,on_draw)
        #pyglet.clock.schedule_interval(update, 1.0/30.0)
        #pyglet.app.run()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        self._pyglet_event_loop()
        self.car.sensors[0]._clear_rays()
        self.car.cmd(action)
        self.space.step(0.1)
        observation = self.car.read_sensors()
        done = self.car.is_crashed
        score = 0.0
        if done:
            score = -500
        else:
            if action == 0 or action == 1:
                score -= 1
            else:
                score += 1
        #print(observation, score, done)
        return observation, score, done, {}

    def render(self, mode='human'):
        self.window.clear()
        self.space.debug_draw(self.draw_options)

    def reset(self):
        self._pyglet_event_loop()
        self.car.sensors[0]._clear_rays()
        rand_pop, rand_angle = self._random_pop()
        self.car.reset_body(rand_pop, rand_angle)
        self.space.step(0.1)
        return self.car.read_sensors()
    
    def _random_pop(self):
        pop_sites = [[200,150],[200,450],[500,500],[550,150],[1100,350]]
        pop_site = random.choice(pop_sites)

        new_x = pop_site[0] + random.randrange(-100, +100, 1)
        new_y = pop_site[1] + random.randrange(-100, +100, 1)
        new_r = random.randrange(-31456, 31456) / 10000.0
        return (new_x, new_y), new_r

    def _pyglet_event_loop(self):
        pyglet.clock.tick()
        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()

    def _create_boundaries(self):
        body = self.space.static_body
        tickness = 1.0
        boundaries = []
        boundaries.append(pymunk.Segment(body, (1.0, 1.0), (self.width-1, 1.0),  tickness))
        boundaries.append(pymunk.Segment(body, (1.0, 1.0), (1.0, self.height-1), tickness))
        boundaries.append(pymunk.Segment(body, (1.0, self.height-1), (self.width-1, self.height-1), tickness))
        boundaries.append(pymunk.Segment(body, (self.width-1, 1.0),  (self.width-1, self.height-1), tickness))
        for boundarie in boundaries:
            boundarie.elasticity = 1.0
            boundarie.friction = 0.0
            boundarie.is_sensed = True
            self.space.add(boundarie)

if __name__ == "__main__":
    simulation = CarSimEnv()
    simulation.reset()
    while True:
        print(simulation.step(0))

