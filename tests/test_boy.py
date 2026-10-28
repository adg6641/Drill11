import unittest
from unittest.mock import Mock, patch

import boy


class BoyTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.image = Mock()
        self.clock_patch = patch.object(boy, 'get_time', side_effect=lambda: self.now)
        self.image_patch = patch.object(boy, 'load_image', return_value=self.image)
        self.clock_patch.start()
        self.image_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.addCleanup(self.image_patch.stop)
        self.boy = boy.Boy()

    def test_idle_sleeps_at_five_seconds_and_wake_resets_timer(self):
        self.now += 4.999
        self.boy.update(0)
        self.assertEqual(self.boy.state, 'IDLE')
        self.now = 105.0
        self.boy.update(0)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.boy.wake()
        self.assertEqual(self.boy.state, 'IDLE')
        self.boy.update(0)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_opposing_keys_and_releases_match_direction_diagram(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.boy = boy.Boy()
                self.boy.press_direction(direction)
                self.assertEqual((self.boy.state, self.boy.face_dir), ('RUN', direction))
                self.boy.press_direction(-direction)
                self.assertEqual((self.boy.state, self.boy.face_dir), ('IDLE', direction))
                self.boy.release_direction(direction)
                self.assertEqual((self.boy.state, self.boy.face_dir), ('RUN', -direction))
                self.boy.release_direction(-direction)
                self.assertEqual((self.boy.state, self.boy.face_dir), ('IDLE', -direction))

    def test_direction_key_wakes_sleep(self):
        self.now += 5
        self.boy.update(0)
        self.boy.press_direction(-1)
        self.assertEqual((self.boy.state, self.boy.face_dir), ('RUN', -1))

    def test_repeat_keydown_does_not_stop_running(self):
        self.boy.press_direction(1)
        self.boy.press_direction(1)
        self.assertEqual(self.boy.state, 'RUN')

    def test_run_distance_is_independent_of_update_frequency(self):
        self.boy.press_direction(1)
        self.boy.update(1.0)
        expected = self.boy.x
        other = boy.Boy()
        other.press_direction(1)
        for _ in range(10):
            other.update(0.1)
        self.assertAlmostEqual(other.x, expected)

    def test_left_idle_and_run_are_drawn_facing_left(self):
        self.boy.press_direction(-1)
        self.boy.draw()
        self.assertEqual(self.image.clip_composite_draw.call_args.args[5], 'h')
        self.boy.release_direction(-1)
        self.boy.draw()
        self.assertEqual(self.image.clip_composite_draw.call_args.args[5], 'h')

    def test_auto_run_is_a_separate_state_class_and_only_starts_from_idle(self):
        self.assertIsInstance(self.boy.states['AUTORUN'], boy.AutoRun)
        self.boy.press_direction(1)
        self.assertFalse(self.boy.request_auto_run())
        self.boy.release_direction(1)
        self.assertTrue(self.boy.request_auto_run())
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.assertTrue(self.boy.is_invulnerable)

    def test_auto_run_moves_without_input_and_expires_at_five_seconds(self):
        self.boy.request_auto_run()
        old_x = self.boy.x
        self.now += 0.1
        self.boy.update(0.1)
        self.assertGreater(self.boy.x, old_x)
        self.now = 104.999
        self.boy.update(0)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.now = 105.0
        self.boy.update(0)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertFalse(self.boy.is_invulnerable)
        self.assertEqual(self.boy.idle_started_at, 105.0)

    def test_direction_press_cancels_auto_run_in_the_pressed_direction(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.boy = boy.Boy()
                self.boy.request_auto_run()
                self.boy.press_direction(direction)
                self.assertEqual((self.boy.state, self.boy.face_dir), ('RUN', direction))
                self.assertFalse(self.boy.is_invulnerable)
                self.boy.release_direction(direction)
                self.assertEqual(self.boy.state, 'IDLE')

    def test_repeat_auto_request_and_key_release_do_not_restart_or_cancel(self):
        self.boy.request_auto_run()
        started_at = self.boy.auto_run_started_at
        self.now += 2
        self.assertFalse(self.boy.request_auto_run())
        self.boy.release_direction(1)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.assertEqual(self.boy.auto_run_started_at, started_at)

    def test_a_cannot_start_auto_run_from_sleep(self):
        self.now += 5
        self.boy.update(0)
        self.assertFalse(self.boy.request_auto_run())
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_auto_run_is_faster_and_draws_a_larger_sprite(self):
        self.boy.press_direction(1)
        self.boy.update(0.1)
        normal_distance = self.boy.x - 400
        self.boy.release_direction(1)
        self.boy.x = 400
        self.boy.request_auto_run()
        self.boy.update(0.1)
        self.assertGreater(self.boy.x - 400, normal_distance)
        self.boy.draw()
        self.assertEqual(self.image.clip_composite_draw.call_args.args[-2:], (160.0, 160.0))

    def test_speed_size_and_invulnerability_restore_on_both_exit_paths(self):
        for cancel_with_key in (False, True):
            with self.subTest(cancel_with_key=cancel_with_key):
                self.boy = boy.Boy()
                self.boy.request_auto_run()
                if cancel_with_key:
                    self.boy.press_direction(-1)
                else:
                    self.now += 5
                    self.boy.update(0)
                self.assertEqual(self.boy.speed, self.boy.RUN_SPEED)
                self.assertEqual(self.boy.scale, 1.0)
                self.assertFalse(self.boy.is_invulnerable)

    def test_auto_run_reflects_at_both_edges_without_restarting_timer(self):
        self.boy.request_auto_run()
        started_at = self.boy.auto_run_started_at
        for direction, start, expected in [(-1, 81.0, 84.0), (1, 719.0, 716.0)]:
            with self.subTest(direction=direction):
                self.boy.x, self.boy.face_dir = start, direction
                self.boy.update(0.01)
                self.assertAlmostEqual(self.boy.x, expected)
                self.assertEqual(self.boy.face_dir, -direction)
                self.assertEqual(self.boy.state, 'AUTORUN')
                self.assertEqual(self.boy.auto_run_started_at, started_at)

    def test_auto_run_turns_on_exact_edge_contact(self):
        self.boy.request_auto_run()
        self.boy.x, self.boy.face_dir = 719.0, 1
        self.boy.update(0.002)
        self.assertEqual((self.boy.x, self.boy.face_dir), (720.0, -1))

    def test_large_frame_can_bounce_multiple_times_without_leaving_screen(self):
        self.boy.request_auto_run()
        self.boy.update(3.0)
        self.assertAlmostEqual(self.boy.x, 620.0)
        self.assertEqual(self.boy.face_dir, 1)

    def test_enlarging_at_an_edge_keeps_the_entire_sprite_in_bounds(self):
        self.boy.x, self.boy.face_dir = 50, -1
        self.boy.request_auto_run()
        self.boy.update(0)
        self.assertEqual((self.boy.x, self.boy.face_dir), (80.0, 1))


if __name__ == '__main__':
    unittest.main()
