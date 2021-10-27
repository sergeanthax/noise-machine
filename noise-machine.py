import subprocess
import gpiozero
import logging
import enum
import time


class PressType(enum):
    SINGLE = 1
    DOUBLE = 2


class NoiseMachine:
    def __init__(self):
        self.logger = logging.Logger()
        self.button_presses = {}
        
        logging.basicConfig(filename='noise_machine.log', level=logging.DEBUG)

        self.init_buttons()


    def monitor(self):
        """
        Master function which monitors button presses and calls appropriate actions.
        """
        
        self.logger.debug('Starting monitor loops.')

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

        subprocess.run(['mpg321', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    
    def init_buttons(self):
        """
        Initialize GPIO inputs and assign callbacks to activation functions.
        """

        self.logger.debug('Initializing buttons.')

        button1 = gpiozero.Button('BOARD29')
        button2 = gpiozero.Button('BOARD31')
        button3 = gpiozero.Button('BOARD33')
        button4 = gpiozero.Button('BOARD35')
        button5 = gpiozero.Button('BOARD37')


        button1.when_activated = lambda: self.button_press(1)
        button2.when_activated = lambda: self.button_press(2)
        button3.when_activated = lambda: self.button_press(3)
        button4.when_activated = lambda: self.button_press(4)
        button5.when_activated = lambda: self.button_press(5)

        self.logger.debug('Buttons initialized.')


    def button_press(self, button_number: int):
        if self.button_presses.get(button_number) is not None:
            self.logger.debug("Button {0} has been pressed for the first time.".format(button_number))

            self.button_presses[button_number] = 1

        else:
            self.button_presses[button_number] += 1

            self.logger.debug("Button {0} has been pressed {1} time(s) since last poll.".fomat(button_number, self.button_presses[button_number]))


if __name__ == '__main__':
    noise_machine = NoiseMachine()

    noise_machine.monitor()
