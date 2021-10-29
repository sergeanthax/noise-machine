import subprocess
import gpiozero
import logging
import enum
import threading


class PressType(enum.Enum):
    SINGLE = 1
    DOUBLE = 2


class NoiseMachine:
    def __init__(self):
        self.last_button_pressed = 0
        self.buttons = []
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


    def monitor(self):
        """
        Master function which monitors button presses and calls appropriate actions.
        """

        self.logger.info('Starting button monitor.')

        while True:
            try:
                self.button_event.wait()

                self.logger.debug('Button {} was pressed, waiting for double press.'.format(self.last_button_pressed))

                moinitored_button = self.last_button_pressed

                self.button_event.clear()

                self.button_event.wait(0.2)

                if self.last_button_pressed == moinitored_button:
                    if self.button_event.is_set():
                        self.logger.debug('Button {} was double-pressed.'.format(moinitored_button))
                        self.play_sound(PressType.DOUBLE, moinitored_button)

                    else:
                        self.logger.debug('Button {} was single-pressed.'.format(moinitored_button))
                        self.play_sound(PressType.SINGLE, moinitored_button)

                else:
                    self.logger.debug('A button other than button {} was pressed, aborting sound playing.'.format(moinitored_button))

                self.button_event.clear()

            except KeyboardInterrupt:
                self.logger.info('Interrupt recieved, exiting.')
                break


    def play_sound(self, press_type: PressType, button_number: int):
        if press_type == PressType.SINGLE:
            file_name = '{}single.wav'.format(button_number)

        elif press_type == PressType.DOUBLE:
            file_name = '{}double.wav'.format(button_number)

        else:
            raise RuntimeError('Invalid PressType for play_sound.')

        self.logger.debug('Playing sound {}.'.format(file_name))

        subprocess.run(['aplay', '-D', 'bluealsa', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


    def __init_buttons(self):
        """
        Initialize GPIO inputs and assign callbacks to activation functions.
        """

        self.logger.info('Initializing buttons.')

        self.buttons.append(gpiozero.Button('BOARD29'))
        self.buttons.append(gpiozero.Button('BOARD31'))
        self.buttons.append(gpiozero.Button('BOARD33'))
        self.buttons.append(gpiozero.Button('BOARD35'))
        self.buttons.append(gpiozero.Button('BOARD37'))

        self.buttons[0].when_pressed = lambda: self.__button_press(1)
        self.buttons[1].when_pressed = lambda: self.__button_press(2)
        self.buttons[2].when_pressed = lambda: self.__button_press(3)
        self.buttons[3].when_pressed = lambda: self.__button_press(4)
        self.buttons[4].when_pressed = lambda: self.__button_press(5)

        self.logger.info('Buttons initialized.')


    def __button_press(self, button_number: int):
        """
        Handler to be registered with gpiozero for each button.
        """
        self.last_button_pressed = button_number
        self.button_event.set()


if __name__ == '__main__':
    noise_machine = NoiseMachine()

    noise_machine.monitor()
