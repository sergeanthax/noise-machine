"""
Noise machine for a Raspberry Pi.

Uses the GPIO pins mapped to buttons to trigger sounds to be played by the Raspberry Pi.
"""

import subprocess
from typing import Dict, List, Optional, Tuple
import logging
import enum
import threading
import os
import shutil
from dataclasses import dataclass, field
import random

import gpiozero


class PressType(enum.Enum):
    """
    Enum for denoting the different possible press types.
    """

    SINGLE = 1
    DOUBLE = 2


class GeneratorType(enum.Enum):
    """
    Enum for listing the possible filename generator types.
    Used by FilenameGenerator to determine in what order to return filenames passed to it.
    """

    SINGLE = 1
    SEQUENCE = 2
    RANDOM = 3


class FilenameGenerator:
    """
    Generator class which returns an infinite list of filenames.
    """

    def __init__(self, filenames: List[Tuple[int, str]], generator_type: GeneratorType):
        self.__filenames: List[Tuple[int, str]] = filenames
        self.generator_type = generator_type
        self.__counter = 0

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self) -> str:
        """
        Return the next filename in the sequence.
        """
        if self.generator_type == GeneratorType.SINGLE:
            return self.__filenames[0][1]

        if self.generator_type == GeneratorType.SEQUENCE:
            filename = self.__filenames[self.__counter]

            self.__counter += 1

            if self.__counter >= len(self.__filenames):
                self.__counter = 0

            return filename[1]

        if self.generator_type == GeneratorType.RANDOM:
            if len(self.__filenames) >= 2:
                return self.__filenames[random.randrange(0, len(self.__filenames))][1]

            return self.__filenames[0][1]

        raise NotImplementedError("Invalid GeneratorType.")

    def add_filename(self, filename, position) -> None:
        """
        Add a filename to the list of filenames to be used by the generator.
        """
        if self.generator_type == GeneratorType.SINGLE:
            raise RuntimeError("GeneratorType single can only have one filename.")

        self.__filenames.append((position, filename))
        self.__filenames.sort()


@dataclass
class ButtonData:
    """
    Data object representing the data associated with the button,
    including the gpiozero button object itself as well as actions assigned to the button.
    """

    gpio_object: gpiozero.Button = None
    button_id: int = None
    filename_generators: Dict[PressType, FilenameGenerator] = field(
        default_factory=dict
    )


# pylint: disable=too-few-public-methods
class NoiseMachine:
    """
    Orchestrator class for creating and monitoring the buttons,
    as well as playing the sounds when required.
    """

    def __init__(self):
        self.last_button_pressed = 0
        self.buttons: Dict[int, ButtonData] = {}
        self.button_event = threading.Event()
        self.sound_player = None

        self.logger = logging.getLogger("noise-machine")

        self.logger.setLevel(logging.DEBUG)

        logger_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logger_formatter)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler("noise-machine.log")
        file_handler.setFormatter(logger_formatter)
        self.logger.addHandler(file_handler)

        self.__init_buttons()

    def monitor(self, stop_event: threading.Event = threading.Event()) -> None:
        """
        Master function which monitors button presses and calls appropriate actions.
        """

        self.logger.info("Starting button monitor.")

        while not stop_event.is_set():
            try:
                self.button_event.wait(timeout=2)

                if not self.button_event.is_set():
                    continue

                if self.sound_player is not None and self.sound_player.poll() is None:
                    self.sound_player.terminate()

                    self.logger.debug(
                        "Button press received while sound was playing, interrupting playback."
                    )
                    self.button_event.clear()
                    continue

                self.logger.debug(
                    "Button %s was pressed, waiting for double press.",
                    self.last_button_pressed,
                )

                moinitored_button = self.last_button_pressed

                self.button_event.clear()

                self.button_event.wait(0.25)

                if self.last_button_pressed == moinitored_button:
                    if self.button_event.is_set():
                        self.logger.debug(
                            "Button %s was double-pressed.", moinitored_button
                        )
                        self.__play_sound(
                            self.buttons[moinitored_button].filename_generators.get(
                                PressType.DOUBLE
                            )
                        )

                    else:
                        self.logger.debug(
                            "Button %s was single-pressed.", moinitored_button
                        )
                        self.__play_sound(
                            self.buttons[moinitored_button].filename_generators.get(
                                PressType.SINGLE
                            )
                        )

                else:
                    self.logger.debug(
                        "A button other than button %s was pressed, aborting sound playing.",
                        moinitored_button,
                    )

                self.button_event.clear()

            except KeyboardInterrupt:
                self.logger.info("Interrupt recieved, exiting.")
                break

    def __play_sound(self, button_number: Optional[FilenameGenerator]) -> None:
        # Nothing to do, no action was assigned to this button press type.
        if button_number is None:
            return

        file_name = button_number.next()

        self.logger.debug("Playing sound %s.", file_name)

        # pylint: disable=consider-using-with
        self.sound_player = subprocess.Popen(
            [shutil.which("aplay"), "-D", "bluealsa", file_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        # Clear button event in case it was pressed during sound playing
        self.button_event.clear()

    # pylint: disable=too-many-branches
    def __init_buttons(self):
        """
        Initialize GPIO inputs and assign callbacks to activation functions.
        """

        self.logger.info("Initializing buttons.")

        files = [x for x in os.listdir() if os.path.isfile(x) and x.endswith(".wav")]

        self.logger.debug("Found files: %s", ", ".join(files))

        for file in files:
            split_filename = file[:-4].split("-")
            button_id = int(split_filename[0])

            if self.buttons.get(button_id) is not None:
                new_button = self.buttons[button_id]

            else:
                new_button = ButtonData()

            new_button.button_id = button_id

            if len(split_filename) >= 2:
                if new_button.gpio_object is None:
                    new_button.gpio_object = gpiozero.Button(new_button.button_id)
                    new_button.gpio_object.when_pressed = self.__button_press

                if len(split_filename) == 4:
                    order_number = int(split_filename[3])

                if split_filename[1] == "single":
                    if len(split_filename) == 4 and split_filename[2] == "random":
                        if new_button.filename_generators.get(PressType.SINGLE) is None:
                            new_button.filename_generators[
                                PressType.SINGLE
                            ] = FilenameGenerator(
                                [(order_number, file)], GeneratorType.RANDOM
                            )

                        else:
                            new_button.filename_generators[
                                PressType.SINGLE
                            ].add_filename(file, order_number)

                    elif len(split_filename) == 4 and split_filename[2] == "sequence":
                        if new_button.filename_generators.get(PressType.SINGLE) is None:
                            new_button.filename_generators[
                                PressType.SINGLE
                            ] = FilenameGenerator(
                                [(order_number, file)], GeneratorType.SEQUENCE
                            )

                        else:
                            new_button.filename_generators[
                                PressType.SINGLE
                            ].add_filename(file, order_number)

                    else:
                        new_button.filename_generators[
                            PressType.SINGLE
                        ] = FilenameGenerator([(1, file)], GeneratorType.SINGLE)

                elif split_filename[1] == "double":
                    if len(split_filename) == 4 and split_filename[2] == "random":
                        if new_button.filename_generators.get(PressType.DOUBLE) is None:
                            new_button.filename_generators[
                                PressType.DOUBLE
                            ] = FilenameGenerator(
                                [(order_number, file)], GeneratorType.RANDOM
                            )

                        else:
                            new_button.filename_generators[
                                PressType.DOUBLE
                            ].add_filename(file, order_number)

                    elif len(split_filename) == 4 and split_filename[2] == "sequence":
                        if new_button.filename_generators.get(PressType.DOUBLE) is None:
                            new_button.filename_generators[
                                PressType.DOUBLE
                            ] = FilenameGenerator(
                                [(order_number, file)], GeneratorType.SEQUENCE
                            )

                        else:
                            new_button.filename_generators[
                                PressType.DOUBLE
                            ].add_filename(file, order_number)

                    else:
                        new_button.filename_generators[
                            PressType.DOUBLE
                        ] = FilenameGenerator([(1, file)], GeneratorType.SINGLE)

                else:
                    self.logger.warning("Invalid filename '%s'", file)

                    # Since the new button is invalid,
                    # close underlying GPIO pin if no other button actions are assigned to it.
                    if len(new_button.filename_generators) < 1:
                        new_button.gpio_object.close()

                    continue

                self.buttons[new_button.button_id] = new_button

        self.logger.info("Buttons initialized.")

    def __button_press(self, button: gpiozero.Button):
        """
        Handler to be registered with gpiozero for each button.
        """
        self.last_button_pressed = button.pin.number
        self.button_event.set()


if __name__ == "__main__":
    noise_machine = NoiseMachine()

    noise_machine.monitor()
