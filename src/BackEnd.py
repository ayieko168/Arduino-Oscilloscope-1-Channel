# Main Imports
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import collections
try:
    from src.MainUI import *
except:
    from MainUI import *
import numpy as np
from math import sin, cos
import serial
import pyqtgraph as pg

try:
    import src.serialPorts as serialPorts
except:
    import serialPorts as serialPorts

#### System Imports
import datetime, time, os

#### Utility Imports
import json

_BAUDRATES = ["300", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200",
              "576000", "1152000", "1500000", "2000000", "2500000", "3000000", "3500000", "4000000"]

_COMPORTs = serialPorts.list_ports()

comPORT = int
baudRate = int


def _map(value, in_min, in_max, out_min, out_max):
    """From scale value to calc val"""

    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class Application(QMainWindow):

    def __init__(self):

        global _COMPORTs
        global curve, ptr, Xm, curve2, ptr2, Xm2

        super().__init__()
        self.MainUi = Ui_MainWindow()
        self.MainUi.setupUi(self)
        # self.MainUi.toolBar.actionTriggered[QAction].connect(self.toolbtnpressed)

        ############## Main Window Widgets connections 
        ### Buttons
        self.MainUi.ConfSerPowerButton.clicked.connect(self.powerButtonFunc)
        self.MainUi.SaveDataButton.clicked.connect(self.saveDataToTxtFile)
        self.MainUi.SamplingControlFlowButton.clicked.connect(self.SamplingControlFlowButtonCMD)
        self.MainUi.SamplingControlOnceButton.clicked.connect(self.SamplingControlOnceButtonCMD)
        self.MainUi.SamplingControlVariousButton.clicked.connect(self.SamplingControlVariousButtonCMD)
        self.MainUi.resetButton.clicked.connect(self.resetButtonCMD)
        ### Sliders
        self.MainUi.Channel1VoltsSlider.valueChanged.connect(self.Channel1VoltsSliderCMD)
        self.MainUi.Channel1MsSlider.valueChanged.connect(self.Channel1MsSliderCMD)
        self.MainUi.SigGenFreqSlider.valueChanged.connect(self.SigGenFreqSliderCMD)
        self.MainUi.SigGenPeriodSlider.valueChanged.connect(self.SigGenPeriodSliderCMD)
        self.MainUi.SigGenDutyslider.valueChanged.connect(self.SigGenDutysliderCMD)
        self.MainUi.SampConrolDTScale.valueChanged.connect(self.SampConrolDTScaleCMD)
        self.MainUi.SampControlQScale.valueChanged.connect(self.SampControlQScaleCMD)
        ### Combo Box
        self.MainUi.ConfSerComPortCombo.activated.connect(self.ConfSerComPortComboCMD)
        self.MainUi.ConfSerBaoudRateCombo.activated.connect(self.ConfSerBaoudRateComboCMD)
        ### Check Boxes
        self.MainUi.Channel1Check.clicked.connect(self.Channel1CheckCMD)

        ############# Set Default Values and Global Variables ###########
        #### Globals
        self.SampilngValue = 0.0
        self.Port = ""
        self.Baudrate = 115200
        self.readData = ""
        self.ch1Data = 0
        #### Oscilloscope Variables
        self.sigFreq = 50 # Hz
        self.sigTimeDiv = 1.0 / self.sigFreq  # Seconds
        self.sigDuty = 25  # Percentage Time PWM On 
        self.sampTimeDiv = 1e-3 # Seconds Per Division # dt
        self.sampQ = 100 
        self.sampDtTotal = self.sampQ * self.sampTimeDiv
        self.chanVolDiv = 1 #Volt per Division
        self.chanTimeDiv = self.sampTimeDiv * 10.0

        #### Set Defaults
        self.Set_SigGenFreqSliderValue(self.sigFreq)
        self.MainUi.SigGenDutyslider.setValue(self.sigDuty)
        self.Set_SampConrolDTScaleValue(self.sampTimeDiv)
        self.MainUi.SampControlQScale.setValue(self.sampQ)
        self.MainUi.ConfSerBaoudRateCombo.addItems(_BAUDRATES)
        self.MainUi.ConfSerBaoudRateCombo.setCurrentIndex(8)
        self.MainUi.ConfSerComPortCombo.addItems([""] + _COMPORTs)
        ############ Serial Setup ########################
        self.ser = serial.Serial(timeout=1)  #initiate a serial but not connect yet
        #### Update Timer Setting Up and Start Graphing
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.GrapgUpdateFunc)

        ############ Graph SetUp #################################
        self.graphView = self.MainUi.graphicsView
        self.graphView.setBackground("k")
        # self.graphView.setMouseEnabled(False, False)

        self.y = np.zeros(self.sampQ)
        self.x = np.arange(0.0, len(self.y))

        # PyQtGraph settings
        self.graphView.showGrid(x=True, y=True)
        self.graphView.setLabel('left', 'amplitude', 'V')
        self.graphView.setLabel('bottom', 'time', 's')        
        self.curve = self.graphView.plot(self.x, self.y, pen=(255, 0, 0), symbol="o", symbolSize=2)

        self.lastTime = time.time()
        self.fps = None

    def GrapgUpdateFunc(self):
        
        ## read serial data
        if self.ser.in_waiting > 0:
            try:
                data = self.ser.read_until(b"\r\n")
                data = data.decode("utf-8", errors='replace')
            except Exception as e:
                print(e)
                data = ""
                return

            ## flow parser
            if data.startswith(">f="):
                dataList = data.split("\t")
                # print(dataList)  ##==> ['>f=0', '4e-3', '1020', '689', '472', '324\r\n']
                try:
                    int(dataList[2])
                    float(dataList[1])

                    foo = _map(float(dataList[2].strip()), 0, 1023, 0, 5)
                    self.sampDtTotal = float(dataList[1].strip())
                
                    self.y = np.append(self.y[1:], foo)
                    self.x = np.append(self.x[1:], self.x[-1] + float(dataList[1]))

                except:
                    pass 
                
            ## various parser
            elif data.startswith(">q="):
                Qdata = data.replace(">q=", "")
                self.sampQ = int(Qdata.strip())
                # print("q value is ", Qdata)

            elif data.startswith(">dtReal="):
                dtRealdata = data.replace(">dtReal=", "")
                try:
                    self.sampTimeDiv = float(dtRealdata.strip())
                except ValueError:
                    return
                # print("dtReal value is ", dtRealdata)

            elif data.startswith(">chq="):
                avlChnls = data.replace(">chq=", "")
                # print("available channels are ", avlChnls)

            elif data.startswith(">v="):
                dataList = data.split("\t")[1:]
                try:
                    int(dataList[0]) 
                except:
                    return 
                lo = _map(float(dataList[0]), 0, 1023, 0, 5)
                self.y = np.append(self.y[1:], lo) 
                self.x = np.append(self.x[1:], self.x[-1] + self.sampTimeDiv)
                # self.y = np.append(self.y, lo) 
                # self.x = np.append(self.x, self.x[-1] + self.sampTimeDiv)

            elif data.startswith(">tTotalReal"):
                tTotalRealData = data.replace(">tTotalReal", "")
                try:
                    self.sampDtTotal = float(tTotalRealData.strip())
                except ValueError:
                    pass
                # print("tTotalReal value is ", tTotalRealData)
                
            else:
                self.y = np.append(self.y[1:], 0) 
                self.x = np.append(self.x[1:], self.x[-1] + self.sampTimeDiv)
                # self.y = np.append(self.y, 0)
                # self.x = np.append(self.x, self.x[-1] + self.sampTimeDiv)

                self.curve.setData(self.x, self.y)

        else:
            pass
            

        # update graph
        now = time.time()
        dtt = now - self.lastTime
        self.lastTime = now
        
        if dtt != 0.0:
            if self.fps is None:
                self.fps = 1.0/dtt
            else:
                s = np.clip(dtt*3., 0, 1)
                self.fps = self.fps * (1-s) + (1.0/dtt) * s
        
        # self.graphView.setXRange(0.0, self.sampDtTotal, padding=0.5)
        self.graphView.setTitle('%0.2f fps' % self.fps)
        self.curve.setData(self.x, self.y)
        

    # *****************CALL BACK FUNCTIONS*******************#
    ####### Button Command CallBack Methods

    def powerButtonFunc(self):

        global _COMPORTs

        ######## WHEN POWER IS Set To ON.......
        if self.MainUi.ConfSerPowerButton.isChecked() == True:
            # change Power Button Look to On
            self.MainUi.ConfSerPowerButton.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.MainUi.ConfSerPowerButton.setText("Power ON")

            # Set default values system Wide
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.MainUi.SamplingControlVariousButton.setChecked(True)  # Set Various To default
            QTimer.singleShot(3000, lambda: self.SamplingControlVariousButtonCMD()) # and call the various function

            # Start Update Timer AND DISABLE REFRESH BUTTON

            self.MainUi.resetButton.setEnabled(False)

            # Main Serial Controls
            self.ser.baudrate = self.Baudrate
            self.ser.port = self.Port
            self.ser.open()
            self.timer.start(0)
            print(self.ser)

            # Send to the arduino the default settings

        
            # self.timerGraph = QtCore.QTimer()
            # self.timerGraph.singleShot(3000, lambda: self.wrireSerail("vo"))
            # self.timer.start()



        ######## WHEN POWER IS SET TO OFF.........
        elif (self.MainUi.ConfSerPowerButton.isChecked() == False):

            # ****** CLOSE THE SERIAL PORT AND ENABLE RESET BUTTON *****#
            self.ser.close()
            self.MainUi.resetButton.setEnabled(True)

            # change Power Button Look To Off
            self.MainUi.ConfSerPowerButton.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.MainUi.ConfSerPowerButton.setText("Power OFF")

            # Swith Off every Default Set Buttons
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.MainUi.SamplingControlVariousButton.setChecked(False)

            # Reset The COM Port List
            self.refreshComPorts()

            # Stop Update Timer
            self.timer.stop()

    def saveDataToTxtFile(self):
        saveDatafileType = self.MainUi.SaveDataFileFormatCombo.currentText()

        data = self.readData
        dataDestination = "SavedData\\Data--{}.{}".format(
            str(datetime.datetime.today()).replace(" ", "--").replace(".", "-").replace(":", "-"), saveDatafileType)
        altDataDestination = "Data--{}.{}".format(
            str(datetime.datetime.today()).replace(" ", "--").replace(".", "-").replace(":", "-"), saveDatafileType)
        savedFileName = dataDestination.split("\\")[1]

        if saveDatafileType == "txt":
            ### Convert data to numbered data before writing

            try:
                with open(dataDestination, "w") as foTxt:
                    foTxt.write(data)
                self.MainUi.statusbar.showMessage(
                    "TXT File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)
            except:
                cdw = os.getcwd()
                saveDirectory = "\\".join(cdw.split("\\")[:-1]) + "\SavedData"
                os.chdir(saveDirectory)

                with open(altDataDestination, "w") as foTxt:
                    foTxt.write(data)
                self.MainUi.statusbar.showMessage(
                    "TXT File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)



        elif saveDatafileType == "json":
            ### Convert data to dictionary before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foJson:
                json.dump(data, foJson, indent=2)
            self.MainUi.statusbar.showMessage("JSON File Saved As {} under 'SavedData' Folder ".format(savedFileName),
                                              5000)

        elif saveDatafileType == "csv":
            ### Convert data to comma separated values before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foCsv:
                foCsv.write(data)
            self.MainUi.statusbar.showMessage("CSV File Saved As {} under 'SavedData' Folder ".format(savedFileName),
                                              5000)

        elif saveDatafileType == "xml":
            ### Convert data to xml firmat before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foXml:
                foXml.write(data)
            self.MainUi.statusbar.showMessage("XML File Saved As {} under 'SavedData' Folder ".format(savedFileName),
                                              5000)

    def SamplingControlFlowButtonCMD(self):

        if self.MainUi.SamplingControlFlowButton.isChecked():
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlVariousButton.setChecked(False)
            self.wrireSerail("fo")
        else:
            self.wrireSerail("fx")

    def SamplingControlOnceButtonCMD(self):

        if self.MainUi.SamplingControlOnceButton.isChecked():
            self.MainUi.SamplingControlVariousButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.wrireSerail("1")

            self.MainUi.SamplingControlOnceButton.setChecked(False)

    def SamplingControlVariousButtonCMD(self):

        if self.MainUi.SamplingControlVariousButton.isChecked():
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.wrireSerail("vo")
        else:
            self.wrireSerail("vx")

    def resetButtonCMD(self):

        self.refreshComPorts()

        print("reset")

    ######## Slider Command CallBack Methods
    def Channel1VoltsSliderCMD(self):
        val = self.Get_Channel1VoltsSliderValue  # Value In miliVolts

        #### Change Volts Label Values
        if (val < 1):
            val = val * 1e3
            self.MainUi.Channel1VLabel.setText("{:.1f} mV/Div".format(val))
        elif (val >= 1):
            self.MainUi.Channel1VLabel.setText("{:.2f} V/Div".format(val))

        print(self.Get_Channel1VoltsSliderValue)

    def Channel1MsSliderCMD(self):

        #### Change Channel Ms/Div Label
        val = self.Get_Channel1MsSliderValue
        Rawval = self.Get_Channel1MsSliderValue / 1e-6
        if (Rawval < 1e3):
            self.MainUi.Channel1MsLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval >= 1e3) and (Rawval < 1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.Channel1MsLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval >= 1e6):
            self.MainUi.Channel1MsLabel.setText("{:.2f} S/Div".format(val))

    def SigGenFreqSliderCMD(self):
        #### set signal genarator period T
        T = 1 / self.Get_SigGenFreqSliderValue
        self.Set_SigGenPeriodSliderValue(T)

        #### Change Sig Freq Label Values
        val = self.Get_SigGenFreqSliderValue
        if (val < 1):
            val = val * 1e3
            self.MainUi.SigGenFreqLabel.setText("f {:.1f}mHz".format(val))
        elif (val >= 1) and (val < 1e3):
            self.MainUi.SigGenFreqLabel.setText("f {:.2f}Hz".format(val))
        elif (val >= 1e3):
            val = val / 1e3
            self.MainUi.SigGenFreqLabel.setText("f {:.2f}kHz".format(val))

    def SigGenPeriodSliderCMD(self):
        #### Set The Signal Gen Freq F
        F = 1 / self.Get_SigGenPeriodSliderValue
        self.Set_SigGenFreqSliderValue(F)

        #### Change Signal Period Label
        val = self.Get_SigGenPeriodSliderValue
        Rawval = self.Get_SigGenPeriodSliderValue / 1e-6
        if (Rawval < 1e3):
            self.MainUi.SigGenPeriodLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval >= 1e3) and (Rawval < 1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SigGenPeriodLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval >= 1e6):
            self.MainUi.SigGenPeriodLabel.setText("{:.2f} S/Div".format(val))

    def SigGenDutysliderCMD(self):

        #### Change Volts Label Values
        val = self.MainUi.SigGenDutyslider.value()
        self.MainUi.SigGenDutyLabel.setText("Duty {}%".format(val))

    def SampConrolDTScaleCMD(self):
        ## Change Sampling Value
        self.SampilngValue = self.Get_SampConrolDTScaleValue * self.MainUi.SampControlQScale.value()

        ############# Set Cahnnel ms-Div Values
        #### Channel 1
        Ch1MsVal = self.SampilngValue / 10
        self.Set_Channel1MsSliderValue(Ch1MsVal)

        print("samp val = ", self.SampilngValue)

        #### Change Signal Period Label
        val = self.Get_SampConrolDTScaleValue
        Rawval = self.Get_SampConrolDTScaleValue / 1e-6
        if (Rawval < 1e3):
            self.MainUi.SampConrolDTLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval >= 1e3) and (Rawval < 1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SampConrolDTLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval >= 1e6):
            self.MainUi.SampConrolDTLabel.setText("{:.2f} S/Div".format(val))


        #### Change 'Sampling Control Value' text
        val = self.SampilngValue
        Rawval = self.SampilngValue / 1e-6
        if (Rawval < 1e3):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} uS)".format(Rawval))
        elif (Rawval >= 1e3) and (Rawval < 1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} mS)".format(_Rawval))
        elif (Rawval >= 1e6):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} S)".format(val))

    def SampControlQScaleCMD(self):

        ## Set Sampling Value
        self.SampilngValue = self.Get_SampConrolDTScaleValue * self.MainUi.SampControlQScale.value()

        #### Change Volts Label Values
        val = self.MainUi.SampControlQScale.value()
        self.MainUi.SampControlQLabel.setText("q {}".format(val))

        #### Change 'Sampling Control Value' text
        val = self.SampilngValue
        Rawval = self.SampilngValue / 1e-6
        if (Rawval < 1e3):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} uS)".format(Rawval))
        elif (Rawval >= 1e3) and (Rawval < 1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} mS)".format(_Rawval))
        elif (Rawval >= 1e6):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} S)".format(val))



    ####### ComboBox CallbBacks
    def ConfSerComPortComboCMD(self):

        '''enable power only if a comport is selected'''
        if self.MainUi.ConfSerComPortCombo.currentText() != "":
            self.MainUi.ConfSerPowerButton.setEnabled(True)
            self.Port = self.MainUi.ConfSerComPortCombo.currentText()
        else:
            self.MainUi.ConfSerPowerButton.setChecked(False)
            self.MainUi.ConfSerPowerButton.setEnabled(False)
            self.powerButtonFunc()

    def ConfSerBaoudRateComboCMD(self):

        self.Baudrate = self.MainUi.ConfSerBaoudRateCombo.currentText()

    # *****************END OF CALL BACK FUNCTIONS*******************#

    # @@@@@@@@@@@@@@@@ Slider Value Methods <Get And Set>@@@@@@@@@@@@@@@@@@@@@#
    #### Channel1MsSlider
    @property
    def Get_Channel1MsSliderValue(self):
        val = self.MainUi.Channel1MsSlider.value()
        """
        convertion calculations
        """
        if (val < 50):
            val = _map(val, 0, 49, 20, (1e3 - 1))
        elif (val >= 50) and (val < 175):
            val = _map(val, 50, 174, 1e3, (1e6 - 1))
        elif (val >= 175):
            val = _map(val, 175, 200, 1e6, 20e6)

        return (val * 1e-6)

    def Set_Channel1MsSliderValue(self, val):
        val = (val / 1e-6)
        """
        convertion calculations
        """
        if (val < 1e3):
            val = _map(val, 20, (1e3 - 1), 0, 49)
        elif (val >= 1e3) and (val < 1e6):
            val = _map(val, 1e3, (1e6 - 1), 50, 174)
        elif (val >= 1e6):
            val = _map(val, 1e6, 20e6, 175, 200)

        self.MainUi.Channel1MsSlider.setValue(val)

    #### Channel1VoltsSlider
    @property
    def Get_Channel1VoltsSliderValue(self):
        """Return the Voltage pre Divition Of the Channel in volts"""
        val = self.MainUi.Channel1VoltsSlider.value()

        if (val < 65):
            val = _map(val, 0, 64, 10, (1e3 - 1))
        elif (val >= 65):
            val = _map(val, 65, 100, 1e3, 20e3)

        return (val / 1e3)

    def Set_Channel1VoltsSliderValue(self, val):
        """set the Voltage pre Divition Of the Channel, 'val' in volts"""

        val = val * 1e3

        if (val < 1e3):
            val = _map(val, 10, (1e3 - 1), 0, 64)
        elif (val >= 1e3):
            val = _map(val, 1e3, 20e3, 65, 100)
        self.MainUi.Channel1VoltsSlider.setValue(val)

    #### SigGenFreqSlider
    @property
    def Get_SigGenFreqSliderValue(self):
        """Return the Frequency Of the signal Genarator in Hz """
        val = self.MainUi.SigGenFreqSlider.value()
        """
        convertion calculations
        """
        if (val < 75):
            val = _map(val, 0, 74, 0.125, 0.9999)
        elif (val >= 75) and (val < 225):
            val = _map(val, 75, 224, 1, 99)
        elif (val >= 225) and (val < 425):
            val = _map(val, 225, 424, 100, (1e3 - 1))
        elif (val >= 425):
            val = _map(val, 425, 500, 1e3, 10e3)

        return val

    def Set_SigGenFreqSliderValue(self, val):
        """Set The Signal Genarator Value To 'val' Hz"""
        # convertion calculations
        if (val < 1):
            val = _map(val, 0.125, 0.9999, 0, 74)
        elif (val >= 1) and (val < 100):
            val = _map(val, 1, 99, 75, 224)
        elif (val >= 100) and (val < 1e3):
            val = _map(val, 100, (1e3 - 1), 225, 424)
        elif (val >= 1e3):
            val = _map(val, 1e3, 10e3, 425, 500)

        self.MainUi.SigGenFreqSlider.setValue(val)

    #### SigGenPeriodSlider
    @property
    def Get_SigGenPeriodSliderValue(self):
        """Return the Period of the Signal Genarator In Seconds"""
        val = self.MainUi.SigGenPeriodSlider.value()

        # convertion calculations
        if (val < 50):
            val = _map(val, 0, 49, 100, (1e3 - 1))
        elif (val >= 50) and (val < 185):
            val = _map(val, 50, 184, 1e3, (1e6 - 1))
        elif (val >= 185):
            val = _map(val, 185, 200, 1e6, 8e6)

        return (val * 1e-6)

    def Set_SigGenPeriodSliderValue(self, val):
        """Set value of the Signal Genarator 'val' in Seconds"""
        val = (val / 1e-6)
        # convertion calculations
        if (val < 1e3):
            val = _map(val, 100, (1e3 - 1), 0, 49)
        elif (val >= 1e3) and (val < 1e6):
            val = _map(val, 1e3, (1e6 - 1), 50, 184)
        elif (val >= 1e6):
            val = _map(val, 1e6, 8e6, 185, 200)

        self.MainUi.SigGenPeriodSlider.setValue(val)

    ### SampConrolDTScale
    @property
    def Get_SampConrolDTScaleValue(self):
        """Get the Sampling dt value in seconds"""
        val = self.MainUi.SampConrolDTScale.value()
        """
        convertion calculations
        """
        if (val < 50):
            val = _map(val, 0, 49, 10, (1e3 - 1))
        elif (val >= 50) and (val < 190):
            val = _map(val, 50, 189, 1e3, (1e6 - 1))
        elif (val >= 190):
            val = _map(val, 190, 200, 1e6, 2e6)

        return (val * 1e-6)

    def Set_SampConrolDTScaleValue(self, val):
        """set the Sampling dt Value, 'val' in seconds"""
        val = (val / 1e-6)
        # convertion calculations
        if (val < 1e3):
            val = _map(val, 10, (1e3 - 1), 0, 49)
        elif (val >= 1e3) and (val < 1e6):
            val = _map(val, 1e3, (1e6 - 1), 50, 189)
        elif (val >= 1e6):
            val = _map(val, 1e6, 2e6, 190, 200)

        self.MainUi.SampConrolDTScale.setValue(val)

    # @@@@@@@@@@@@@@@@@@@@ END OF SLIDER VALUE METHODS @@@@@@@@@@@@@@@@@@@@@@@@@@#

    def refreshComPorts(self):
        """Clear Then Add New Available COM Ports"""
        previousCOMPort = self.MainUi.ConfSerComPortCombo.currentIndex()  # get the previously selected port

        _COMPORTs = []  # reset the ports list
        _COMPORTs = serialPorts.list_ports()  # get new ports list
        self.MainUi.ConfSerComPortCombo.clear()  # reset ports list combo box
        self.MainUi.ConfSerComPortCombo.addItems([""] + _COMPORTs)  # add the new port list to the combo box

        self.MainUi.ConfSerComPortCombo.setCurrentIndex(previousCOMPort)  # set back previous port if available

    def Channel1CheckCMD(self):

        if self.MainUi.Channel1Check.isChecked():
            self.wrireSerail("c0o")
        else:
            self.wrireSerail("c0x")

    # =========================== Serial Methods ================================#

    def readSerial(self):

        if self.ser.in_waiting > 0:

            ## Read data from serial
            data = self.ser.read_until(b"\r\n")
            # data = self.ser.read(self.ser.in_waiting)
            # data = self.ser.readline()
            # print(data)

            # data = data.decode("utf-8", errors='replace')
            data = data.decode("utf-8", errors='replace')

            # print("data = ", data)
            try:
                self.readData = int(data)
            except:
                self.readData = data

            # self.GrapgUpdateFunc()

            if data.startswith(">f=0"):
                # "['>f=0', '4e-3', '87', '82', '79', '83\r\n']"
            
                self.ch1Data = int(data.split("\t")[2])
            else:
                self.ch1Data = None

            return self.ch1Data

    def wrireSerail(self, data):

        data = bytes(data, "utf-8")
        if self.ser.is_open:
            self.ser.write(data)


# =============================================================================#


if __name__ == "__main__":
    w = QApplication([])
    app = Application()
    app.show()
    w.exec_()
