def SamplingTypeControl(self, what):
    if self.MainUi.SamplingControlFlowButton.isChecked():

        self.MainUi.SamplingControlOnceButton.setChecked(False)
        self.MainUi.SamplingControlVariousButton.setChecked(False)
        self.wrireSerail("1")

    elif self.MainUi.SamplingControlVariousButton.isChecked():

        self.MainUi.SamplingControlOnceButton.setChecked(False)
        self.MainUi.SamplingControlFlowButton.setChecked(False)
        self.wrireSerail("1")

    elif self.MainUi.SamplingControlOnceButton.isChecked():

        self.MainUi.SamplingControlVariousButton.setChecked(False)
        self.MainUi.SamplingControlFlowButton.setChecked(False)
        self.wrireSerail("1")