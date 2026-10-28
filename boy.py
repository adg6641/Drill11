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
        self.boy.x += self.boy.face_dir * self.boy.speed * dt
        self.boy.clamp_to_screen()

    def draw(self):
        self.boy.draw_animation(100)


class Sleep(BoyState):
    def update(self, dt):
        pass

    def draw(self):
        self.boy.draw_animation(300, rotation=pi / 2, y=self.boy.y - 30)


class AutoRun(BoyState):
    def enter(self):
        super().enter()
        self.boy.auto_run_started_at = get_time()
        self.boy.pressed_directions.clear()
        self.boy.is_invulnerable = True
        self.boy.speed = self.boy.AUTO_RUN_SPEED
        self.boy.scale = self.boy.AUTO_RUN_SCALE
        self.boy.clamp_to_screen()

    def exit(self):
        self.boy.is_invulnerable = False
        self.boy.speed = self.boy.RUN_SPEED
        self.boy.scale = 1.0

    def update(self, dt):
        if get_time() - self.boy.auto_run_started_at >= self.boy.AUTO_RUN_DURATION:
            self.boy.finish_auto_run()
            return
        self.boy.animate(dt)
        self.boy.x += self.boy.face_dir * self.boy.speed * dt
        self.boy.clamp_to_screen()

    def draw(self):
        self.boy.draw_animation(100)


class Boy:
    SCREEN_WIDTH = 800
    SPRITE_SIZE = 100
    RUN_SPEED = 250.0  # pixels per second (the original 10 pixels / 0.04 s)
    ANIMATION_FPS = 10.0
    IDLE_TIMEOUT = 5.0
    AUTO_RUN_DURATION = 5.0
    AUTO_RUN_SPEED = RUN_SPEED * 2.0
    AUTO_RUN_SCALE = 1.6

    def __init__(self):
        self.x, self.y = 400.0, 85.0
        self.frame = 0.0
        self.face_dir = 1
        self.pressed_directions = set()
        self.is_invulnerable = False
        self.speed = self.RUN_SPEED
        self.scale = 1.0
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.last_updated_at = get_time()
        self.states = {
            'IDLE': Idle(self), 'RUN': Run(self),
            'SLEEP': Sleep(self), 'AUTORUN': AutoRun(self),
        }
        self.machine = Machine(
            model=self,
            states=[
                {'name': name, 'on_enter': state.enter, 'on_exit': state.exit}
                for name, state in self.states.items()
            ],
            initial='IDLE',
            auto_transitions=False,
            transitions=[
                {'trigger': 'run', 'source': ['IDLE', 'SLEEP', 'AUTORUN'], 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'sleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'auto_run', 'source': 'IDLE', 'dest': 'AUTORUN'},
                {'trigger': 'finish_auto_run', 'source': 'AUTORUN', 'dest': 'IDLE'},
            ],
        )
        # Machine sets its initial state without calling on_enter.
        self.states[self.state].enter()

    def request_auto_run(self):
        if self.state != 'IDLE':
            return False
        self.auto_run()
        return True

    def press_direction(self, direction):
        if self.state == 'AUTORUN':
            # Cancellation obeys the newly pressed direction, not stale keys.
            self.pressed_directions = {direction}
            self.face_dir = direction
            self.run()
            return
        if direction in self.pressed_directions:
            return  # Ignore operating-system key repeat.
        self.pressed_directions.add(direction)
        self.apply_direction_input()

    def release_direction(self, direction):
        if direction not in self.pressed_directions:
            return
        self.pressed_directions.remove(direction)
        if self.state == 'AUTORUN':
            return  # Only a direction key DOWN cancels AutoRun.
        self.apply_direction_input()

    def apply_direction_input(self):
        # Both keys cancel each other. Releasing one resumes the other direction.
        direction = sum(self.pressed_directions)
        if direction:
            self.face_dir = direction
            if self.state in ('IDLE', 'SLEEP'):
                self.run()
        elif self.state == 'RUN':
            self.stop_run()

    def animate(self, dt):
        self.frame = (self.frame + self.ANIMATION_FPS * (self.speed / self.RUN_SPEED) * dt) % 8

    def clamp_to_screen(self):
        half_width = self.SPRITE_SIZE * self.scale / 2
        self.x = max(half_width, min(self.SCREEN_WIDTH - half_width, self.x))

    def update(self, dt=None):
        now = get_time()
        if dt is None:
            dt = now - self.last_updated_at
        self.last_updated_at = now
        self.states[self.state].update(max(0.0, dt))

    def draw_animation(self, row, rotation=0, y=None):
        size = self.SPRITE_SIZE * self.scale
        # Keep the sprite's feet at the same ground level when it grows.
        draw_y = self.y + 35 * (self.scale - 1) if y is None else y
        self.image.clip_composite_draw(
            int(self.frame) * self.SPRITE_SIZE, row,
            self.SPRITE_SIZE, self.SPRITE_SIZE,
            rotation, 'h' if self.face_dir < 0 else '',
            self.x, draw_y, size, size,
        )

    def draw(self):
        self.states[self.state].draw()
