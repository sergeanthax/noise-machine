from genericpath import isfile
from posixpath import split
import subprocess
from typing import Dict, List, Callable
import gpiozero
import logging
import enum
import threading
import os
from dataclasses import dataclass, field


class PressType(enum.Enum):
    SINGLE = 1
    DOUBLE = 2



class GeneratorType(enum.Enum):
    SINGLE = 1
    SEQUENCE = 2
    RANDOM = 3


class FilenameGenerator:
    def __init__(self, filenames: List[str], generator_type: GeneratorType):
        self.__filenames = filenames
        self.generator_type = generator_type


    def __iter__(self):
        return self


    def __next__(self):
        return self.next()


    def next(self):
        if self.generator_type == GeneratorType.SINGLE:
            return self.__filenames[0]


@dataclass
class ButtonData:
    gpio_object: gpiozero.Button = None
    button_id: int = None
    filename_generators: Dict[PressType, FilenameGenerator] = field(default_factory=dict)


class NoiseMachine:
    def __init__(self):
        self.last_button_pressed = 0
        self.buttons: Dict[int, ButtonData] = {}
        self.button_event = threading.Event()

        self.logger = logging.getLogger('noise-machine')

        self.logger.setLevel(logging.DEBUG)

        logger_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logger_formatter)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler('noise-machine.log')
        file_handler.setFormatter(logger_formatter)
        self.logger.addHandler(file_handler)

        self.__init_buttons()


    def monitor(self, stop_event: threading.Event = threading.Event()):
        """
        Master function which monitors button presses and calls appropriate actions.
        """

        self.logger.info('Starting button monitor.')

        while not stop_event.is_set():
            try:
                self.button_event.wait(timeout=2)

                if not self.button_event.is_set():
                    continue

                self.logger.debug('Button {} was pressed, waiting for double press.'.format(self.last_button_pressed))

                moinitored_button = self.last_button_pressed

                self.button_event.clear()

                self.button_event.wait(0.2)

                if self.last_button_pressed == moinitored_button:
                    if self.button_event.is_set():
                        self.logger.debug('Button {} was double-pressed.'.format(moinitored_button))
                        self.play_sound(self.buttons[moinitored_button].filename_generators[PressType.DOUBLE])

                    else:
                        self.logger.debug('Button {} was single-pressed.'.format(moinitored_button))
                        self.play_sound(self.buttons[moinitored_button].filename_generators[PressType.SINGLE])

                else:
                    self.logger.debug('A button other than button {} was pressed, aborting sound playing.'.format(moinitored_button))

                self.button_event.clear()

            except KeyboardInterrupt:
                self.logger.info('Interrupt recieved, exiting.')
                break


    def play_sound(self, button_number: FilenameGenerator):
        file_name = button_number.next()

        self.logger.debug('Playing sound {}.'.format(file_name))

        subprocess.run(['aplay', '-D', 'bluealsa', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


    def __init_buttons(self):
        """
        Initialize GPIO inputs and assign callbacks to activation functions.
        """

        self.logger.info('Initializing buttons.')

        files = [x for x in os.listdir() if os.path.isfile(x) and x.endswith('.wav')]

        self.logger.debug('Found files: ' + ', '.join(files))

        for file in files:
            split_filename = file.removesuffix('.wav').split('-')
            button_id = int(split_filename[0])

            if self.buttons.get(button_id) is not None:
                new_button = self.buttons[button_id]
    
            else:
                new_button = ButtonData()

            if len(split_filename) == 2:
                new_button.button_id = button_id

                if len(split_filename) == 2:
                    if new_button.gpio_object is None:
                        new_button.gpio_object = gpiozero.Button('{}'.format(new_button.button_id))
                        new_button.gpio_object.when_pressed = self.__button_press

                    if split_filename[1] == 'single':
                        new_button.filename_generators[PressType.SINGLE] = FilenameGenerator([file], GeneratorType.SINGLE)

                    elif split_filename[1] == 'double':
                        new_button.filename_generators[PressType.DOUBLE] = FilenameGenerator([file], GeneratorType.SINGLE)

                    else:
                        self.logger.warning("Invalid filename '{}'".format(file))

                self.buttons[new_button.button_id] = new_button

        self.logger.info('Buttons initialized.')


    def __button_press(self, button: gpiozero.Button):
        """
        Handler to be registered with gpiozero for each button.
        """
        self.last_button_pressed = button.pin.number
        self.button_event.set()


if __name__ == '__main__':
    noise_machine = NoiseMachine()

    noise_machine.monitor()
