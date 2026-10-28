from pico2d import *

from grass import Grass
from boy import Boy
# Game object class here

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                running = False
            elif event.key == SDLK_SPACE and boy.state == 'SLEEP':
                boy.wake()
            elif event.key == SDLK_LEFT:
                boy.press_direction(-1)
            elif event.key == SDLK_RIGHT:
                boy.press_direction(1)
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                boy.release_direction(-1)
            elif event.key == SDLK_RIGHT:
                boy.release_direction(1)


def reset_world():
    global world
    global boy

    world = []

    grass = Grass()
    world.append(grass)

    boy = Boy()
    world.append(boy)



def update_world():
    for o in world:
        o.update()


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


running = True

open_canvas()
reset_world()
# game loop
while running:
    handle_events()
    update_world()
    render_world()
    delay(0.04)
# finalization code
close_canvas()
