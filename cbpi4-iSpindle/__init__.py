# -*- coding: utf-8 -*-
#import os
from aiohttp import web
import logging
import asyncio
from cbpi.api import *
from cbpi.api import *
import re
#from cbpi.api.config import ConfigType
from cbpi.api.dataclasses import DataType
import mysql.connector
import datetime
#from json import JSONEncoder
#from pandas import DataFrame
from .spindle_controller import iSpindleController
from .spindleconfig import iSpindleConfigController


logger = logging.getLogger(__name__)

cache = {}

class iSpindleConfig(CBPiExtension):

    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_config())

    async def init_config(self):
        global sql_connection, spindle_SQL_CONFIG, spindledata
        self.config_controller=iSpindleConfigController(self.cbpi)
        sql_connection=False
        parametercheck=False

        try:
            spindledata, parametercheck, spindle_SQL_CONFIG = await self.config_controller.iSpindle_config()
        except Exception as e:
            logger.error(e)

        logger.info("Spindledatabase: %s" % spindle_SQL_CONFIG)
        logger.info("Spindledata: %s" % spindledata)
        logger.info("Parametercheck: %s" % parametercheck)

        logging.error("Waiting for parameters")
        while parametercheck == False:
            await asyncio.sleep(1)
        logging.error("Parameters received")
        
        if spindle_SQL_CONFIG["spindle_SQL"] == "Yes":
            try:
                cnx = mysql.connector.connect(
                user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                    host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
                cur = cnx.cursor()
                sqlselect = "SELECT VERSION()"
                cur.execute(sqlselect)
                results = cur.fetchone()
                ver = results[0]
                logger.warning("MySQL connection available. MySQL version: %s" % ver)
                sql_connection=True
                if (ver is None):
                    sql_connection=False
                    logger.error("MySQL connection failed")
            except Exception as e:
                logger.error("MySQL connection failed")
                logger.error(e)
                sql_connection=False
                        


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
             Property.Text(label="GrainConnect_ServerURL", configurable=True, description="Enter the GrainConnect Server URL for this Spindle (only effective for Gravity/Angle sensors)"),
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
        self.lasttime = 0
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

        sensorlist = self.cbpi.sensor.get_state()
        grainconnect_serverurl= None
        value=0
        for sensor in sensorlist['data']:
            try:
                if (sensor['type'] == 'iSpindle' and sensor['props']['Type'] == 'Gravity/Angle'):
                    if sensor['props']['iSpindle'] == key:
                        grainconnect_serverurl = sensor['props']['GrainConnect_ServerURL']
                        polynomial = sensor['props']['Polynomial']
                        gravity_units = sensor['props']['Units']
                        value = await calcGravity(polynomial, angle, sensor['props']['Units'])
            except:
                pass

        if grainconnect_serverurl is not None and grainconnect_serverurl != "":
            logging.info('Time between last and current data: %s' % (round(datatime) - self.lasttime))
            if (datatime - self.lasttime) >= 900:
                await self.controller.send_data_to_grainconnect(grainconnect_serverurl, key, spindle_id, temp, temp_units, angle, value, battery, rssi, interval, user_token, gravity_units)
            else:   
                logging.error('Data not sent to GrainConnect. Time between last and current data to short (must be > 900 seconds): %s' % (round(datatime) - self.lasttime))
            self.lasttime = round(datatime)

        if self.cbpi.config.get("spindle_SQL", "No") == "Yes":
            await self.controller.send_data_to_sql(datatime, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token, spindle_SQL_CONFIG)
        
        if self.cbpi.config.get("brewfather_enable", "No") == "Yes":
            await self.controller.send_brewfather_data(key, spindle_id, angle, temp, gravity, battery,  user_token)

        if self.cbpi.config.get("statusupdate", "No") == "Yes":
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
        return web.json_response(status=204)

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
    
    @request_mapping(path='/testsqlconnection', method="POST", auth_required=False)
    async def test_sql_connection(self, request):
        """
        ---
        description: test if sql connection is available
        tags:
        - iSpindle
        responses:
            "200":
                description: successful operation
        """

        data= await self.controller.test_connection(spindle_SQL_CONFIG)
        return  web.json_response(data=data)

    @request_mapping(path='/createdatabase', method="POST", auth_required=False)
    async def createdatabase(self, request):
        """
        ---
        description: create database for iSpindle
        tags:
        - iSpindle
        responses:
            "200":
                description: successful operation
        """
        sql_admin= await request.json()
        try:
            admin=sql_admin['admin']
            password=sql_admin['adminpassword']
        except:
            admin=""
            password=""
        logger.error(sql_admin)
        data = await self.controller.create_database(spindle_SQL_CONFIG, admin, password)
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
