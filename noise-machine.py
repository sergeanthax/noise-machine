import subprocess
import gpiozero
import logging
import enum
import time


class PressType(enum.Enum):
    SINGLE = 1
    DOUBLE = 2


class NoiseMachine:
    def __init__(self):
        self.button_presses = {}
        self.buttons = []
        logger_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        self.logger = logging.getLogger('noise-machine')

        self.logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logger_formatter)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler('noise-machine.log')
        file_handler.setFormatter(logger_formatter)
        self.logger.addHandler(file_handler)

        self.init_buttons()


    def monitor(self):
        """
        Master function which monitors button presses and calls appropriate actions.
        """
        
        self.logger.info('Starting button monitor.')

        while True:
            for key in self.button_presses.keys():

                if self.button_presses[key] == 1:
                    self.play_sound(PressType.SINGLE, key)

                elif self.button_presses[key] == 2:
                    self.play_sound(PressType.DOUBLE, key)

                self.button_presses[key] = 0

            time.sleep(0.2)


    def play_sound(self, press_type: PressType, button_number: int):
        if press_type == PressType.SINGLE:
            file_name = '{}single.mp3'.format(button_number)

        elif press_type == PressType.DOUBLE:
            file_name = '{}double.mp3'.format(button_number)

        else:
            raise RuntimeError('Invalid PressType for play_sound.')

        self.logger.debug('Playing sound {}.'.format(file_name))

        subprocess.run(['mpg321', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    
    def init_buttons(self):
        """
        Initialize GPIO inputs and assign callbacks to activation functions.
        """

        self.logger.info('Initializing buttons.')

        self.buttons.append(gpiozero.Button('BOARD29'))
        self.buttons.append(gpiozero.Button('BOARD31'))
        self.buttons.append(gpiozero.Button('BOARD33'))
        self.buttons.append(gpiozero.Button('BOARD35'))
        self.buttons.append(gpiozero.Button('BOARD37'))

        self.buttons[0].when_pressed = lambda: self.button_press(1)
        self.buttons[1].when_pressed = lambda: self.button_press(2)
        self.buttons[2].when_pressed = lambda: self.button_press(3)
        self.buttons[3].when_pressed = lambda: self.button_press(4)
        self.buttons[4].when_pressed = lambda: self.button_press(5)

        self.logger.info('Buttons initialized.')


    def button_press(self, button_number: int):
        """
        
        """
        if self.button_presses.get(button_number) is None:
            self.logger.debug("Button {0} has been pressed for the first time.".format(button_number))

            self.button_presses[button_number] = 1

        else:
            self.button_presses[button_number] += 1

            self.logger.debug("Button {0} has been pressed {1} time(s) since last poll.".format(button_number, self.button_presses[button_number]))


if __name__ == '__main__':
    noise_machine = NoiseMachine()

    noise_machine.monitor()
