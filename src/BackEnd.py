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

        # Main Window Widgets connections 
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

        self.Set_Channel1MsSliderValue(10e3)



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
        print(self.Get_Channel1VoltsSliderValue)

    def Channel1MsSliderCMD(self):

        print(self.Get_Channel1MsSliderValue)
    
    def SigGenFreqSliderCMD(self):
        val = self.MainUi.SigGenFreqSlider.value()

        print(val)

    def SigGenPeriodSliderCMD(self):
        val = self.MainUi.SigGenPeriodSlider.value()

        print(val)

    def SigGenDutysliderCMD(self):
        val = self.MainUi.SigGenDutyslider.value()

        print(val)

    def SampConrolDTScaleCMD(self):
    
        print(self.MainUi.SampConrolDTScale.value())

    def SampControlQScaleCMD(self):
        val = self.MainUi.SampControlQScale.value()

        print(val)


#*****************END OF CALL BACK FUNCTIONS*******************#

#@@@@@@@@@@@@@@@@ Slider Value Classes And Methods @@@@@@@@@@@@@@@@@@@@@#
#### Channel1MsSlider
    @property
    def Get_Channel1MsSliderValue(self):
        val = self.MainUi.Channel1MsSlider.value()
        """
        convertion calculations
        """
        if (val<=25):
            val = _map(val, 0, 25, 20, 1e3)
        elif (val>25) and (val<=75):
            val = _map(val, 26, 75, (1e3+1), 1e6)
        elif (val>75):
            val = _map(val, 76, 100, (1e6+1), 20e6)

        return val
    
    def Set_Channel1MsSliderValue(self, val):
        """
        convertion calculations
        """
        if (val<=20):
            val = _map(val, 20, 1e3, 0, 25)
        elif (val>1e3) and (val<=1e6):
            val = _map(val, (1e3+1), 1e6, 26, 75)
        elif (val>1e6):
            val = _map(val, (1e6+1), 20e6, 76, 100)

        self.MainUi.Channel1MsSlider.setValue(val)
#### Channel1VoltsSlider
    @property
    def Get_Channel1VoltsSliderValue(self):
        val = self.MainUi.Channel1VoltsSlider.value()
        """
        convertion calculations
        """
        return val
    
    def Set_Channel1VoltsSliderValue(self, val):
        """
        convertion calculations
        """
        self.MainUi.Channel1VoltsSlider.setValue(val)


#@@@@@@@@@@@@ END OF SLIDER VALUE METHODS @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

    































if __name__ == "__main__":
    
    w = QApplication([])
    app = Application()
    app.show()
    w.exec_()