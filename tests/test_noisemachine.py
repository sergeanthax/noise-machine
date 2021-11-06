import unittest
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from noisemachine import NoiseMachine
import noisemachine
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
        self.assertEqual(len(self.machine.buttons), 2)


    def test_single_button_press(self):
        with mock.patch('noisemachine.subprocess.run') as mock_patch:
            self.machine.buttons[5].gpio_object.pin.drive_high()
            sleep(0.1)
            self.machine.buttons[5].gpio_object.pin.drive_low()
            sleep(0.5)
            self.assertTrue(self.monitor_thread.is_alive())
            self.assertTrue(mock_patch.called)
            self.assertEqual(mock_patch.call_args.args, tuple([['aplay', '-D', 'bluealsa', '5-single.wav']]))

    
    def test_double_button_press(self):
        with mock.patch('noisemachine.subprocess.run') as mock_patch:
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
            self.assertEqual(mock_patch.call_args.args, tuple([['aplay', '-D', 'bluealsa', '5-double.wav']]))
