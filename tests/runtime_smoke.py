"""Exercise the real SDL event queue, images, renderer, and five-second timers."""
from ctypes import byref
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
from pico2d import get_time, SDL_Event, SDL_PushEvent


def key(event_type, symbol):
    event = SDL_Event()
    event.type = event_type
    event.key.type = event_type
    event.key.repeat = 0
    event.key.keysym.sym = symbol
    assert SDL_PushEvent(byref(event)) == 1
    main.handle_events()


def run_for(seconds, observer=None):
    started_at = get_time()
    while get_time() - started_at < seconds:
        main.handle_events()
        main.update_world()
        main.render_world()
        if observer:
            observer()
        main.delay(1 / 60)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print('PASS:', message, flush=True)


def smoke():
    main.running = True
    main.open_canvas(800, 600)
    report = {}
    try:
        main.reset_world()
        actor = main.boy
        main.render_world()
        key(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        run_for(0.2)
        check(actor.state == 'RUN' and actor.x > 425, 'SDL right key moves the normal boy')
        key(main.SDL_KEYUP, main.SDLK_RIGHT)
        check(actor.state == 'IDLE', 'SDL key release returns to Idle')

        key(main.SDL_KEYDOWN, main.SDLK_a)
        key(main.SDL_KEYUP, main.SDLK_a)
        check(actor.state == 'AUTORUN' and actor.scale == 1.6 and actor.speed == 500,
              'SDL a key enters the separate enlarged and faster AutoRun state')
        started_at = actor.auto_run_started_at
        previous_direction = actor.face_dir
        turns = set()
        expired_at = None

        def observe():
            nonlocal previous_direction, expired_at
            if actor.state == 'AUTORUN':
                check_bounds = 80 <= actor.x <= 720
                if not check_bounds:
                    raise AssertionError('Enlarged sprite left the screen')
                if actor.face_dir != previous_direction:
                    turns.add('left' if actor.face_dir == 1 else 'right')
                    previous_direction = actor.face_dir
                if actor.auto_run_started_at != started_at:
                    raise AssertionError('A bounce restarted the AutoRun timer')
            elif expired_at is None:
                expired_at = get_time() - started_at

        run_for(5.15, observe)
        check(turns == {'left', 'right'}, 'AutoRun visibly reaches and turns at both edges')
        check(actor.state == 'IDLE' and expired_at is not None and 5 <= expired_at < 5.2,
              'AutoRun returns to Idle after five real seconds')
        check(actor.scale == 1 and actor.speed == 250 and not actor.is_invulnerable,
              'Timeout restores normal size speed and vulnerability')
        report['auto_run_elapsed_seconds'] = round(expired_at, 3)
        report['boundary_turns'] = sorted(turns)

        for symbol, direction in [(main.SDLK_LEFT, -1), (main.SDLK_RIGHT, 1)]:
            key(main.SDL_KEYDOWN, main.SDLK_a)
            key(main.SDL_KEYUP, main.SDLK_a)
            run_for(0.15)
            key(main.SDL_KEYDOWN, symbol)
            check(actor.state == 'RUN' and actor.face_dir == direction and actor.scale == 1,
                  f'Direction {direction} cancels AutoRun into normal Run')
            run_for(0.1)
            key(main.SDL_KEYUP, symbol)

        run_for(5.1)
        check(actor.state == 'SLEEP', 'Idle becomes Sleep after five real seconds')
        key(main.SDL_KEYDOWN, main.SDLK_SPACE)
        key(main.SDL_KEYUP, main.SDLK_SPACE)
        check(actor.state == 'IDLE', 'SDL Space wakes Sleep into Idle')
        run_for(5.1)
        check(actor.state == 'SLEEP', 'Idle timer restarts after waking')
        key(main.SDL_KEYDOWN, main.SDLK_LEFT)
        check(actor.state == 'RUN' and actor.face_dir == -1, 'SDL direction key wakes Sleep into Run')
        key(main.SDL_KEYUP, main.SDLK_LEFT)
        key(main.SDL_KEYDOWN, main.SDLK_ESCAPE)
        check(not main.running, 'SDL Escape exits the game loop')
        report['result'] = 'passed'
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    finally:
        main.close_canvas()


if __name__ == '__main__':
    smoke()
