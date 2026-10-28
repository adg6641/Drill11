from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main


class EventTests(unittest.TestCase):
    def setUp(self):
        main.boy = Mock()
        main.boy.state = 'IDLE'
        main.running = True

    def send(self, event_type, key=None, repeat=0):
        event = SimpleNamespace(type=event_type, key=key, repeat=repeat)
        with patch.object(main, 'get_events', return_value=[event]):
            main.handle_events()

    def test_a_key_routes_to_auto_run_request(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        main.boy.request_auto_run.assert_called_once_with()

    def test_direction_key_down_and_up_are_forwarded(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        main.boy.press_direction.assert_called_with(-1)
        self.send(main.SDL_KEYUP, main.SDLK_LEFT)
        main.boy.release_direction.assert_called_with(-1)
        self.send(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        main.boy.press_direction.assert_called_with(1)
        self.send(main.SDL_KEYUP, main.SDLK_RIGHT)
        main.boy.release_direction.assert_called_with(1)

    def test_space_only_wakes_sleep(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_SPACE)
        main.boy.wake.assert_not_called()
        main.boy.state = 'SLEEP'
        self.send(main.SDL_KEYDOWN, main.SDLK_SPACE)
        main.boy.wake.assert_called_once_with()

    def test_key_repeat_is_ignored(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a, repeat=1)
        main.boy.request_auto_run.assert_not_called()

    def test_escape_and_window_close_stop_the_loop(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_ESCAPE)
        self.assertFalse(main.running)
        main.running = True
        self.send(main.SDL_QUIT)
        self.assertFalse(main.running)


if __name__ == '__main__':
    unittest.main()
