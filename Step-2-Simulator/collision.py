import sys
import pygame
import pymunk
import pymunk.pygame_util


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("pi=31415926535897932384626433")
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, -900)

    wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    wall_body.position = (0, 0)
    wall_shape = pymunk.Segment(wall_body, (0, 0), (0, 600), 2)
    wall_shape.elasticity = 1.0
    wall_shape.friction = 0.0
    wall_shape.collision_type = 0
    space.add(wall_body, wall_shape)

    floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    floor_body.position = (0, 0)
    floor_shape = pymunk.Segment(floor_body, (0, 0), (800, 0), 2)
    floor_shape.friction = 0.0
    space.add(floor_body, floor_shape)

    block_1_mass = 1000
    block_1_size = (100, 100)
    block_1_inertia = pymunk.moment_for_box(block_1_mass, block_1_size)
    block_1_body = pymunk.Body(block_1_mass, block_1_inertia)
    block_1_body.position = (600, 50)
    block_1_shape = pymunk.Poly.create_box(block_1_body, size=block_1_size)
    block_1_shape.elasticity = 1.0
    block_1_shape.friction = 0.0
    block_1_shape.collision_type = 1
    space.add(block_1_body, block_1_shape)
    block_1_body.apply_impulse_at_local_point((-100000, 0))

    block_2_mass = 1
    block_2_size = (10, 10)
    block_2_inertia = pymunk.moment_for_box(block_2_mass, block_2_size)
    block_2_body = pymunk.Body(block_2_mass, block_2_inertia)
    block_2_body.position = (200, 5)
    block_2_shape = pymunk.Poly.create_box(block_2_body, size=block_2_size)
    block_2_shape.elasticity = 1.0
    block_2_shape.friction = 0.0
    block_2_shape.collision_type = 2
    space.add(block_2_body, block_2_shape)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    def print_block_1_position(arbiter, space, data):
        print("print_block_1_position",block_1_body.position)
        return True

    def print_block_2_position(arbiter, space, data):
        print("print_block_2_position",block_2_body.position)
        return True


    wall_block_collision = space.add_collision_handler(1,2)
    wall_block_collision.begin = print_block_2_position
    wall_blocks_collision = space.add_collision_handler(0,1)
    wall_blocks_collision.begin = print_block_1_position
    block_block_collision = space.add_collision_handler(0,2)
    block_block_collision.begin = print_block_2_position

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit(0)
        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)
        space.step(1/60)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()