# Arduino-Oscilloscope-1-Channel
 One Channeled Arduino-based Oscilloscope.
 
 This software is an attempt at creating an arduino-based / software-based oscilloscope for those who can't afford 
 this essential electronics hobbyist instrument.
 
 This project was inspired by 
 
 NOTE: This project is not yet functional as an oscilloscope but can plot data from the arduino
 
# INSTALLATION
 #### Requirements
 Bellow is a list of the packages needed in python to run the oscilloscope software
 1. PyQt5
 2. collections
 3. numpy
 4. pyqtgraph
 5. pyserial
 6. glob
 
 #### Running the software
 In order to run the oscilloscope follow the steps bellow:
 * Upload the arduino code to your Arduino
 * Run the main program [python file](/src/BackEnd.py) i.e /src/BackEnd.py
 * Start the Oscilloscope and probe your projects!
 
 
# SCREENSHOTS
 Bellow is an image of the Osciloscope
 ![Inactive Oscilloscope Image](/Screenshot/Frontend-Inactive.JPG)
 
 This is an image of the oscilloscope plotting radom data from the Arduino
 ![Oscilloscope Active](/Screenshot/Frontend-Active.JPG)
 
 
# FUTURE ADVANCES
 In the future I want to:
 - [ ] Make the sliders easy to work with and interactive with the oscilloscope
 - [ ] Make the Oscilloscope functional at plotting data
 - [ ] Add the save raw data functionality
 - [ ] Make The signal generator functional
 - [ ] Advance to making a muti-channeled oscilloscope
 - [ ] Make the graphs detatchable
 - [ ] Make the multimeter functionality work
 - [ ] Make the multimeter work using multiplexing
 - [ ] Enable use of other microcontroller boards
 - [ ] Make the measure function work, for measurement of frequency and periods
 - [ ] Make the triger function work
 - [ ] Add Triger voltage seting feature
 - [ ] Add image Capture and Video Capture functionality
