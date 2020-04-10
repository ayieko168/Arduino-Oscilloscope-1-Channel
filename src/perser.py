from numpy import *
import serial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import time

ser = serial.Serial(timeout=1)
ser.baudrate = 115200
ser.port = "/dev/ttyACM0"
ser.open()



class Application(QMainWindow):

    def __init__(self):

        super().__init__()

        self.command = ""

        self.labelA = QLabel(self)
        self.labelB = QLabel(self)
        self.entry = QLineEdit(self)
        self.button = QPushButton(self)

        self.labelA.setText('Enter a command:')
        self.labelA.setMinimumWidth(150)
        self.labelA.move(10, 10)

        self.entry.setMinimumWidth(150)
        self.entry.move(10, 50)

        self.button.setText("Send Command")
        self.button.setMinimumWidth(150)
        self.button.move(20, 100)
        self.button.clicked.connect(self.click)

        self.labelB.setText("Current command = {}".format(self.command))
        self.labelB.setMinimumWidth(190)
        self.labelB.move(10, 150)


        self.setWindowTitle('serial interface')
        self.setGeometry(100, 100, 300, 200)

    def click(self):

        self.command = self.entry.text()
        self.labelB.setText("Current command = {}".format(self.command))
        self.entry.selectAll()

        data = bytes(self.command, "utf-8")
        if ser.is_open:
            ser.write(data)

        self.entry.setFocus()


np_array = np.array([])

def GrapgUpdateFunc():

    global np_array
    ## functions

    if ser.in_waiting > 0:
        try:
            data = ser.read_until(b"\r\n")
            data = data.decode("utf-8", errors='replace')
        except Exception as e:
            print(e)
            data = ""


        ## flow parser
        if data.startswith(">f="):
            dataList = data.split("\t")
            # print(dataList)

        ## various parser
        elif data.startswith(">q="):
            Qdata = data.replace(">q=", "")
            print("q value is ", Qdata)

        elif data.startswith(">dt="):
            dtdata = data.replace(">dt=", "")
            # print("dt_data value is ", dtdata)

        elif data.startswith(">dtReal="):
            dtRealdata = data.replace(">dtReal=", "")
            # print("dtReal value is ", dtRealdata)

        elif data.startswith(">chq="):
            avlChnls = data.replace(">chq=", "")
            # print("available channels are ", avlChnls)

        elif data.startswith(">v="):
            dataList = data.split("\t")

            np_array = np.append(np_array, dataList, axis=0)
            np_array.reshape(6, 100)

            print(np_array.size)

        elif data.startswith(">tTotalReal"):
            tTotalRealData = data.replace(">tTotalReal", "")
            # print("tTotalReal value is ", tTotalRealData)

        else:
            print(data)

    else:
        return

    ## end of functions

    # print(time.time()-initial_time)
    # print(fps, "Frames Per Second")



w = QApplication([])
timer = QTimer()
timer.timeout.connect(GrapgUpdateFunc)
timer.start()
app = Application()
app.show()
w.exec_()
