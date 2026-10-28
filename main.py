from pico2d import (
    SDL_KEYDOWN, SDL_KEYUP, SDL_QUIT,
    SDLK_ESCAPE, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE, SDLK_a,
    clear_canvas, close_canvas, delay, get_events, get_time,
    open_canvas, update_canvas,
)

from boy import Boy
from grass import Grass


def handle_events():
    global running
    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN:
            if getattr(event, 'repeat', 0):
                continue
            if event.key == SDLK_ESCAPE:
                running = False
            elif event.key == SDLK_SPACE and boy.state == 'SLEEP':
                boy.wake()
            elif event.key == SDLK_LEFT:
                boy.press_direction(-1)
            elif event.key == SDLK_RIGHT:
                boy.press_direction(1)
            elif event.key == SDLK_a:
                boy.request_auto_run()
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                boy.release_direction(-1)
            elif event.key == SDLK_RIGHT:
                boy.release_direction(1)


def reset_world():
    global world, boy
    boy = Boy()
    world = [Grass(), boy]


def update_world():
    for obj in world:
        obj.update()


def render_world():
    clear_canvas()
    for obj in world:
        obj.draw()
    update_canvas()


def main():
    global running
    running = True
    open_canvas(800, 600)
    try:
        reset_world()
        while running:
            started_at = get_time()
            handle_events()
            update_world()
            render_world()
            delay(max(0.0, 1.0 / 60.0 - (get_time() - started_at)))
    finally:
        close_canvas()


if __name__ == '__main__':
    main()
