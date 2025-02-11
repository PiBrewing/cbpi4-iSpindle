# CraftBeerPi4 iSpindle Sensor Plugin


- Data Transfer from the Spindle itself to Craftbeerpi4
- The Spindel Connection needs to be set to HTTP as shown in the image below
- For Server, please enter the IP address of your CBPi4 Server.
- Enter 8000 for Port and '/api/hydrometer/v1/data' for path.

![iSpindle Settings](https://github.com/PiBrewing/cbpi4-iSpindle/blob/main/Spindle_Connection_Settings.png?raw=true)

## Software installation:

Please have a look at the [Craftbeerpi4 Documentation](https://openbrewing.gitbook.io/craftbeerpi4_support/readme/plugin-installation)

- Package name: cbpi4-ispindle
- Package link: https://github.com/PiBrewing/cbpi4-ispindle/archive/main.zip

## Transfer of spindle data to SQL database:

- Minimum Requirements: CBPi4: 4.5.0 | User Interface: 0.3.18

- If you want to store the spindle data for each of your brews in a database and archive them for later, you need to install and configure a database on the pi or you can use just a sql database on a different sever (e.g. NAS) if available.
- If you use a database not directly on your pi, it is important that you configure the [database for access from other hosts than just localhost](https://dev.mysql.com/blog-archive/the-bind-address-option-now-supports-multiple-addresses/).

### Installation and configuration of mariadb on you pi_

Install the apache server if it is not already installed on your system (not required for the afoementioned bookworm 64 bit full): 

	sudo apt-get install apache2

You also might need to install php as this is not automtically installed on recent images (also not required on bookworm 64 bit full):

	sudo apt-get install php8.2 libapache2-mod-php8.2 php8.2-mbstring php8.2-mysql php8.2-curl php8.2-gd php8.2-zip -y
	
You need to install MariaDB on the Raspi. (Mysql should also work)

	sudo apt install mariadb-server

Configure the database:

	sudo mysql_secure_installation

Enter a password for the datase user root during the configuration

Add a user (e.g. pi) to the database that has all privileges to create also the iSpindle database during setup (Password as example here: 'PiSpindle'):
	
	sudo mysql --user=root mysql

```
	CREATE USER 'pi'@'localhost' IDENTIFIED BY 'PiSpindle';
	GRANT ALL PRIVILEGES ON *.* TO 'pi'@'localhost' WITH GRANT OPTION;
	FLUSH PRIVILEGES;
	QUIT;
```

Install phpmyadmin:

	sudo apt-get install phpmyadmin

Select apache2 as webserver if you installed this before.
Configure the database: yes 
enter database root password you have choosen during the mariadb installation
define a phpmyadmin password.

## Database configuratrion

- If you want to use data transfer to sql database and the functionality in the user interface you must configure the global settings for the cbpi4-ispindle plugin in the cbpi4 settings page:

![iSpindle global sql settings](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_SQL_Settings.png?raw=true)

- Select Yes for Spindledata to activate the ui functions
- Select Yes for spinlde_SQL to activate the database functions for the spindle data (transfer of data to database, diagrams,...)
- 'iSpindle' is the recommended name for database and user.
- if you have installed the database on the same system as cbpi4, enter localhost for the host parameter nad 3306 for port, if you have not adapted the settings. If you want to use a different database (e.g. on your NAS), enter the correspondig IP and port of your external database.
- Enter a password you want to use for the user that is owner of the iSpindle database.
- Restart the server
- After restart you should see an additional menu item:

![iSpindle Menu Item](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Menu_Item.png?raw=true)

- Click on Spindledata and you should see a message, that the user you have entered has currently no access to the database. Click on the message.

![iSpindle No Connection](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Menu_no_connection.png?raw=true)

- Enter the user name you have created earlier in the command line (e.g. pi) and the password (e.g. PiSpindle) and click on create databse.

![iSpindle Create Database](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Menu_create_database.png?raw=true)

- The plugin will create the database and user and after a short moment, you should see this empty table:

![iSpindle Current data table](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Current_data.png?raw=true)

- Once you have configured a Spindle to send data to your cbpi4 server, the table should fill with data:

![iSpindle Current data table with data](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Current_data_with_data.png?raw=true)

- This Page has several buttons and you can select the SPindles that have sent data recently. 
- The button set recipe start should be used, if you place a spindle into your fermenter for a starting fermentation. It creates an entry in the database with the name of your fermentation (e.g. Kölsch)  and a batch (e.g. 2501 for the first batch in 2025)
- The refresh data button refreshes the page and you will see the latest data from the spindle if a new dataset has been sent.
- The button Show archive data will bring you to another page, where you can see all fermentations from your database and select different types of diagrams.
- PLEASE NOTE: You must enter calibration values for your spindle in the interface as some calculations are based on the server calculated gravity.

![iSpindle Calibration](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Calibration.png?raw=true)

- This can be done on the current data page if a spindle is not yet calibrated or from the archive page.
- Every time you start a new recipe, the current calibration for the spindle will be used for the archive. If you start a recipe and the spindle has not been calibrated yet, you can calibrate it later and transfer the current calibration to your archive (button on the archive page)

![iSpindle Archive](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_Archive_data.png?raw=true)


## Forwarding data to brewfather

- You can also forward the spindle data to brewfather. Therefore, you need to set 'brewfather_enable' to 'yes' and enter the corresponding settings.
- In the [brewfather app](https://web.brewfather.app/tabs/settings), you will find the correct settings for your spindle.
- The token you need to enter ist the token behind the '=' (e.g. /ispindel?id=ATRB43gfdyi) Token:ATRB43gfdyi
- Data can only be transferred every 15 minutes. Brewfather won't accept shorter cycles. 

![iSpindle Brewfather Configuration](https://github.com/PiBrewing/cbpi4-iSpindle/blob/development/Spindle_brewfather.png?raw=true)

## Alarm configuration

- Alarm parameters can be also set in the global settings.
- alarmlow: Sends an alarm once the current fermentation (after new recipe start) is below the alarm value (e.g. 4.5) raises an alarm / notification, once the gravity reaches a value below 4.5 °P.
- alarmsvg: Sends an alarm once the attenuation (after new recipe start) is below the alarm value (e.g. 60) raises an alarm / notification, once the attenuation reaches a value above 60%.
- dailyalarm: If set to yes, a status message of each acitve spindle will be send once a day.
- statusupdate: defines the time, when the daily alarm will be send.

## Sensor Configuration

- Add Hardware under Sensor and choose iSpindle as Type
- If you want to retrieve multiple parameters from one Spindle, you need to add the Spindle several times as sensor and choose different Types
- The Sensor name should be different for each of your sensors
- The settings are shown below.
    - Name: This is the name of your sensor shown in CBPi4. e.g. iSpindleXXX - Angle
    - iSpindle: Name of your Spindle that you entered in the Spindle setup page. This name must match to the Spindle. Otherwise no data will be collected.
    - Type: Temperature, Gravity/Angle, Battery (Choose one type)
        - If Gravity/Angle is choosen and the Polynomial field is left empty, the angle data is stored
    - Polynomial: The polynomial to calculate gravity. '^' is not working. You need to use 'tilt\*tilt\*tilt' for '^3' and 'tilt*tilt' for '^2'
    - Units: Choose SG, Brix or °P. This has impact on the calculated digits.
    - Sensor: Only useful in combination with the [iSpindle TCP Server](https://github.com/avollkopf/iSpindel-TCP-Server). If aforementioned server is forwarding iSpindle data to craftbeerpi, it can also read the fermenter temp sensor and store the data in the TCP server database in parallel to the iSpindle temeprature. If you have defined more than one sensor for one iSpindle (e.g. gravity and date of last measurement), you need to set the fermenter for both sensors.
	- GrainConnect_ServerURL: If you want to forward Spindle data to grainconnect, you can enter the correspondig server url for your spindle in this parameter (see also [here](https://community.grainfather.com/my-equipment) and click on setup instructions for your spindle, and copy the ServerURL into this field)

![CBPi4 Settings](https://github.com/PiBrewing/cbpi4-iSpindle/blob/main/Settings.png?raw=true)

### Changelog:

- xx.02.25: (1.0.0) Added sql database funcitonality from iSpindle TCP Server
- 25.06.23: (0.0.13) change logging from 'warning' to 'info'
- 10.06.23: (0.0.12) bump to release
- 06.03.23: (0.0.12.a2) Added DataType for datetime (TEST)
- 11.05.22: (0.0.10) Updated README (removed cbpi add)
- 10.05.22: (0.0.9) Removed cbpi dependency
- 16.01.22: (0.0.8) Adaption for cbpi 4.0.1.2
- 13.01.22: (0.0.7) Reduced mqtt traffic -> update only for new value
- 23.11.21: (0.0.6) Added RSSI to available parmeters
- 10.06.21: (0.0.5) Fix to improve UI behavior with respect to frequency of value update
- 17.04.21: Some small fixes
- 15.03.21: Changes to suppoer cbpi >= 4.0.0.31
