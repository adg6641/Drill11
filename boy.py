from math import pi

from pico2d import get_time, load_image
from transitions import Machine


class Boy:
    SCREEN_WIDTH = 800
    HALF_WIDTH = 50
    RUN_SPEED = 10

    def __init__(self):
        self.x, self.y = 400, 85
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = set()
        self.image = load_image('animation_sheet.png')
        self.idle_started_at = get_time()

        self.machine = Machine(
            model=self,
            states=[
                {'name': 'IDLE', 'on_enter': 'start_idle_timer'},
                {'name': 'RUN', 'on_enter': 'start_run_animation'},
                'SLEEP',
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

    def start_idle_timer(self):
        self.idle_started_at = get_time()

    def start_run_animation(self):
        self.frame = 0

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

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if get_time() - self.idle_started_at >= 5:
                self.sleep()
        elif self.state == 'RUN':
            self.frame = (self.frame + 1) % 8
            self.x = max(
                self.HALF_WIDTH,
                min(self.SCREEN_WIDTH - self.HALF_WIDTH,
                    self.x + self.face_dir * self.RUN_SPEED),
            )

    def draw(self):
        if self.state == 'IDLE':
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        elif self.state == 'RUN':
            self.image.clip_composite_draw(
                self.frame * 100, 100, 100, 100,
                0, 'h' if self.face_dir < 0 else '',
                self.x, self.y, 100, 100,
            )
        elif self.state == 'SLEEP':
            self.image.clip_composite_draw(
                self.frame * 100, 300, 100, 100,
                pi / 2, '', self.x, self.y - 30, 100, 100,
            )