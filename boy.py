from math import pi
from pathlib import Path

from pico2d import get_time, load_image
from transitions import Machine


class BoyState:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        self.boy.frame = 0.0

    def exit(self):
        pass


class Idle(BoyState):
    def enter(self):
        super().enter()
        self.boy.idle_started_at = get_time()

    def update(self, dt):
        self.boy.animate(dt)
        if get_time() - self.boy.idle_started_at >= self.boy.IDLE_TIMEOUT:
            self.boy.sleep()

    def draw(self):
        self.boy.draw_animation(300)


class Run(BoyState):
    def update(self, dt):
        self.boy.animate(dt)
        self.boy.x += self.boy.face_dir * self.boy.RUN_SPEED * dt
        self.boy.clamp_to_screen()

    def draw(self):
        self.boy.draw_animation(100)


class Sleep(BoyState):
    def update(self, dt):
        pass

    def draw(self):
        self.boy.draw_animation(300, rotation=pi / 2, y=self.boy.y - 30)


class Boy:
    SCREEN_WIDTH = 800
    SPRITE_SIZE = 100
    RUN_SPEED = 250.0  # pixels per second (the original 10 pixels / 0.04 s)
    ANIMATION_FPS = 10.0
    IDLE_TIMEOUT = 5.0

    def __init__(self):
        self.x, self.y = 400.0, 85.0
        self.frame = 0.0
        self.face_dir = 1
        self.pressed_directions = set()
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.last_updated_at = get_time()
        self.states = {'IDLE': Idle(self), 'RUN': Run(self), 'SLEEP': Sleep(self)}
        self.machine = Machine(
            model=self,
            states=[
                {'name': name, 'on_enter': state.enter, 'on_exit': state.exit}
                for name, state in self.states.items()
            ],
            initial='IDLE',
            auto_transitions=False,
            transitions=[
                {'trigger': 'run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'sleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake', 'source': 'SLEEP', 'dest': 'IDLE'},
            ],
        )
        # Machine sets its initial state without calling on_enter.
        self.states[self.state].enter()

    def press_direction(self, direction):
        if self.state not in ('IDLE', 'RUN', 'SLEEP'):
            return

        self.pressed_directions.add(direction)
        self.face_dir = direction
        if self.state in ('IDLE', 'SLEEP'):
            self.run()

    def release_direction(self, direction):
        self.pressed_directions.discard(direction)
        if self.state != 'RUN':
            return

        if not self.pressed_directions:
            self.stop_run()
        elif direction == self.face_dir:
            self.face_dir = next(iter(self.pressed_directions))

    def animate(self, dt):
        self.frame = (self.frame + self.ANIMATION_FPS * dt) % 8

    def clamp_to_screen(self):
        half_width = self.SPRITE_SIZE / 2
        self.x = max(half_width, min(self.SCREEN_WIDTH - half_width, self.x))

    def update(self, dt=None):
        now = get_time()
        if dt is None:
            dt = now - self.last_updated_at
        self.last_updated_at = now
        self.states[self.state].update(max(0.0, dt))

    def draw_animation(self, row, rotation=0, y=None):
        self.image.clip_composite_draw(
            int(self.frame) * self.SPRITE_SIZE, row,
            self.SPRITE_SIZE, self.SPRITE_SIZE,
            rotation, 'h' if self.face_dir < 0 else '',
            self.x, self.y if y is None else y,
            self.SPRITE_SIZE, self.SPRITE_SIZE,
        )

    def draw(self):
        self.states[self.state].draw()
