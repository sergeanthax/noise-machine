import subprocess
import gpiozero


def button1_action():
    print('Button 1 was pressed.')
    subprocess.run(['mpg321', '1.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def button2_action():
    print('Button 2 was pressed.')
    subprocess.run(['mpg321', '2.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def button3_action():
    print('Button 3 was pressed.')
    subprocess.run(['mpg321', '3.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def button4_action():
    print('Button 4 was pressed.')
    subprocess.run(['mpg321', '4.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def button5_action():
    print('Button 5 was pressed.')
    subprocess.run(['mpg321', '5.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


button1 = gpiozero.Button('BOARD29')
button2 = gpiozero.Button('BOARD31')
button3 = gpiozero.Button('BOARD33')
button4 = gpiozero.Button('BOARD35')
button5 = gpiozero.Button('BOARD37')


button1.when_activated = button1_action
button2.when_activated = button2_action
button3.when_activated = button3_action
button4.when_activated = button4_action
button5.when_activated = button5_action

input('Press enter to exit.\n')
