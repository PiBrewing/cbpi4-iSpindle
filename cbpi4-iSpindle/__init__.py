
# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
from aiohttp import web
from cbpi.api import *
import re
import time
import json
from cbpi.api.config import ConfigType
from cbpi.api.dataclasses import DataType
import mysql.connector
import datetime
from json import JSONEncoder
from pandas import DataFrame

logger = logging.getLogger(__name__)

cache = {}

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

class iSpindleConfig(CBPiExtension):

    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_config())

    async def init_config(self):
        global parametercheck, sql_connection

        parametercheck=False
        sql_connection=False

        plugin = await self.cbpi.plugin.load_plugin_list("cbpi4-iSpindle")
        try:
            self.version=plugin[0].get("Version","0.0.0")
            self.name=plugin[0].get("Name","cbpi4-iSPindle")
        except:
            self.version="0.0.0"
            self.name="craftbeerpi"
        
        self.iSpindle_update = self.cbpi.config.get(self.name+"_update", None)
        await self.iSpindle_config()

        while parametercheck == False:
            await asyncio.sleep(1)
        
        if spindle_SQL == "Yes":
            cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
            cur = cnx.cursor()
            sqlselect = "SELECT VERSION()"
            cur.execute(sqlselect)
            results = cur.fetchone()
            ver = results[0]
            logger.warning("MySQL connection available. MySQL version: %s" % ver)
            sql_connection=True
            if (ver is None):
                logger.error("MySQL connection failed")
                        

    async def iSpindle_config(self):
        global spindledata, spindle_SQL, spindle_SQL_HOST, spindle_SQL_DB, spindle_SQL_TABLE, spindle_SQL_USER, spindle_SQL_PASSWORD, spindle_SQL_PORT, parametercheck
        parametercheck=False
        spindledata = self.cbpi.config.get("spindledata", None)
        if spindledata is None:
            logger.warning("INIT Spindledata extra page in UI")
            try:
                await self.cbpi.config.add("spindledata", "No", type=ConfigType.SELECT, description="Enable extra page for spindledata in ui",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                spindledata = self.cbpi.config.get("spindledata", "No")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindledata", spindledata, type=ConfigType.SELECT, description="Enable extra page for spindledata in ui",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL = self.cbpi.config.get("spindle_SQL", None)  # 1 to enable output to MySQL database
        if spindle_SQL is None:
            logger.warning("INIT Spindle database select for transfer")
            try:
                await self.cbpi.config.add("spindle_SQL", "No", type=ConfigType.SELECT, description="Enable transfer of Spindle data to SQL database",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL", "No")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL", spindle_SQL, type=ConfigType.SELECT, description="Enable transfer of Spindle data to SQL database",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_HOST = self.cbpi.config.get("spindle_SQL_HOST", None)  # Database host name (default: localhost - 127.0.0.1 loopback interface)
        if spindle_SQL_HOST is None:
            logger.warning("INIT Spindle database host name")
            try:
                await self.cbpi.config.add("spindle_SQL_HOST", "", type=ConfigType.STRING, description="SQL database host. e.g: localhost or IP address",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_HOST", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_HOST", spindle_SQL_HOST, type=ConfigType.STRING, description="SQL database host. e.g: localhost or IP address",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_DB = self.cbpi.config.get("spindle_SQL_DB", None)  # Database name
        if spindle_SQL_DB is None:
            logger.warning("INIT Spindle Database Name")
            try:
                await self.cbpi.config.add("spindle_SQL_DB", "", type=ConfigType.STRING, description="SQL database name",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_DB", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_DB", spindle_SQL_DB, type=ConfigType.STRING, description="SQL database name",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_TABLE = self.cbpi.config.get("spindle_SQL_TABLE", None)  # Table name
        if spindle_SQL_TABLE is None:
            logger.warning("INIT Spindle Database table Name")
            try:
                await self.cbpi.config.add("spindle_SQL_TABLE", "", type=ConfigType.STRING, description="SQL database table name",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_TABLE", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_TABLE", spindle_SQL_TABLE, type=ConfigType.STRING, description="SQL database table name",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_USER = self.cbpi.config.get("spindle_SQL_USER", None)  # DB user
        if spindle_SQL_USER is None:
            logger.warning("INIT Spindle Database user name")
            try:
                await self.cbpi.config.add("spindle_SQL_USER", "", type=ConfigType.STRING, description="SQL database user name",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_USER", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_USER", spindle_SQL_USER, type=ConfigType.STRING, description="SQL database user name",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_PASSWORD = self.cbpi.config.get("spindle_SQL_PASSWORD", None)  # DB user's password (change this)
        if spindle_SQL_PASSWORD is None:
            logger.warning("INIT Spindle Database password")
            try:
                await self.cbpi.config.add("spindle_SQL_PASSWORD", "", type=ConfigType.STRING, description="SQL database password",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_PASSWORD", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_PASSWORD", spindle_SQL_PASSWORD, type=ConfigType.STRING, description="SQL database password",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        spindle_SQL_PORT = self.cbpi.config.get("spindle_SQL_PORT", None)
        if spindle_SQL_PORT is None:
            logger.warning("INIT Spindle Database port number")
            try:
                await self.cbpi.config.add("spindle_SQL_PORT", "", type=ConfigType.NUMBER, description="SQL database port number",
                                                                                                    source=self.name)
                                                                                                            
                spindle_SQL = self.cbpi.config.get("spindle_SQL_PORT", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("spindle_SQL_PORT", spindle_SQL_PORT, type=ConfigType.NUMBER, description="SQL database port number",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')


        if self.iSpindle_update == None or self.iSpindle_update != self.version:
            try:
                 await self.cbpi.config.add(self.name+"_update", self.version,type=ConfigType.STRING, description='iSpindle Version Update', source='hidden')
            except Exception as e:
                logger.warning('Unable to update database')
                logger.warning(e)

        parametercheck=True


async def calcGravity(polynom, tilt, unitsGravity):
	if unitsGravity == "SG":
		rounddec = 3
	else:
		rounddec = 2

	# Calculate gravity from polynomial
	tilt = float(tilt)
	result = eval(polynom)
	result = round(float(result),rounddec)
	return result

@parameters([Property.Text(label="iSpindle", configurable=True, description="Enter the name of your iSpindel"),
             Property.Select("Type", options=["Temperature", "Gravity/Angle", "Battery", "RSSI", "DateTime"], description="Select which type of data to register for this sensor. For Angle, Polynomial has to be left empty"),
             Property.Text(label="Polynomial", configurable=True, description="Enter your iSpindel polynomial. Use the variable tilt for the angle reading from iSpindel. Does not support ^ character."),
             Property.Select("Units", options=["SG", "Brix", "°P"], description="Displays gravity reading with this unit if the Data Type is set to Gravity. Does not convert between units, to do that modify your polynomial."),
             Property.Sensor("FermenterTemp",description="Select Fermenter Temp Sensor that you want to provide to TCP Server")])

class iSpindle(CBPiSensor):
    
    def __init__(self, cbpi, id, props):
        super(iSpindle, self).__init__(cbpi, id, props)
        self.value = 0
        self.key = self.props.get("iSpindle", None)
        self.Polynomial = self.props.get("Polynomial", "tilt")
        self.temp_sensor_id = self.props.get("FermenterTemp", None)
        self.datatype = DataType.DATETIME if self.props.get("Type", None) == "DateTime" else DataType.VALUE
        self.time_old = 0

    def get_unit(self):
        if self.props.get("Type") == "Temperature":
            return "°C" if self.get_config_value("TEMP_UNIT", "C") == "C" else "°F"
        elif self.props.get("Type") == "Gravity/Angle":
            return self.props.Units
        elif self.props.get("Type") == "Battery":
            return "V"
        elif self.props.get("Type") == "RSSI":
            return "dB"
        else:
            return " "

    async def run(self):
        global cache
        global fermenter_temp
        Spindle_name = self.props.get("iSpindle") 
        while self.running == True:
            try:
                if (float(cache[self.key]['Time']) > float(self.time_old)):
                    self.time_old = float(cache[self.key]['Time'])
                    if self.props.get("Type") == "Gravity/Angle":
                        self.value = await calcGravity(self.Polynomial, cache[self.key]['Angle'], self.props.get("Units"))
                    elif self.props.get("Type") == "DateTime":
                        self.value=float(cache[self.key]['Time'])
                    else:
                        self.value = float(cache[self.key][self.props.Type])
                    self.log_data(self.value)
                    self.push_update(self.value)
                self.push_update(self.value,False)
                #self.cbpi.ws.send(dict(topic="sensorstate", id=self.id, value=self.value))
                
            except Exception as e:
                pass
            await asyncio.sleep(2)

    def get_state(self):
        return dict(value=self.value)

class iSpindleEndpoint(CBPiExtension):
    
    def __init__(self, cbpi):
        '''
        Initializer
        :param cbpi:
        '''
        self.pattern_check = re.compile("^[a-zA-Z0-9,.]{0,10}$")
        self.cbpi = cbpi
        self.sensor_controller : SensorController = cbpi.sensor
        # register component for http, events
        # In addtion the sub folder static is exposed to access static content via http
        self.cbpi.register(self, "/api/hydrometer/v1/data")

    async def run(self):
        await self.get_spindle_sensor()

    @request_mapping(path='', method="POST", auth_required=False)
    async def http_new_value3(self, request):
        import time
        """
        ---
        description: Get iSpindle Value
        tags:
        - iSpindle 
        parameters:
        - name: "data"
          in: "body"
          description: "Data"
          required: "name"
          type: "object"
          type: string
        responses:
            "204":
                description: successful operation
        """

        global cache
        try:
            data = await request.json()
        except Exception as e:
            print(e)
        logging.error(data)
        datatime = time.time()
        key = data['name']
        temp = round(float(data['temperature']), 2)
        angle = data['angle']
        battery = data['battery']

        try:
            rssi = data['RSSI']
        except:
            rssi = 0
        try:
            interval = data['interval']
        except:     
            interval = 0
        try:
            gravity = data['gravity']
        except:
            gravity = 0
        try:
            spindle_id = data['ID']
        except:
            spindle_id = 0
        try:
            temp_units = data['temp_units']
        except:
            temp_units = 'C'
        try:
            user_token = data['token']
        except:
            user_token = '*'

        cache[key] = {'Time': datatime,'Temperature': temp, 'Angle': angle, 'Battery': battery, 'RSSI': rssi}

        if spindle_SQL == "Yes":
            await self.send_data_to_sql(datatime, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token)
            pass

    async def send_data_to_sql(self, datatime, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token):
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()

        #get current recipe name
        recipe = 'n/a'
        try:
            sqlselect = (f"SELECT Data.Recipe FROM Data WHERE Data.Name = '{key}' AND Data.Timestamp >= (SELECT max( Data.Timestamp )FROM Data WHERE Data.Name = '{key}' AND Data.ResetFlag = true) LIMIT 1;")
            cur.execute(sqlselect)
            recipe_names = cur.fetchone()
            recipe = str(recipe_names[0])
        except Exception as e:
            logging.error(' Recipe Name not found - Database Error: ' + str(e))
        logging.info('Recipe Name: ' + recipe)

        #get current recipe id
        recipe_id = 0
        try:
            sqlselect = f"SELECT max(Archive.Recipe_ID) FROM Archive WHERE Archive.Name='{key}';"
            cur.execute(sqlselect)
            recipe_ids = cur.fetchone()
            recipe_id = str(recipe_ids[0])
            logging.info('Recipe_ID: Done. ' + recipe_id)
        except Exception as e:
            logging.error(' Recipe_ID not found - Database Error: ' + str(e))
        if recipe_id == "None":
            recipe_id = 0

        #logging.error('Recipe_ID: ' + recipe_id)
        #logging.error('Recipe: ' + recipe)
        #logging.error('Name: ' + key)
        #logging.error('Timestamp: ' + str(time))
        #logging.error('Temperature: ' + str(temp))
        #logging.error('Angle: ' + str(angle))
        #logging.error('Gravity: ' + str(gravity))
        #logging.error('Battery: ' + str(battery))
        #logging.error('RSSI: ' + str(rssi))
        #logging.error('Interval: ' + str(interval))
        #logging.error('Token: ' + str(user_token))
        #logging.error('Spindle_ID: ' + str(spindle_id))


        fieldlist = ['Timestamp', 'Name', 'ID', 'Angle', 'Temperature', 'Battery', 'Gravity', 'Recipe', 'Recipe_ID', 'RSSI', '`Interval`', 'UserToken']
        valuelist = [datetime.datetime.now(), key, spindle_id, angle, temp, battery, gravity, recipe, recipe_id, rssi, interval, str(user_token)]
  
        fieldstr = ', '.join(fieldlist)
        valuestr = ', '.join(['%s' for x in valuelist])

        add_sql = f"INSERT INTO Data ({fieldstr}) VALUES ({valuestr})"
        logging.info(add_sql)
        logging.info(valuelist)
        try:
            cur.execute(add_sql, valuelist)
            cnx.commit()
        except Exception as e:
            logging.error('Database Error: ' + str(e))





    @request_mapping(path='/gettemp/{SpindleID}', method="POST", auth_required=False)
    async def get_fermenter_temp(self, request):
        SpindleID = request.match_info['SpindleID']
        sensor_value = await self.get_spindle_sensor(SpindleID)
        data = {'Temp': sensor_value}
        return  web.json_response(data=data)

    async def get_spindle_sensor(self, iSpindleID = None):
        self.sensor = self.sensor_controller.get_state()
        for id in self.sensor['data']:
            if id['type'] == 'iSpindle':
                name= id['props']['iSpindle']
                if name == iSpindleID:
                    try:
                        sensor= id['props']['FermenterTemp']
                    except:
                        sensor = None
                    if (sensor is not None) and sensor != "":
                        sensor_value = self.cbpi.sensor.get_sensor_value(sensor).get('value')
                    else:
                        sensor_value = None
                    return sensor_value

    @request_mapping(path='/getarchive', method="GET", auth_required=False)
    async def get_archive_headers(self, request):
        """
        ---
        description: Get all stored fermentations from database archive
        tags:
        - iSpindle
        responses:
            "200":
                description: successful operation
        """

        data= await self.get_archive_list()
        return  web.json_response(data=data)
    

    async def get_archive_list(self):
        ORDER="DESC"
        archive_sql = "SELECT Recipe_ID as value, CONCAT(Batch, ' | ', Name, ' | ',DATE_FORMAT(Start_date, '%Y-%m-%d'),' | ', Recipe, ' (', Recipe_ID,')' ) as 'label' FROM Archive ORDER BY Recipe_ID {}".format(ORDER)
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        cur.execute(archive_sql)
        columns = [column[0] for column in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        return results

    @request_mapping(path='/getdiagrams', method="GET", auth_required=False)
    async def get_diagrams(self, request):
        """
        ---
        description: Get available diagrams
        tags:
        - iSpindle
        responses:
            "200":
                description: successful operation
        """

        data= await self.get_diagram_list()
        return  web.json_response(data=data)
  
    async def get_diagram_list(self):
        results = [{'value': '0', 'label': 'Gravity and Temperature (RasPySpindle)'},
                   {'value': '1', 'label': 'Gravity and Temperature (iSpindle Polynom)'},
                   {'value': '2', 'label': 'Tilt and Temperature'},
                   {'value': '3', 'label': 'Attenuation'},
                   {'value': '4', 'label': 'Battery and Wifi Signal'}]

        return results

    @request_mapping(path='/getarchiveheader/{ArchiveID}/', method="POST", auth_required=False)
    async def get_archive_header(self, request):
        """
        ---
        description: Get Archive header data for specified archive id
        tags:
        - iSpindle
        parameters:
        - name: "ArchiveID"
          in: "path"
          description: "ArchiveID"
          required: true
          type: "integer"
          format: "int64"
        responses:
            "200":
                description: successful operation
        """
        ArchiveID = request.match_info['ArchiveID']
        try:
            header_data = await self.get_archive_header_data(ArchiveID)
            #logger.error(header_data)
            return  web.json_response(data=header_data)
        except Exception as e:
            logger.error(e)
            return  web.json_response(status=500)
    
    async def get_archive_header_data(self, ArchiveID):
        result_angle=[] 

        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()

        #get other archive data
        archive_sql = "Select * FROM Archive WHERE Recipe_ID = {}".format(ArchiveID)
        cur.execute(archive_sql)
        columns = [column[0] for column in cur.description] 
        result_archive = [dict(zip(columns, row)) for row in cur.fetchall()]

        Spindle_Name=result_archive[0]['Name']
        SpindleID=result_archive[0]['ID']
        Batch=result_archive[0]['Batch']
        Recipe=result_archive[0]['Recipe']
        Start_date=result_archive[0]['Start_date']
        End_date=result_archive[0]['End_date']

        try:
            const0=result_archive[0]['const0']
            const1=result_archive[0]['const1']  
            const2=result_archive[0]['const2']
            const3=result_archive[0]['const3']
            calibrated=True
        except:
            const0=0.000000001
            const1=0.000000001
            const2=0.000000001
            const3=0.000000001
            calibrated=False

        if calibrated:
            if const0 == 0:
                forumla= "{:+.5f} * tilt^2 {:+.5f} * tilt {:+.5f}".format(const1, const2, const3)
            else:
                forumla= "{:+.5f} * tilt^3 {:+.5f} * tilt^2 {:+.5f} * tilt {:+.5f}".format(const0, const1, const2, const3)
        else:
            forumla="Not calibrated"


        #if no entry for end date in archive table, get last timestamp of last dataset for selected recipe from data table
        if End_date is None:
            get_end_date_sql = "SELECT max(Timestamp) FROM Data WHERE Recipe_ID = {}".format(ArchiveID)
            cur.execute(get_end_date_sql)
            columns = [column[0] for column in cur.description]
            result_end_date = [dict(zip(columns, row)) for row in cur.fetchall()]
            End_date=result_end_date[0]['max(Timestamp)']

        # check if end flag is set for the archive 
        RID_END=False
        check_RID_END = "SELECT * FROM Data WHERE Recipe_ID = {} AND Internal = 'RID_END'".format(ArchiveID)
        cur.execute(check_RID_END)
        columns = [column[0] for column in cur.description]
        result_RID_END = [dict(zip(columns, row)) for row in cur.fetchall()]
        if len(result_RID_END) > 0:
            End_date=result_RID_END[0]['Timestamp']
            RID_END=True
                    
        # Get Angle data for the first hour after reset
        where_sql = "WHERE Recipe_ID = {} AND Timestamp > (Select MAX(Data.Timestamp) FROM Data WHERE Data.ResetFlag = true AND Recipe_id = {}) AND Timestamp < DATE_ADD((SELECT MAX(Data.Timestamp) FROM Data WHERE Recipe_ID = {} AND Data.ResetFlag = true), INTERVAL 1 HOUR)".format(ArchiveID, ArchiveID, ArchiveID)   
        sql_select = "SELECT AVG(Data.Angle) as angle FROM Data {}".format(where_sql) 
        cur.execute(sql_select)
        columns = [column[0] for column in cur.description]
        result_angle = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        try:
            if len(result_angle) > 0:
                initial_angle=result_angle[0]['angle']
                initial_gravity = round((const0 * initial_angle**3 + const1 * initial_angle**2 + const2 * initial_angle + const3),2)
        except:
            initial_gravity=0.000000001

        # Get Angle data for the last hour before end date -> Final Gravity caculation
        where_sql="WHERE Recipe_id = {} and Timestamp < '{}' and Recipe_id = {} AND Timestamp > DATE_SUB('{}', INTERVAL 1 HOUR)".format(ArchiveID, End_date, ArchiveID, End_date)
        sql_select="SELECT AVG(Data.Angle) as angle FROM Data {}".format(where_sql)
        cur.execute(sql_select)
        columns = [column[0] for column in cur.description]
        result_angle = [dict(zip(columns, row)) for row in cur.fetchall()]
        try:
            if len(result_angle) > 0:
                final_angle=result_angle[0]['angle']
                final_gravity = round((const0 * final_angle**3 + const1 * final_angle**2 + const2 * final_angle + const3),2)
        except:
            final_gravity=0.000000001

        try:    
            attenuation=round((initial_gravity - final_gravity)*100/initial_gravity,1)
            real_gravity = 0.1808 * initial_gravity + 0.8192 * final_gravity
            alcohol_by_weight = ( 100 * (real_gravity - initial_gravity) / (1.0665 * initial_gravity - 206.65))
            alcohol_by_volume = round((alcohol_by_weight / 0.795),1)
        except:
            attenuation=0
            alcohol_by_volume=0

        archive_header=dict.fromkeys(['ArchiveID', 'Spindle_Name', 'SpindleID', 'Batch', 'Recipe', 'Start_date', 'End_date', 'Const0', 'Const1', 'Const2', 'Const3','Calibrated', 'Formula', 'Initial_Gravity', 'Final_Gravity', 'Attenuation', 'Alcohol_by_volume']) 
        archive_header['Spindle_Name']=Spindle_Name
        archive_header['SpindleID']=SpindleID
        archive_header['Batch']=Batch
        archive_header['Recipe']=Recipe
        try:
            archive_header['Start_date']=Start_date.strftime('%Y-%m-%d')
            archive_header['End_date']=End_date.strftime('%Y-%m-%d')
        except:
            archive_header['Start_date']="1970-01-01"
            archive_header['End_date']="1970-01-01"
        archive_header['RID_END']=RID_END
        archive_header['Const0']=const0
        archive_header['Const1']=const1
        archive_header['Const2']=const2
        archive_header['Const3']=const3
        archive_header['Calibrated']=calibrated
        archive_header['Formula']=forumla
        archive_header['Initial_Gravity']=initial_gravity
        archive_header['Final_Gravity']=final_gravity
        archive_header['Attenuation']=attenuation
        archive_header['Alcohol_by_volume']=alcohol_by_volume
        archive_header['ArchiveID']=ArchiveID
        
        return archive_header


    @request_mapping(path='/getarchivevalues', method="POST", auth_required=False)
    async def get_archive_values(self, request):
        """
        ---
        description: get archive values for specified archive id
        tags:
        - iSpindle
        parameters:
        - in: body
          name: body
          description: get archive values for specified archive id
          required: true
          
          schema:
            type: object
            
            properties:
              name:
                type: string
              sensor:
                type: "integer"
                format: "int64"
              heater:
                type: "integer"
                format: "int64"
              agitator:
                type: "integer"
                format: "int64"
              target_temp:
                type: "integer"
                format: "int64"
              type:
                type: string
            example: 
              name: "Kettle 1"
              type: "CustomKettleLogic"

              
        responses:
            "204":
                description: successful operation
        """        
        data = await request.json()

        result= await self.get_all_archive_values(data)

        #header_data = await self.get_archive_header_data(ArchiveID)
        #logger.error(header_data)
        #return  web.json_response(data=header_data)
        return  web.json_response(data=result)

    async def get_all_archive_values(self, data):
        ArchiveID = data.get('ArchiveID')
        Const0 = float(data.get('Const0'))
        Const1 = float(data.get('Const1'))
        Const2 = float(data.get('Const2'))
        Const3 = float(data.get('Const3'))
        Initial_Gravity = float(data.get('Initial_Gravity'))
        if Initial_Gravity == 0:
            Initial_Gravity = 0.000000001
        Start = data.get('Start_date')
        End = data.get('End_date')
        RID_END = data.get('RID_END')
        if RID_END == True:
            AND_SQL =  " AND Timestamp <= (Select max(Timestamp) FROM Data WHERE Recipe_ID='{}' AND Internal = 'RID_END')".format(ArchiveID)
        else:
            AND_SQL=""

        sql_select = (f"SELECT DATE_FORMAT(Timestamp, '%Y-%m-%d %H:%i:%s') as Timestamp, temperature, angle, \
                      ({Const0}*angle*angle*angle+ {Const1}*angle*angle +{Const2}*angle + {Const3}) as Servergravity, gravity, battery, rssi, \
                      (({Initial_Gravity} - ({Const0}*angle*angle*angle+ {Const1}*angle*angle +{Const2}*angle + {Const3}))* 100 / {Initial_Gravity}) as attenuation, \
                      ((100 * (0.1808 * {Initial_Gravity} + 0.8192 * ({Const0}*angle*angle*angle+ {Const1}*angle*angle +{Const2}*angle + {Const3})- {Initial_Gravity}) / (1.0665 * {Initial_Gravity} - 206.65)) / 0.795) as alcohol \
                        FROM Data WHERE Recipe_ID = '{ArchiveID}'{AND_SQL} ORDER BY Timestamp ASC")

        # Get all data for the selected recipe
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()

        cur.execute(sql_select)
        df = DataFrame(cur.fetchall())
        columns = [column[0] for column in cur.description]
        df.columns = columns
        df.set_index('Timestamp', inplace=True)
        data = {"time": df.index.tolist()}
        for col in df.columns:
            data[col] = df[col].tolist()
        return data
    
    @request_mapping(path='/removeridflag/{ArchiveID}/', method="POST", auth_required=False)
    async def removeridflag(self, request):
        """
        ---
        description: Remove end of archive flag for specified archive id
        tags:
        - iSpindle
        parameters:
        - name: "ArchiveID"
          in: "path"
          description: "ArchiveID"
          required: true
          type: "integer"
          format: "int64"
        responses:
            "200":
                description: successful operation
        """
        ArchiveID = request.match_info['ArchiveID']
        await self.removearchiveflag(ArchiveID)
        #logger.error(header_data)
        return  web.json_response(status=200)

    async def removearchiveflag(self, ArchiveID):
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        sql_update = "UPDATE Data SET Internal = NULL WHERE Recipe_ID = '{}' AND Internal = 'RID_END'".format(ArchiveID)
        cur.execute(sql_update)
        cnx.commit()

    @request_mapping(path='/addridflag/{ArchiveID}/{Timestamp}/', method="POST", auth_required=False)
    async def addridflag(self, request):
        """
        ---
        description: Remove end of archive flag for specified archive id
        tags:
        - iSpindle
        parameters:
        - name: "ArchiveID"
          in: "path"
          description: "ArchiveID"
          required: true
          type: "integer"
          format: "int64"
        - name: "Timestamp"
          in: "path"
          description: "Timestamp"
          required: true
          type: "Timestamp"
          format: "YYYY-MM-DD HH:MM:SS"
        responses:
            "200":
                description: successful operation
        """
        ArchiveID = request.match_info['ArchiveID']
        Timestamp = round(int(request.match_info['Timestamp'])/1000)
        await self.addarchiveflag(ArchiveID, Timestamp)
        #logger.error(header_data)
        return  web.json_response(status=200)

    async def addarchiveflag(self, ArchiveID, Timestamp):
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        sql_update = "UPDATE Data SET Internal = 'RID_END' WHERE Recipe_ID = '{}' AND UNIX_TIMESTAMP(Timestamp) = {}".format(ArchiveID, Timestamp)
        cur.execute(sql_update)
        cnx.commit()

    @request_mapping(path='/deletearchive/{ArchiveID}/', method="POST", auth_required=False)
    async def deletearchive(self, request):
        """
        ---
        description: Delete data from  database for specified archive id
        tags:
        - iSpindle
        parameters:
        - name: "ArchiveID"
          in: "path"
          description: "ArchiveID"
          required: true
          type: "integer"
          format: "int64"
        responses:
            "200":
                description: successful operation
        """
        ArchiveID = request.match_info['ArchiveID']
        await self.deletearchivefromdatabase(ArchiveID)
        #logger.error(header_data)
        return  web.json_response(status=200)

    async def deletearchivefromdatabase(self, ArchiveID):
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        sql_delete1 = "DELETE FROM Archive WHERE Recipe_ID = '{}'".format(ArchiveID)
        sql_delete2 = "DELETE FROM Data WHERE Recipe_ID = '{}'".format(ArchiveID)
        cur.execute(sql_delete1)
        cur.execute(sql_delete2)
        cnx.commit()

    @request_mapping(path='/getcalibration/', method="POST", auth_required=False)
    async def getcalibration(self, request):
        """
        ---
        description: Get calibration data for all spindles
        tags:
        - iSpindle
        responses:
            "200":
                description: successful operation
        """
        spindle_calibration = await self.get_calibration()
        return  web.json_response(data=spindle_calibration)
    
    async def get_calibration(self):
        result_spindles=[]
        spindles = []
        spindle_ids=[]
        spindle_calibration=[]
        calibrated=[]
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()

        #get all spindles from Data table
        spindlenames_sql = "SELECT DATE_FORMAT(max(Timestamp),'%Y-%m-%d') as 'LastSeen', Name FROM Data GROUP BY Name"
        cur.execute(spindlenames_sql)
        spindles = cur.fetchall()


        for spindle in spindles:
            spindle_ID_sql=f"SELECT DISTINCT ID FROM Data WHERE Name = '{spindle[1]}'AND (ID <>'' OR ID <>'0') ORDER BY Timestamp DESC LIMIT 1"
            cur.execute(spindle_ID_sql)
            spindle_id = cur.fetchall()
            if len(spindle_id) > 0:
                spindle_ids.append(int(spindle_id[0][0]))
            else:
                spindle_ids.append('0')

            calibration_sql=f"SELECT const0, const1, const2, const3 FROM Calibration WHERE ID = {int(spindle_id[0][0])}" 
            cur.execute(calibration_sql)
            spindle_cal = cur.fetchall()
            if spindle_cal:
                spindle_calibration.append(spindle_cal)
                calibrated.append(True)
            else:  
                spindle_calibration.append([(0,0,0,0)])
                calibrated.append(False)

        i=0
        for spindle in spindles:
            data= {"calibrated": calibrated[i],"const0": float(spindle_calibration[i][0][0]), "const1": float(spindle_calibration[i][0][1]), "const2": float(spindle_calibration[i][0][2]), "const3": float(spindle_calibration[i][0][3])}
            result_spindles.append({'value': i, 'ID': int(spindle_ids[i]) , 'label': spindle[1], 'data': data})
            i+=1
       
        return result_spindles

    @request_mapping(path='/savecalibration/{id}/', method="POST", auth_required=False)
    async def savecalibration(self, request):
        """
        ---
        description: Save Calibration for specified spindle id
        tags:
        - iSpindle
        parameters:
        - name: "id"
          in: "path"
          description: "Spindle ID"
          required: true
          type: "integer"
          format: "int64"
        - in: body
          name: body
          description: dict of const0, const1, const2, const3
          required: true
          schema:
            type: object

            properties:
              const0:
                type: "float"
                format: "float"
                required: true
              const1:
                type: "float"
                format: "float"
                required: true
              const2:
                type: "float"
                format: "float"
                required: true                            
              const3:
                type: "float"
                format: "float"
                required: true             
        example:
            const0: 0.0
            const1: 0.0
            const2: 0.0
            const3: 0.0

        responses:
            "200":
                description: successful operation
        """        
        data = await request.json()
        id = request.match_info['id']
        await self.save_calibration(id, data)

        return  web.json_response(status=200)

    async def save_calibration(self, id, data):
        cnx = mysql.connector.connect(
                user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        if data['calibrated'] == True:
            sql_update = "UPDATE Calibration SET const0 = {}, const1 = {}, const2 = {}, const3 = {} WHERE ID = '{}'".format(data['const0'], data['const1'], data['const2'], data['const3'], id)
            cur.execute(sql_update)
            cnx.commit()
        else:
            sql_insert = "INSERT INTO Calibration (ID, const0, const1, const2, const3) VALUES ('{}', '{}', '{}', '{}', '{}')".format(id, data['const0'], data['const1'], data['const2'], data['const3'])
            cur.execute(sql_insert)
            cnx.commit()

    @request_mapping(path='/getrecentdata/{days}/', method="POST", auth_required=False)
    async def getrecentdata(self, request):
        """
        ---
        description: get last data from Spindles that have send data in the last x days
        tags:
        - iSpindle
        parameters:
        - name: "days"
          in: "path"
          description: "Get last data from Spindle if Spindle has sent data within the last x days "
          required: true
          type: "integer"
          format: "int64"
        responses:
            "200":
                description: successful operation
        """
        days = request.match_info['days']
        try:
            spindle_data = await self.get_recent_data(days)
            return  web.json_response(data=spindle_data)

        except Exception as e:
            logger.error(e)
            return  web.json_response(status=500)
        #logger.error(header_data)
        
    async def get_recent_data(self,days):
        spindles = []
        calibrated=[]
        spindle_data=[]
        spindle_id=[]
        spindle_calibration=[]
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()

        #get all spindles from Data table
        spindlenames_sql = f"SELECT DISTINCT Name FROM Data WHERE Timestamp > date_sub(NOW(), INTERVAL {days} DAY) ORDER BY Name"
        cur.execute(spindlenames_sql)
        spindles = cur.fetchall()
        
        if spindles:
            for spindle in spindles:
                spindle_ID_sql=f"SELECT DISTINCT ID FROM Data WHERE Name = '{spindle[0]}'AND (ID <>'' OR ID <>'0') ORDER BY Timestamp DESC LIMIT 1"
                cur.execute(spindle_ID_sql)
                result = cur.fetchall()
                if result:
                    spindle_id=int(result[0][0])
                else:
                    spindle_id=0
                try:
                    calibration_sql=f"SELECT const0, const1, const2, const3 FROM Calibration WHERE ID = {result[0][0]}" 
                    cur.execute(calibration_sql)
                    columns = [column[0] for column in cur.description] 
                    result_archive = [dict(zip(columns, row)) for row in cur.fetchall()]
                
                    Const0=result_archive[0]['const0']
                    Const1=result_archive[0]['const1'] 
                    Const2=result_archive[0]['const2']
                    Const3=result_archive[0]['const3']
                    calibrated=True
                except:
                    Const0=0.0000000001
                    Const1=0.0000000001
                    Const2=0.0000000001
                    Const3=0.0000000001
                    calibrated=False

                where_sql=(f"WHERE Name = '{spindle[0]}' \
                            AND Timestamp > (Select MAX(Data.Timestamp) FROM Data  WHERE Data.ResetFlag = true AND Data.Name = '{spindle[0]}') \
                            AND Timestamp < DATE_ADD((SELECT MAX(Data.Timestamp)FROM Data WHERE Data.Name = '{spindle[0]}' \
                            AND Data.ResetFlag = true), INTERVAL 1 HOUR)")

                #// query to calculate average angle for this recipe_id and timeframe
                sql_select= f"SELECT AVG(Angle) as angle FROM Data {where_sql}"
                cur.execute(sql_select)
                result = cur.fetchall()
                try:
                    initial_angle=float(result[0][0])
                except:
                    initial_angle=0.0000000001
                initial_gravity = (Const0 * initial_angle**3 + Const1 * initial_angle**2 + Const2 * initial_angle + Const3)

                sql_select=(f"SELECT UNIX_TIMESTAMP(Timestamp) as unixtime, temperature, angle, recipe, battery, 'interval', rssi, gravity, recipe_id, \
                            ({Const0}*angle*angle*angle+ {Const1}*angle*angle +{Const2}*angle + {Const3}) as Servergravity \
                                FROM Data WHERE Name = '{spindle[0]}' ORDER BY Timestamp DESC LIMIT 1")
                cur.execute(sql_select)
                columns = [column[0] for column in cur.description]
                result = [dict(zip(columns, row)) for row in cur.fetchall()]
                if result:
                    try:
                        hours=12
                        lasttime=result[0]['unixtime']
                        old_gravity = await self.getgravityhoursago(spindle[0], Const0, Const1, Const2, Const3, lasttime,hours)
                        result[0]['Delta_Gravity']=(float(result[0]['Servergravity'])-old_gravity)
                    except:
                        result[0]['Delta_Gravity']=0
                    result[0]['InitialGravity']=initial_gravity
                    try:
                        attenuation=(initial_gravity - float(result[0]['Servergravity']))*100/initial_gravity
                        real_gravity = 0.1808 * initial_gravity + 0.8192 * float(result[0]['Servergravity'])
                        alcohol_by_weight = ( 100 * (real_gravity - initial_gravity) / (1.0665 * initial_gravity - 206.65))
                        alcohol_by_volume = (alcohol_by_weight / 0.795)
                    except:
                        attenuation=0
                        alcohol_by_volume=0

                    result[0]['unixtime']=datetime.datetime.fromtimestamp(result[0]['unixtime']).strftime('%Y-%m-%d %H:%M:%S')
                    result[0]['Attenuation']=attenuation
                    result[0]['ABV']=alcohol_by_volume
                    result[0]['Calibrated']=calibrated
                    result[0]['Const0']=Const0
                    result[0]['Const1']=Const1
                    result[0]['Const2']=Const2
                    result[0]['Const3']=Const3

                    recipe_id=result[0]['recipe_id']

                    sql_select=(f"SELECT batch FROM Archive WHERE Recipe_ID = {recipe_id}")

                    cur.execute(sql_select)
                    columns = [column[0] for column in cur.description]
                    result_batch = [dict(zip(columns, row)) for row in cur.fetchall()]
                    result[0]['BatchID']=result_batch[0]['batch']

                    currentspindle={'label': spindle[0], 'value': spindle_id, 'data': result[0] }
                    spindle_data.append(currentspindle)
                else:
                    currentspindle={'label': spindle[0], 'value': spindle_id, 'data': {} }
                    spindle_data.append(currentspindle)

        return spindle_data

    async def getgravityhoursago(self,spindle, Const0, Const1, Const2, Const3, last, hours=12):
        cnx = mysql.connector.connect(
            user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        
        sql_select=(f"SELECT UNIX_TIMESTAMP(Timestamp) as unixtime, temperature, angle, recipe, battery, 'interval', rssi, gravity \
                    FROM Data \
                    WHERE Name = '{spindle}' AND Timestamp > DATE_SUB(FROM_UNIXTIME({last}), INTERVAL {hours} HOUR) limit 1")
        cur.execute(sql_select)
        columns = [column[0] for column in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]       
        if result:
            angle=result[0]['angle']
            old_gravity=round((Const0 * angle**3 + Const1 * angle**2 + Const2 * angle + Const3),2)
            return old_gravity
        else:
            return 0

    @request_mapping(path='/resetspindlerecipe/{id}/', method="POST", auth_required=False)
    async def resetspindlerecipe(self, request):
        """
        ---
        description: Save Calibration for specified spindle id
        tags:
        - iSpindle
        parameters:
        - name: "id"
          in: "path"
          description: "Spindle ID"
          required: true
          type: "integer"
          format: "int64"
        - in: body
          name: body
          description: dict of Spindlename, Batchid, Recipeid
          required: true
          schema:
            type: object

            properties:
              Spindlename:
                type: "string"
                required: true
              Batchid:
                type: "string"
                required: true
              Recipeid:
                type: "string"
                required: true                            
        example:
            Spindlename: "iSpindle001"
            Batchid: "2501"
            RecipeID: "Kölsch"

        responses:
            "200":
                description: successful operation
        """        
        data = await request.json()
        id = request.match_info['id']
        await self.reset_spindle_recipe(id, data)

        return  web.json_response(status=200)

    async def reset_spindle_recipe(self, id, data):
        cnx = mysql.connector.connect(
                user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
        cur = cnx.cursor()
        spindlename=data['Spindlename']
        batchid=data['BatchID']
        recipename=data['RecipeName']
        timestamp = datetime.datetime.now()
        time= timestamp.strftime('%Y-%m-%d %H:%M:%S')
        const0 = float(data['const0'])
        const1 = float(data['const1'])
        const2 = float(data['const2'])
        const3 = float(data['const3'])
        calibrated=data['calibrated']


        sql_select=f"SELECT max(Recipe_ID) as recipeid FROM Archive where Name='{spindlename}'"
        cur.execute(sql_select)
        columns = [column[0] for column in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]
        recipeid=result[0]['recipeid']



        if recipeid:
            timestamp_2 = datetime.datetime.now()
            time= timestamp_2.strftime('%Y-%m-%d %H:%M:%S')
            if calibrated == True:
                update_archive_table = (f"UPDATE Archive Set End_date = '{time}', const0 = '{const0}',const1 = '{const1}', const2 = '{const2}', const3 = '{const3}' \
                                        WHERE Recipe_ID = '{recipeid}'")
        
            else:
                update_archive_table = (f"UPDATE Archive Set End_date = '{time}', const0 = NULL, const1 = NULL, const2 = NULL, const3 = NULL \
                                        WHERE Recipe_ID = '{recipeid}'")
            #logging.error(update_archive_table)
            cur.execute(update_archive_table)
            cnx.commit()


            #write to archive table     
        if calibrated == True:
            const0 = float(data['const0'])
            const1 = float(data['const1'])
            const2 = float(data['const2'])
            const3 = float(data['const3'])
 
            entry_recipe_table_sql = (f"INSERT INTO `Archive` \
                                (`Recipe_ID`, `Name`, `ID`, `Recipe`, `Batch`, `Start_date`, `End_date`, `const0`, `const1`, `const2`, `const3`) \
                                VALUES (NULL, '{spindlename}', '{id}', '{recipename}', '{batchid}', '{time}', NULL, '{const0}', '{const1}', '{const2}', '{const3}')")
        
        else:
            entry_recipe_table_sql = (f"INSERT INTO `Archive` \
                                    (`Recipe_ID`, `Name`, `ID`, `Recipe`, `Batch`, `Start_date`, `End_date`, `const0`,`const1`, `const2`, `const3`) \
                                    VALUES (NULL, '{spindlename}', '{id}', '{recipename}', '{batchid}', '{time}', NULL, NULL, NULL, NULL, NULL)")

        #logging.error(entry_recipe_table_sql)
        cur.execute(entry_recipe_table_sql)
        cnx.commit()

        #write to archive table  
        get_latest_archive_id_sql=f"SELECT max(Recipe_ID) FROM Archive where Name='{spindlename}'"
        cur.execute(get_latest_archive_id_sql)
        columns = [column[0] for column in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]

        new_id=[result[0]['max(Recipe_ID)']]

        sql_select=(f"INSERT INTO Data (Timestamp, Name, ID, Angle, Temperature, Battery, resetFlag, RSSI, Recipe, Recipe_ID) \
                    VALUES ('{time}','{spindlename}', {id}, 0, 0, 0, true, 0, '{recipename}','{new_id[0]}')")
        #logging.error(sql_select)
        cur.execute(sql_select)
        cnx.commit()
        pass 

    @request_mapping(path='/transfercalibration/{SpindleID}/{ArchiveID}/', method="POST", auth_required=False)
    async def transfercalibration(self, request):
        """
        ---
        description: Transfer current Calibration from SpindleID to ArchiveID
        tags:
        - iSpindle
        parameters:
        - name: "SpindleID"
          in: "path"
          description: "Spindle ID"
          required: true
          type: "integer"
          format: "int64"
        - name: "ArchiveID"
          in: "path"
          description: "Archive ID"
          required: true
          type: "integer"
          format: "int64"

        responses:
            "200":
                description: successful operation
        """
        SpindleID = request.match_info['SpindleID']
        ArchiveID = request.match_info['ArchiveID']
        status= await self.transfer_calibration(SpindleID, ArchiveID)
        return  web.json_response(status=status)
    
    async def transfer_calibration(self, SpindleID, ArchiveID):
        data=[]
        spindle_calibration = await self.get_calibration()
        for spindle in spindle_calibration:
            if spindle['ID'] == int(SpindleID):
                data=spindle['data']

        if data:
            const0=data['const0']
            const1=data['const1']
            const2=data['const2']
            const3=data['const3']
            calibrated=data['calibrated']
            if calibrated == True:
                cnx = mysql.connector.connect(
                    user=spindle_SQL_USER,  port=spindle_SQL_PORT, password=spindle_SQL_PASSWORD, host=spindle_SQL_HOST, database=spindle_SQL_DB)
                cur = cnx.cursor()                         
                update_archive_table = (f"UPDATE Archive Set const0 = '{const0}',const1 = '{const1}', const2 = '{const2}', const3 = '{const3}' \
                                        WHERE Recipe_ID = '{ArchiveID}'")
                cur.execute(update_archive_table) 
                cnx.commit()
                return 200
            else:
                return 500  

        else:
            return 500


def setup(cbpi):
    cbpi.plugin.register("iSpindle", iSpindle)
    cbpi.plugin.register("iSpindleEndpoint", iSpindleEndpoint)
    cbpi.plugin.register("iSpindleConfig", iSpindleConfig)
    pass
