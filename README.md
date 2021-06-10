# CraftBeerPi4 iSpindle Sensor Plugin

- Initial Version which has to be considered as beta
    - Data Transfer is working from the SPindle itself and from the TCP server via forward-
    - TCP Server does not require any changes. Only the port needs to be changed from 5000 to 8000
    - The Spindel Connection needs to be changed from CraftbeerPi to HTTP as shown in the image below
    - For Server, please enter the IP address of your CBPi4 Server.
    - Enter 8000 for Port and '/api/hydrometer/v1/data' for path.

![iSpindle Settings](https://github.com/avollkopf/cbpi4-iSpindle/blob/main/Spindle_Connection_Settings.png?raw=true)

- Installation: 
    - pip install cbpi4-iSpindle (or from the GIT repo)
    - cbpi add cbpi4-iSpindle
- Usage:
    - Add Hardware under Sensor and choose iSpindle as Type

- Units are currently not displayed in CBPi4 for Sensors. You need to add that on you own in the Dashboard
- If you want to retrieve multiple parameters from one Spindle, you need to add the Spindle several times as sensor and choose different Types
    - The Sensor name should be different for each of your sensors
- The settings are shown below.
    - Name: This is the name of your sensor shown in CBPi4. e.g. iSpindleXXX - Angle
    - iSpindle: Name of your Spindle that you entered in the Spindle setup page. This name must match to the Spindle. Otherwise no data will be collected.
    - Type: Temperature, Gravity/Angle, Battery (Choose one type)
        - If Gravity/Angle is choosen and the Polynomial field is left empty, the angle data is stored
    - Polynomial: The polynomial to calculate gravity. '^' is not working. You need to uses tilt*tilt*tilt for '^3' and tilt*tilt for '^2'
    - Units: Choose SG, Brix or °P. This has impact on the calculated digits

![CBPi4 Settings](https://github.com/avollkopf/cbpi4-iSpindle/blob/main/Settings.png?raw=true)

- Changelog:

	- 10.06.21: Fix to improve UI behavior with respect to frequency of value update
	- 15.03.21: Changes to suppoer cbpi >= 4.0.0.31
	- 17.04.21: Some small fixes
