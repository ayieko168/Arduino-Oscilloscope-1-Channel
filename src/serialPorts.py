import sys
import glob
import serial
import os
from PyQt5.QtWidgets import (QWidget, QLineEdit, QInputDialog, QApplication)
import sys


def ask_pass():

    class App(QWidget):

        def __init__(self):
            super().__init__()
            self.title = 'PyQt5 input dialogs - pythonspot.com'
            self.left = 10
            self.top = 10
            self.width = 640
            self.height = 480
            self.tex = ""

        def initUI(self):
            self.setWindowTitle(self.title)
            self.setGeometry(self.left, self.top, self.width, self.height)

            tex = self.getText()

            self.destroy()

            return tex

        def getText(self):
            text, okPressed = QInputDialog.getText(self, "Get sudo password", "Password:", QLineEdit.Normal, "")
            if okPressed and text != '':
                print("sudo pass set to {}".format(text))
                return text

    app = QApplication(sys.argv)
    ex = App()
    tex = ex.initUI()

    return tex


def list_ports():
    """ Lists serial port names

        Type: List, []

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
        try:
            s = serial.Serial("/dev/ttyACM0")
            s.close()
        except Exception as e:
            if e.args[0] == 13:
                sudoPassword = ask_pass()

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except Exception as e:
            if e.args[0] == 13:

                command = f'chmod 666 {port}'
                os.system('echo %s|sudo -S %s' % (sudoPassword, command))

                try:
                    s = serial.Serial(port)
                    s.close()
                    result.append(port)
                except Exception as e:
                    print(e)
    return result
