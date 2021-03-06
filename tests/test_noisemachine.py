from enum import auto
import unittest
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from noisemachine import NoiseMachine
from os import chdir
from os.path import realpath, split
from unittest import mock
from unittest.mock import patch
from time import sleep
import threading

Device.pin_factory = MockFactory()

# Set the current directory to be in the same place as the test script.
chdir(split(realpath(__file__))[0])

class TestNoiseMachine(unittest.TestCase):
    def setUp(self):
        self.machine = NoiseMachine()
        self.stop_event = threading.Event()
        self.monitor_thread = threading.Thread(target=self.machine.monitor, args=[self.stop_event])
        self.monitor_thread.start()


    def tearDown(self) -> None:
        self.stop_event.set()
        for button in self.machine.buttons.values():
            button.gpio_object.close()


    def test_init(self):
        self.assertNotEqual(self.machine.buttons, [])
        self.assertEqual(len(self.machine.buttons), 5)


    def test_single_button_single_action(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.1)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(0.5)
            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_args.args[0][3], '5-single.wav')


    def test_double_button_single_action(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.05)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(0.1)
            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.05)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(0.5)
            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_args.args[0][3], '5-double.wav')


    def test_single_button_random_action(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            for _ in range(0, 5):
                self.machine.buttons[26].gpio_object.pin.drive_high()
                sleep(0.1)
                self.machine.buttons[26].gpio_object.pin.drive_low()
                sleep(0.5)

                self.assertIn(mock_patch.call_args.args[0][3], ['26-single-random-1.wav', '26-single-random-2.wav', '26-single-random-3.wav'])

            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_count, 5)


    def test_double_button_random_action(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            for _ in range(0, 5):
                self.machine.buttons[26].gpio_object.pin.drive_high()
                sleep(0.05)
                self.machine.buttons[26].gpio_object.pin.drive_low()
                sleep(0.1)
                self.machine.buttons[26].gpio_object.pin.drive_high()
                sleep(0.05)
                self.machine.buttons[26].gpio_object.pin.drive_low()
                sleep(0.5)

                self.assertIn(mock_patch.call_args.args[0][3], ['26-double-random-1.wav', '26-double-random-2.wav', '26-double-random-3.wav'])

            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_count, 5)


    def test_unassigned_action(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            self.machine.buttons[6].gpio_object.pin.drive_high()
            sleep(0.1)
            self.machine.buttons[6].gpio_object.pin.drive_low()
            sleep(0.5)

            self.assertTrue(self.monitor_thread.is_alive())
            self.assertFalse(mock_patch.called)


    def test_single_button_sequence_action(self):
        expected_files = ['19-single-sequence-1.wav', '19-single-sequence-2.wav', '19-single-sequence-3.wav']

        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            for i in range(0, 3):
                self.machine.buttons[19].gpio_object.pin.drive_high()
                sleep(0.1)
                self.machine.buttons[19].gpio_object.pin.drive_low()
                sleep(0.5)

                self.assertEqual(mock_patch.call_args.args[0][3], expected_files[i])

            self.assertTrue(self.monitor_thread.is_alive())


    def test_double_button_sequence_action(self):
        expected_files = ['19-double-sequence-1.wav', '19-double-sequence-2.wav', '19-double-sequence-3.wav']

        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            for i in range(0, 3):
                self.machine.buttons[19].gpio_object.pin.drive_high()
                sleep(0.05)
                self.machine.buttons[19].gpio_object.pin.drive_low()
                sleep(0.1)
                self.machine.buttons[19].gpio_object.pin.drive_high()
                sleep(0.05)
                self.machine.buttons[19].gpio_object.pin.drive_low()
                sleep(0.5)
                self.assertEqual(mock_patch.call_args.args[0][3], expected_files[i])

            self.assertTrue(self.monitor_thread.is_alive())


    def test_playback_interrupt(self):
        with mock.patch('noisemachine.subprocess.Popen', autospec=True) as mock_patch:
            mock_patch.return_value.poll.return_value = None

            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.05)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(1)
            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.05)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(0.5)
            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_args.args[0][3], '5-single.wav')
            self.assertTrue(mock_patch.return_value.terminate.called)
