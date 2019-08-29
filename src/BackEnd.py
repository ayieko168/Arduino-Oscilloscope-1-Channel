# Main Imports
from PyQt4.QtGui import *
from PyQt4 import QtCore
from MainUI import *
#### System Imports
import datetime
#### Utility Imports
import json

def _map(value, in_min, in_max, out_min, out_max):
    """From scale value to calc val"""

    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

class Application(QMainWindow):

    def __init__(self):

        super().__init__()
        self.MainUi = Ui_MainWindow()
        self.MainUi.setupUi(self)
        # self.MainUi.toolBar.actionTriggered[QAction].connect(self.toolbtnpressed)

        ############## Main Window Widgets connections 
        ### Buttons
        self.MainUi.ConfSerPowerButton.clicked.connect(self.powerButtonFunc)
        self.MainUi.SaveDataButton.clicked.connect(self.saveDataToTxtFile)
        ### Sliders
        self.MainUi.Channel1VoltsSlider.valueChanged.connect(self.Channel1VoltsSliderCMD)
        self.MainUi.Channel1MsSlider.valueChanged.connect(self.Channel1MsSliderCMD)
        self.MainUi.SigGenFreqSlider.valueChanged.connect(self.SigGenFreqSliderCMD)
        self.MainUi.SigGenPeriodSlider.valueChanged.connect(self.SigGenPeriodSliderCMD)
        self.MainUi.SigGenDutyslider.valueChanged.connect(self.SigGenDutysliderCMD)
        self.MainUi.SampConrolDTScale.valueChanged.connect(self.SampConrolDTScaleCMD)
        self.MainUi.SampControlQScale.valueChanged.connect(self.SampControlQScaleCMD)

        ############# Set Default Values and Global Variables
        
        self.SampilngValue = 0.0
        
        
        


#*****************CALL BACK FUNCTIONS*******************#
######## Button Command CallBack Methods
    def powerButtonFunc(self):
        ######## IF POWER IS ON.......
        if self.MainUi.ConfSerPowerButton.isChecked() == True:
            # change Power Button Look to On
            self.MainUi.ConfSerPowerButton.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.MainUi.ConfSerPowerButton.setText("Power ON")
            
            # Set default values system Wide
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.MainUi.SamplingControlVariousButton.setChecked(True) #Set Various To default

        ######## IF POWER IS OFF.........
        else:
            # change Power Button Look To Off
            self.MainUi.ConfSerPowerButton.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.MainUi.ConfSerPowerButton.setText("Power OFF")
            
            # Swith Off every Default Set Buttons
            self.MainUi.SamplingControlOnceButton.setChecked(False)
            self.MainUi.SamplingControlFlowButton.setChecked(False)
            self.MainUi.SamplingControlVariousButton.setChecked(False)

    def saveDataToTxtFile(self):
        saveDatafileType = self.MainUi.SaveDataFileFormatCombo.currentText()

        data = "No Data"
        dataDestination = "SavedData\\Data--{}.{}".format(str(datetime.datetime.today()).replace(" ","--").replace(".", "-").replace(":", "-"), saveDatafileType)
        savedFileName = dataDestination.split("\\")[1]


        if saveDatafileType == "txt":
            ### Convert data to numbered data before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foTxt:
                foTxt.write(data)
            self.MainUi.statusbar.showMessage("TXT File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)
        
        elif saveDatafileType == "json":
            ### Convert data to dictionary before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foJson:
                json.dump(data, foJson, indent=2)
            self.MainUi.statusbar.showMessage("JSON File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)
        
        elif saveDatafileType == "csv":
            ### Convert data to comma separated values before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foCsv:
                foCsv.write(data)
            self.MainUi.statusbar.showMessage("CSV File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)
        
        elif saveDatafileType == "xml":
            ### Convert data to xml firmat before writing
            """
            Data convertion and cleanup
            """
            with open(dataDestination, "w") as foXml:
                foXml.write(data)
            self.MainUi.statusbar.showMessage("XML File Saved As {} under 'SavedData' Folder ".format(savedFileName), 5000)

######## Slider Command CallBack Methods
    def Channel1VoltsSliderCMD(self):
        val = self.Get_Channel1VoltsSliderValue # Value In miliVolts

        #### Change Volts Label Values
        if(val<1e3):
            self.MainUi.Channel1VLabel.setText("{:.1f} mV/Div".format(val))
        elif(val>=1e3):
            val = val / 1e3
            self.MainUi.Channel1VLabel.setText("{:.2f} V/Div".format(val))
        
        print(self.Get_Channel1VoltsSliderValue)
        
    def Channel1MsSliderCMD(self):

        #### Change Channel Ms/Div Label
        val = self.Get_Channel1MsSliderValue
        Rawval = self.Get_Channel1MsSliderValue / 1e-6
        if (Rawval<1e3):
            self.MainUi.Channel1MsLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval>=1e3) and (Rawval<1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.Channel1MsLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval>=1e6):
            self.MainUi.Channel1MsLabel.setText("{:.2f} S/Div".format(val))
            
    def SigGenFreqSliderCMD(self):
        #### set signal genarator period T
        T = 1 / self.Get_SigGenFreqSliderValue
        self.Set_SigGenPeriodSliderValue(T)

        #### Change Sig Freq Label Values
        val = self.Get_SigGenFreqSliderValue
        if(val<1):
            val = val * 1e3
            self.MainUi.SigGenFreqLabel.setText("f {:.1f}mHz".format(val))
        elif (val>=1) and (val<1e3):
            self.MainUi.SigGenFreqLabel.setText("f {:.2f}Hz".format(val))
        elif (val>=1e3):
            val = val / 1e3
            self.MainUi.SigGenFreqLabel.setText("f {:.2f}kHz".format(val))

    def SigGenPeriodSliderCMD(self):
        #### Set The Signal Gen Freq F
        F = 1 / self.Get_SigGenPeriodSliderValue
        self.Set_SigGenFreqSliderValue(F)

        #### Change Signal Period Label
        val = self.Get_SigGenPeriodSliderValue
        Rawval = self.Get_SigGenPeriodSliderValue / 1e-6
        if (Rawval<1e3):
            self.MainUi.SigGenPeriodLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval>=1e3) and (Rawval<1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SigGenPeriodLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval>=1e6):
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
        if (Rawval<1e3):
            self.MainUi.SampConrolDTLabel.setText("{:.1f} uS/Div".format(Rawval))
        elif (Rawval>=1e3) and (Rawval<1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SampConrolDTLabel.setText("{:.1f} mS/Div".format(_Rawval))
        elif (Rawval>=1e6):
            self.MainUi.SampConrolDTLabel.setText("{:.2f} S/Div".format(val))
        
        #### Change 'Sampling Control Value' text
        val = self.SampilngValue
        Rawval = self.SampilngValue / 1e-6
        if (Rawval<1e3):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} uS)".format(Rawval))
        elif (Rawval>=1e3) and (Rawval<1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} mS)".format(_Rawval))
        elif (Rawval>=1e6):
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
        if (Rawval<1e3):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} uS)".format(Rawval))
        elif (Rawval>=1e3) and (Rawval<1e6):
            _Rawval = Rawval / 1e3
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} mS)".format(_Rawval))
        elif (Rawval>=1e6):
            self.MainUi.SamplingControlsFrame.setTitle("Sampling Contorls ({:.1f} S)".format(val))


#*****************END OF CALL BACK FUNCTIONS*******************#

#@@@@@@@@@@@@@@@@ Slider Value Methods <Get And Set>@@@@@@@@@@@@@@@@@@@@@#
#### Channel1MsSlider
    @property
    def Get_Channel1MsSliderValue(self):
        val = self.MainUi.Channel1MsSlider.value()
        """
        convertion calculations
        """
        if (val<50):
            val = _map(val, 0, 49, 20, (1e3-1))
        elif (val>=50) and (val<175):
            val = _map(val, 50, 174, 1e3, (1e6-1))
        elif (val>=175):
            val = _map(val, 175, 200, 1e6, 20e6)

        return (val * 1e-6)
    
    def Set_Channel1MsSliderValue(self, val):
        val = (val / 1e-6)
        """
        convertion calculations
        """
        if (val<1e3):
            val = _map(val, 20, (1e3-1), 0, 49)
        elif (val>=1e3) and (val<1e6):
            val = _map(val, 1e3, (1e6-1), 50, 174)
        elif (val>=1e6):
            val = _map(val, 1e6, 20e6, 175, 200)

        self.MainUi.Channel1MsSlider.setValue(val)
#### Channel1VoltsSlider
    @property
    def Get_Channel1VoltsSliderValue(self):
        val = self.MainUi.Channel1VoltsSlider.value() 
        """
        convertion calculations
        """
        if (val<65):
            val = _map(val, 0, 64, 10, (1e3-1))
        elif (val>=65):
            val = _map(val, 65, 100, 1e3, 20e3)

        return val
    
    def Set_Channel1VoltsSliderValue(self, val):
        """
        convertion calculations
        """
        if (val<1e3):
            val = _map(val, 10, (1e3-1), 0, 64)
        elif (val>=1e3):
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
        if (val<75):
            val = _map(val, 0, 74, 0.125, 0.9999)
        elif (val>=75) and (val<225):
            val = _map(val, 75, 224, 1, 99)
        elif (val>=225) and (val<425):
            val = _map(val, 225, 424, 100, (1e3-1))
        elif (val>=425):
            val = _map(val, 425, 500, 1e3, 10e3)
            
        return val
    
    def Set_SigGenFreqSliderValue(self, val):
        """Set The Signal Genarator Value To 'val' Hz"""
        # convertion calculations
        if (val<1):
            val = _map(val, 0.125, 0.9999, 0, 74)
        elif (val>=1) and (val<100):
            val = _map(val, 1, 99, 75, 224)
        elif (val>=100) and (val<1e3):
            val = _map(val, 100, (1e3-1), 225, 424)
        elif (val>=1e3):
            val = _map(val, 1e3, 10e3, 425, 500)

        self.MainUi.SigGenFreqSlider.setValue(val)
#### SigGenPeriodSlider
    @property
    def Get_SigGenPeriodSliderValue(self):
        """Return the Period of the Signal Genarator In Seconds"""
        val = self.MainUi.SigGenPeriodSlider.value()

        #convertion calculations
        if (val<50):
            val = _map(val, 0, 49, 100, (1e3-1))
        elif (val>=50) and (val<185):
            val = _map(val, 50, 184, 1e3, (1e6-1))
        elif (val>=185):
            val = _map(val, 185, 200, 1e6, 8e6)

        return (val * 1e-6)
    
    def Set_SigGenPeriodSliderValue(self, val):
        """Set value of the Signal Genarator 'val' in Seconds"""
        val = (val /1e-6)
        #convertion calculations
        if (val<1e3):
            val = _map(val, 100, (1e3-1), 0, 49)
        elif (val>=1e3) and (val<1e6):
            val = _map(val, 1e3, (1e6-1), 50, 184)
        elif (val>=1e6):
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
        if (val<50):
            val = _map(val, 0, 49, 10, (1e3-1))
        elif (val>=50) and (val<190):
            val = _map(val, 50, 189, 1e3, (1e6-1))
        elif (val>=190):
            val = _map(val, 190, 200, 1e6, 2e6)

        return (val * 1e-6)
    
    def Set_SampConrolDTScaleValue(self, val):
        """set the Sampling dt Value, 'val' in seconds"""
        val = (val / 1e-6)
        #convertion calculations
        if (val<1e3):
            val = _map(val, 10, (1e3-1), 0, 49)
        elif (val>=1e3) and (val<1e6):
            val = _map(val, 1e3, (1e6-1), 50, 189)
        elif (val>=1e6):
            val = _map(val, 1e6, 2e6, 190, 200)

        self.MainUi.SampConrolDTScale.setValue(val)


#@@@@@@@@@@@@@@@@@@@@ END OF SLIDER VALUE METHODS @@@@@@@@@@@@@@@@@@@@@@@@@@#

    
print(1-1e-3)




























if __name__ == "__main__":
    
    w = QApplication([])
    app = Application()
    app.show()
    w.exec_()