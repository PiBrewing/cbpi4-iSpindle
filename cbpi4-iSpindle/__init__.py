# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
import asyncio
from cbpi.api import *
from aiohttp import web
from cbpi.api import *
import re
from cbpi.api.config import ConfigType
from cbpi.api.dataclasses import DataType
import mysql.connector
import datetime
from json import JSONEncoder
from pandas import DataFrame
from .spindle_controller import iSpindleController

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
        global brewfatheraddr, brewfatherport, brewfathersuffix, brewfathertoken, brewfather_enable
        global dailyalarm, statusupdate
        global spindle_SQL_CONFIG 
        
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

        brewfather_enable = self.cbpi.config.get("brewfather_enable", None)
        if brewfather_enable is None:
            logger.warning("INIT Brewfather enable")
            try:
                await self.cbpi.config.add("brewfather_enable", "No", type=ConfigType.SELECT, description="Enable Brewfather data transfer",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                brewfather_enable = self.cbpi.config.get("brewfather_enable", "No")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("brewfather_enable", brewfather_enable, type=ConfigType.SELECT, description="Enable Brewfather data transfer",
                                                                                                    source=self.name,
                                                                                                    options= [{"label": "No","value": "No"},
                                                                                                            {"label": "Yes", "value": "Yes"}])
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        brewfatheraddr = self.cbpi.config.get("brewfatheraddr", None)
        if brewfatheraddr is None:
            logger.warning("INIT Brewfather address")
            try:
                await self.cbpi.config.add("brewfatheraddr", "", type=ConfigType.STRING, description="Brewfather address",
                                                                                                    source=self.name)
                                                                                                            
                brewfatheraddr = self.cbpi.config.get("brewfatheraddr", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("brewfatheraddr", brewfatheraddr, type=ConfigType.STRING, description="Brewfather address",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        brewfatherport = self.cbpi.config.get("brewfatherport", None)
        if brewfatherport is None:
            logger.warning("INIT Brewfather port")
            try:
                await self.cbpi.config.add("brewfatherport", "", type=ConfigType.NUMBER, description="Brewfather port",
                                                                                                    source=self.name)
                                                                                                            
                brewfatherport = self.cbpi.config.get("brewfatherport", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("brewfatherport", brewfatherport, type=ConfigType.NUMBER, description="Brewfather port",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        brewfathersuffix = self.cbpi.config.get("brewfathersuffix", None)
        if brewfathersuffix is None:
            logger.warning("INIT Brewfather suffix")
            try:
                await self.cbpi.config.add("brewfathersuffix", "", type=ConfigType.STRING, description="Brewfather suffix",
                                                                                                    source=self.name)
                                                                                                            
                brewfathersuffix = self.cbpi.config.get("brewfathersuffix", "")
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("brewfathersuffix", brewfathersuffix, type=ConfigType.STRING, description="Brewfather suffix",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        brewfathertoken = self.cbpi.config.get("brewfathertoken", None)
        if brewfathertoken is None:
            logger.warning("INIT Brewfather token")
            try:
                await self.cbpi.config.add("brewfathertoken", "", type=ConfigType.STRING, description="Brewfather token",
                                                                                                    source=self.name)
                                                                                                            
                brewfathertoken = self.cbpi.config.get("brewfathertoken", "")
            except:
                logger.warning('Unable to update database')
            else:   
                if self.iSpindle_update == None or self.iSpindle_update != self.version:
                    try:
                        await self.cbpi.config.add("brewfathertoken", brewfathertoken, type=ConfigType.STRING, description="Brewfather token",
                                                                                                    source=self.name)
                                                                                                            
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

        dailyalarm = self.cbpi.config.get("dailyalarm", None)
        if dailyalarm is None:
            logger.warning("INIT Spindle daily alarm")
            try:
                await self.cbpi.config.add("dailyalarm", "0", type=ConfigType.SELECT, description="Time for daily Spindle alarm", 
                                                                                                        source=self.name,
                                                                                                      options=[{"label": "0", "value": 0},
                                                                                                        {"label": "1", "value": 1},
                                                                                                        {"label": "2", "value": 2},
                                                                                                        {"label": "3", "value": 3},
                                                                                                        {"label": "4", "value": 4},
                                                                                                        {"label": "5", "value": 5},
                                                                                                        {"label": "6", "value": 6},
                                                                                                        {"label": "7", "value": 7},
                                                                                                        {"label": "8", "value": 8},
                                                                                                        {"label": "9", "value": 9},
                                                                                                        {"label": "10", "value": 10},
                                                                                                        {"label": "11", "value": 11},
                                                                                                        {"label": "12", "value": 12},
                                                                                                        {"label": "13", "value": 13},
                                                                                                        {"label": "14", "value": 14},
                                                                                                        {"label": "15", "value": 15},
                                                                                                        {"label": "16", "value": 16},
                                                                                                        {"label": "17", "value": 17},
                                                                                                        {"label": "18", "value": 18},
                                                                                                        {"label": "19", "value": 19},
                                                                                                        {"label": "20", "value": 20},
                                                                                                        {"label": "21", "value": 21},
                                                                                                        {"label": "22", "value": 22},
                                                                                                        {"label": "23", "value": 23}])
                                                                                                    
            except:
                logger.warning('Unable to update config')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("dailyalarm", dailyalarm, type=ConfigType.SELECT, description="Time for daily Spindle alarm", 
                                                                                                        source=self.name,
                                                                                                      options=[{"label": "0", "value": 0},
                                                                                                        {"label": "1", "value": 1},
                                                                                                        {"label": "2", "value": 2},
                                                                                                        {"label": "3", "value": 3},
                                                                                                        {"label": "4", "value": 4},
                                                                                                        {"label": "5", "value": 5},
                                                                                                        {"label": "6", "value": 6},
                                                                                                        {"label": "7", "value": 7},
                                                                                                        {"label": "8", "value": 8},
                                                                                                        {"label": "9", "value": 9},
                                                                                                        {"label": "10", "value": 10},
                                                                                                        {"label": "11", "value": 11},
                                                                                                        {"label": "12", "value": 12},
                                                                                                        {"label": "13", "value": 13},
                                                                                                        {"label": "14", "value": 14},
                                                                                                        {"label": "15", "value": 15},
                                                                                                        {"label": "16", "value": 16},
                                                                                                        {"label": "17", "value": 17},
                                                                                                        {"label": "18", "value": 18},
                                                                                                        {"label": "19", "value": 19},
                                                                                                        {"label": "20", "value": 20},
                                                                                                        {"label": "21", "value": 21},
                                                                                                        {"label": "22", "value": 22},
                                                                                                        {"label": "23", "value": 23}])

                except:
                    logger.warning('Unable to update config')

        statusupdate = self.cbpi.config.get("statusupdate", None)
        if statusupdate is None:
            logger.warning("INIT Spindle status update")
            try:
                await self.cbpi.config.add("statusupdate", "No", type=ConfigType.SELECT, description="Send daily status update from active iSpindle", 
                                                                                                        source=self.name,
                                                                                                      options=[{"label": "No", "value": "No"},
                                                                                                        {"label": "Yes", "value": "Yes"}])                                                                                                    
            except:
                logger.warning('Unable to update config')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("statusupdate", statusupdate, type=ConfigType.SELECT, description="Send daily status update from active iSpindle", 
                                                                                                        source=self.name,
                                                                                                      options=[{"label": "No", "value": "No"},
                                                                                                        {"label": "Yes", "value": "Yes"}])                                                                                                    
                except:
                    logger.warning('Unable to update config')

        alarmlow = self.cbpi.config.get("alarmlow", None)
        if alarmlow is None:
            logger.warning("INIT Spindle low alarm")
            try:
                await self.cbpi.config.add("alarmlow", 0, type=ConfigType.NUMBER, description="Low alarm value for iSpindle",
                                                                                                    source=self.name)
                                                                                                            
                alarmlow = self.cbpi.config.get("alarmlow", 0)
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("alarmlow", alarmlow, type=ConfigType.NUMBER, description="Low alarm value for iSpindle",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        alarmsvg = self.cbpi.config.get("alarmsvg", None)
        if alarmsvg is None:
            logger.warning("INIT Spindle attenuation alarm")
            try:
                await self.cbpi.config.add("alarmsvg", 100, type=ConfigType.NUMBER, description="Attenuation alarm value for iSpindle",
                                                                                                    source=self.name)
                                                                                                            
                alarmsvg = self.cbpi.config.get("alarmsvg", 100)
            except:
                logger.warning('Unable to update database')
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add("alarmsvg", alarmsvg, type=ConfigType.NUMBER, description="Attenuation alarm value for iSpindle",
                                                                                                    source=self.name)
                                                                                                            
                except:
                    logger.warning('Unable to update database')

        if self.iSpindle_update == None or self.iSpindle_update != self.version:
            try:
                 await self.cbpi.config.add(self.name+"_update", self.version,type=ConfigType.STRING, description='iSpindle Version Update', source='hidden')
            except Exception as e:
                logger.warning('Unable to update database')
                logger.warning(e)
        
        spindle_SQL_CONFIG = {'spindle_SQL': spindle_SQL, 'spindle_SQL_HOST': spindle_SQL_HOST, 'spindle_SQL_DB': spindle_SQL_DB, 'spindle_SQL_TABLE': spindle_SQL_TABLE, 'spindle_SQL_USER': spindle_SQL_USER, 'spindle_SQL_PASSWORD': spindle_SQL_PASSWORD, 'spindle_SQL_PORT': spindle_SQL_PORT}
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
        self.controller = iSpindleController(cbpi)
        # register component for http, events
        # In addtion the sub folder static is exposed to access static content via http
        self.cbpi.register(self, "/api/hydrometer/v1/data")

    async def run(self):
        await self.controller.get_spindle_sensor() 

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
            await self.controller.send_data_to_sql(datatime, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token, spindle_SQL_CONFIG)
        
        if brewfather_enable == "Yes":
            await self.controller.send_brewfather_data(key, spindle_id, angle, temp, gravity, battery,  user_token)

        if statusupdate == "Yes":
            alarmtime=self.cbpi.config.get("dailyalarm", "6")
            timestatuslow = datetime.time(int(alarmtime)-1, 45)
            timestatushigh = datetime.time(int(alarmtime), 15)
            currentdate = datetime.datetime.now()
            currenttime = datetime.datetime.time(currentdate)
            if currenttime >= timestatuslow and currenttime < timestatushigh:
                notificationsent = await self.controller.check_mail_sent(spindle_SQL_CONFIG, 'SentStatus', '1')
                if not notificationsent:
                    await self.controller.send_status_update(spindle_SQL_CONFIG)
                    await self.controller.write_mail_sent(spindle_SQL_CONFIG, 'SentStatus', '1',"")
            else:
                await self.controller.delete_mail_sent(spindle_SQL_CONFIG, 'SentStatus', '1')

        await self.controller.send_alarm(spindle_SQL_CONFIG, key, spindle_id)

    @request_mapping(path='/gettemp/{SpindleID}', method="POST", auth_required=False)
    async def get_fermenter_temp(self, request):
        SpindleID = request.match_info['SpindleID']
        sensor_value = await self.controller.get_spindle_sensor(SpindleID)
        data = {'Temp': sensor_value}
        return  web.json_response(data=data)

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

        data= await self.controller.get_archive_list(spindle_SQL_CONFIG)
        return  web.json_response(data=data)

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

        data= await self.controller.get_diagram_list()
        return  web.json_response(data=data)

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
            header_data = await self.controller.get_archive_header_data(spindle_SQL_CONFIG, ArchiveID)
            #logger.error(header_data)
            return  web.json_response(data=header_data)
        except Exception as e:
            logger.error(e)
            return  web.json_response(status=500)

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

        result= await self.controller.get_all_archive_values(spindle_SQL_CONFIG, data)

        #header_data = await self.get_archive_header_data(ArchiveID)
        #logger.error(header_data)
        #return  web.json_response(data=header_data)
        return  web.json_response(data=result)

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
        await self.controller.removearchiveflag(spindle_SQL_CONFIG, ArchiveID)
        #logger.error(header_data)
        return  web.json_response(status=200)

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
        await self.controller.addarchiveflag(spindle_SQL_CONFIG, ArchiveID, Timestamp)
        #logger.error(header_data)
        return  web.json_response(status=200)

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
        await self.controller.deletearchivefromdatabase(spindle_SQL_CONFIG, ArchiveID)
        #logger.error(header_data)
        return  web.json_response(status=200)

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
        spindle_calibration = await self.controller.get_calibration(spindle_SQL_CONFIG)
        return  web.json_response(data=spindle_calibration)

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
        await self.controller.save_calibration(spindle_SQL_CONFIG, id, data)

        return  web.json_response(status=200)

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
            spindle_data = await self.controller.get_recent_data(spindle_SQL_CONFIG, days)
            return  web.json_response(data=spindle_data)

        except Exception as e:
            logger.error(e)
            return  web.json_response(status=500)
        #logger.error(header_data)
        
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
        await self.controller.reset_spindle_recipe(spindle_SQL_CONFIG, id, data)

        return  web.json_response(status=200)

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
        status= await self.controller.transfer_calibration(spindle_SQL_CONFIG, SpindleID, ArchiveID)
        return  web.json_response(status=status)


def setup(cbpi):
    cbpi.plugin.register("iSpindle", iSpindle)
    cbpi.plugin.register("iSpindleEndpoint", iSpindleEndpoint)
    cbpi.plugin.register("iSpindleConfig", iSpindleConfig)
    pass
