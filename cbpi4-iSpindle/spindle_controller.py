# -*- coding: utf-8 -*-
import logging
from cbpi.api import *
from cbpi.api import *
import json
from cbpi.api.dataclasses import NotificationAction, NotificationType
import mysql.connector
import datetime
from pandas import DataFrame
import urllib3

class iSpindleController:

    def __init__(self, cbpi):
        self.cbpi = cbpi
        pass

    async def send_alarm(self, spindle_SQL_CONFIG, key, spindle_id):
        alarmlow = float(self.cbpi.config.get("alarmlow", 0))
        alarmsvg = self.cbpi.config.get("alarmsvg", 100)
        result = await self.get_recent_data(spindle_SQL_CONFIG, 1)

        body = '<br/><b>Date:</b> {}' +\
                '<br/><b>ID:</b> {}' +\
                '<br/><b>Angle:</b> {}' + \
                '<br/><b>Initial Gravity Plato:</b> {}' + \
                '<br/><b>Current Gravity:</b> {}' + \
                '<br/><b>Delta Gravity (12 hrs):</b> {}' + \
                '<br/><b>Apparent Attenuation:</b> {}' + \
                '<br/><b>Alcohol by Volume %:</b> {}' + \
                '<br/><b>Temperature:</b> {}' +  \
                '<br/><b>Battery:</b> {}' + \
                '<br/><b>Recipe name:</b> {}' + \
                '<br/><br/>'

        for spindle in result:
            if spindle['label'] == key:
                data=spindle['data']
                #logger.error('Data: ' + str(data))
                if float(data['Servergravity']) < alarmlow:
                    alarmlowsent = await self.check_mail_sent(spindle_SQL_CONFIG, 'SentAlarmLow', spindle_id)
                    #logger.error('AlarmLow: ' + str(alarmlowsent))
                    if not alarmlowsent:
                        try:
                            content=body.format(data['unixtime'], spindle_id, round(float(data['angle']),1), round(float(data['InitialGravity']),1), round(float(data['Servergravity']),1), round(float(data['Delta_Gravity']),1), round(float(data['Attenuation']),1), round(float(data['ABV']),1), round(float(data['temperature']),1), round(float(data['battery']),2), data['recipe'])                            
                            self.cbpi.notify(f"Low Gravity Alarm from Spindle {str(spindle['label'])}", str(content), NotificationType.INFO, action=[NotificationAction("OK", self.Confirm)])
                        except Exception as e:
                            logging.error('Error sending alarm: ' + str(e))
                        await self.write_mail_sent(spindle_SQL_CONFIG, 'SentAlarmLow', spindle_id, spindle['label'])
                        pass
                if float(data['Attenuation']) > alarmsvg:
                    alarmsvgsent = await self.check_mail_sent(spindle_SQL_CONFIG, 'SentAlarmSVG', spindle_id)
                    if not alarmsvgsent:
                        try:
                            content=body.format(data['unixtime'], spindle_id, round(float(data['angle']),1), round(float(data['InitialGravity']),1), round(float(data['Servergravity']),1), round(float(data['Delta_Gravity']),1), round(float(data['Attenuation']),1), round(float(data['ABV']),1), round(float(data['temperature']),1), round(float(data['battery']),2), data['recipe'])                            
                            self.cbpi.notify(f"Attenuation Alarm from Spindle {str(spindle['label'])}", str(body), NotificationType.INFO, action=[NotificationAction("OK", self.Confirm)])
                        except Exception as e:
                            logging.error('Error sending alarm: ' + str(e))
                        await self.write_mail_sent(spindle_SQL_CONFIG, 'SentAlarmSVG', spindle_id, spindle['label'])
                        pass
                    
        pass
            
    async def Confirm(self, **kwargs):
        pass

    async def send_status_update(self, spindle_SQL_CONFIG):
        message=""
        body = '<br/><b>Name:</b> {}' +\
                '<br/><b>Date:</b> {}' +\
                '<br/><b>Angle:</b> {}' + \
                '<br/><b>Initial Gravity Plato:</b> {}' + \
                '<br/><b>Current Gravity:</b> {}' + \
                '<br/><b>Delta Gravity (12 hrs):</b> {}' + \
                '<br/><b>Apparent Attenuation:</b> {}' + \
                '<br/><b>Alcohol by Volume %:</b> {}' + \
                '<br/><b>Temperature:</b> {}' +  \
                '<br/><b>Battery:</b> {}' + \
                '<br/><b>Recipe name:</b> {}' + \
                '<br/><br/>'
        try:
            result = await self.get_recent_data(spindle_SQL_CONFIG, 3)
            #logging.error('Status Update: ' + str(result))
            try:
                for spindle in result:
                    data=spindle['data']
                    content=body.format(spindle['label'],data['unixtime'], round(float(data['angle']),1), round(float(data['InitialGravity']),1), round(float(data['Servergravity']),1), round(float(data['Delta_Gravity']),1), round(float(data['Attenuation']),1), round(float(data['ABV']),1), round(float(data['temperature']),1), round(float(data['battery']),2), data['recipe'])                            
                    message += content
                self.cbpi.notify(f"Status alarm for the following Spindles", str(message), NotificationType.INFO)
            except Exception as e:
                logging.error('Error sending alarm: ' + str(e))
        except Exception as e:
            logging.error('Error sending status update: ' + str(e))
        pass
        

    async def send_data_to_sql(self, datatime, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token, spindle_SQL_CONFIG):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()

        #get current recipe name
        recipe = 'n/a'
        try:
            sqlselect = (f"SELECT Data.Recipe FROM Data WHERE Data.Name = '{key}' AND Data.Timestamp >= (SELECT max( Data.Timestamp )FROM Data WHERE Data.Name = '{key}' AND Data.ResetFlag = true) LIMIT 1;")
            cur.execute(sqlselect)
            recipe_names = cur.fetchone()
            if recipe_names:
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

    # retrieve information from database, if mail has been sent for corresponding alarm
    async def check_mail_sent(self, spindle_SQL_CONFIG, alarm, iSpindel):
        try:
            cnx = mysql.connector.connect(
                user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
            cur = cnx.cursor()

            sqlselect = "Select value from Settings where Section ='MESSAGING' and Parameter = '%s' AND value = '%s' ;" %(alarm, iSpindel)
            #logger.error('SQL: ' + sqlselect)
            cur.execute(sqlselect)
            mail_sent = cur.fetchall()
            #logger.error('Mail Sent: ' + str(mail_sent))
            if len(mail_sent) > 0:
                for i in mail_sent:
                    spindelID_sent = i[0]
                return spindelID_sent
            else:
                return 
        except Exception as e:
            logging.error('Database Error: ' + str(e))

    # write information to database, that email has been send for corresponding alarm
    # iSpindel could be also '1' for setting SentStatus
    async def write_mail_sent(self, spindle_SQL_CONFIG, alarm,iSpindel,SpindelName=''):
        try:
            logging.error('Writing alarmflag %s for Spindel %s' %(alarm,iSpindel))
            cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
            cur = cnx.cursor()
            sqlselect = "INSERT INTO Settings (Section, Parameter, value, DeviceName) VALUES ('MESSAGING','%s','%s','%s');" %(alarm, iSpindel, SpindelName)
            cur.execute(sqlselect)
            cnx.commit()
            cur.close()
            cnx.close()
            return 1
        except Exception as e:
            logging.error('Database Error: ' + str(e))

    # remove email sent flag from database for corresponding alarm
    async def delete_mail_sent(self, spindle_SQL_CONFIG, alarm, iSpindel):
        try:
            cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
            cur = cnx.cursor()
            sqlselect = "DELETE FROM Settings where Section ='MESSAGING' and Parameter = '%s' AND value = '%s';" %(alarm, iSpindel)
            cur.execute(sqlselect)
            cnx.commit()
            cur.close()
            cnx.close()
            return 1
        except Exception as e:
            logging.error('Database Error: ' + str(e))

    async def send_brewfather_data(self, key, spindle_id, angle, temp, gravity, battery, user_token):
        brewfatheraddr = self.cbpi.config.get("brewfatheraddr", "")
        brewfatherport = self.cbpi.config.get("brewfatherport", 80)
        brewfathertoken = self.cbpi.config.get("brewfathertoken", "")
        brewfathersuffix = self.cbpi.config.get("brewfathersuffix", "")
        try:
            outdata = {
                    "ID": spindle_id,
                    "angle": angle,
                    "battery": battery,
                    "gravity": gravity,
                    "name": key + brewfathersuffix,
                    "temperature": temp,
                    "token": user_token
                    }
            url = 'http://' + brewfatheraddr + ':' + str(brewfatherport) + '/ispindel?id='+brewfathertoken
            out = json.dumps(outdata).encode('utf-8')
            headers = {'Content-Type': 'application/json', 'User-Agent': key}

            http=urllib3.PoolManager()
            request = http.request('POST', url, headers=headers, body=out)
            logging.info('Brewfather Data sent: ' + str(out))
            if request.status != 200:
                logging.error('Brewfather Response: ' + str(request.status))
            logging.info('Brewfather Response: ' + str(request.status))

        except Exception as e:
            logging.error('Brewfather Error: ' + str(e))
        
    async def send_data_to_grainconnect(self, grainconnect_serverurl, key, spindle_id, temp, temp_units, angle, gravity, battery, rssi, interval, user_token, gravity_units):
        grainconnect_url = "http://community.grainfather.com:80" + grainconnect_serverurl.strip()
        if gravity_units == "SG":
            GRAIN_SUFFIX=",SG"
        else:      
            GRAIN_SUFFIX = ""
        outdata = {
                        'name': key + GRAIN_SUFFIX,
                        'ID': spindle_id,
                        'angle': angle,
                        'temperature': temp,
                        'temp_units': temp_units,
                        'battery': battery,
                        'gravity': gravity,
                        'token': user_token,
                        'interval': interval,
                        'RSSI': rssi
                    }
        out=json.dumps(outdata).encode('utf-8')
        logging.info('serverurl: ' + grainconnect_url)
        logging.info('Data to GrainConnect: ' + str(outdata))
        try:
            http = urllib3.PoolManager()
            header={'User-Agent': 'iSpindel', 'Connection': 'close', 'Content-Type': 'application/json'}
            req = http.request('POST', grainconnect_url, body = out, headers = header)
            if req.status != 201:
                logging.error('GrainConnect Response: ' + str(req.status))
        except Exception as e:
            logging.error('GrainConnect Error: ' + str(e))
            pass


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

    

    async def get_archive_list(self, spindle_SQL_CONFIG):
        ORDER="DESC"
        archive_sql = "SELECT Recipe_ID as value, CONCAT(Batch, ' | ', Name, ' | ',DATE_FORMAT(Start_date, '%Y-%m-%d'),' | ', Recipe, ' (', Recipe_ID,')' ) as 'label' FROM Archive ORDER BY Recipe_ID {}".format(ORDER)
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        cur.execute(archive_sql)
        columns = [column[0] for column in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        return results

  
    async def get_diagram_list(self):
        results = [{'value': '0', 'label': 'Gravity and Temperature (RasPySpindle)'},
                   {'value': '1', 'label': 'Gravity and Temperature (iSpindle Polynom)'},
                   {'value': '2', 'label': 'Tilt and Temperature'},
                   {'value': '3', 'label': 'Attenuation'},
                   {'value': '4', 'label': 'Battery and Wifi Signal'}]

        return results

    
    async def get_archive_header_data(self, spindle_SQL_CONFIG, ArchiveID):
        result_angle=[] 

        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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
            const0=float(result_archive[0]['const0'])
            const1=float(result_archive[0]['const1'])
            const2=float(result_archive[0]['const2'])
            const3=float(result_archive[0]['const3'])
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



    async def get_all_archive_values(self, spindle_SQL_CONFIG, data):
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
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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
    
    async def removearchiveflag(self, spindle_SQL_CONFIG, ArchiveID):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        sql_update = "UPDATE Data SET Internal = NULL WHERE Recipe_ID = '{}' AND Internal = 'RID_END'".format(ArchiveID)
        cur.execute(sql_update)
        cnx.commit()

    async def addarchiveflag(self, spindle_SQL_CONFIG, ArchiveID, Timestamp):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        sql_update = "UPDATE Data SET Internal = 'RID_END' WHERE Recipe_ID = '{}' AND UNIX_TIMESTAMP(Timestamp) = {}".format(ArchiveID, Timestamp)
        cur.execute(sql_update)
        cnx.commit()


    async def deletearchivefromdatabase(self, spindle_SQL_CONFIG, ArchiveID):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        sql_delete1 = "DELETE FROM Archive WHERE Recipe_ID = '{}'".format(ArchiveID)
        sql_delete2 = "DELETE FROM Data WHERE Recipe_ID = '{}'".format(ArchiveID)
        cur.execute(sql_delete1)
        cur.execute(sql_delete2)
        cnx.commit()

    
    async def get_calibration(self, spindle_SQL_CONFIG):
        result_spindles=[]
        spindles = []
        spindle_ids=[]
        spindle_calibration=[]
        calibrated=[]
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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


    async def save_calibration(self, spindle_SQL_CONFIG, id, data):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        if data['calibrated'] == True:
            sql_update = "UPDATE Calibration SET const0 = {}, const1 = {}, const2 = {}, const3 = {} WHERE ID = '{}'".format(data['const0'], data['const1'], data['const2'], data['const3'], id)
            cur.execute(sql_update)
            cnx.commit()
        else:
            sql_insert = "INSERT INTO Calibration (ID, const0, const1, const2, const3) VALUES ('{}', '{}', '{}', '{}', '{}')".format(id, data['const0'], data['const1'], data['const2'], data['const3'])
            cur.execute(sql_insert)
            cnx.commit()

    async def get_recent_data(self, spindle_SQL_CONFIG, days):
        spindles = []
        calibrated=[]
        spindle_data=[]
        spindle_id=[]
        spindle_calibration=[]
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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

                sql_select=(f"SELECT UNIX_TIMESTAMP(Timestamp) as unixtime, temperature, angle, recipe, battery, '`Interval`', rssi, gravity, recipe_id, \
                            ({Const0}*angle*angle*angle+ {Const1}*angle*angle +{Const2}*angle + {Const3}) as Servergravity \
                                FROM Data WHERE Name = '{spindle[0]}' ORDER BY Timestamp DESC LIMIT 1")
                cur.execute(sql_select)
                columns = [column[0] for column in cur.description]
                result = [dict(zip(columns, row)) for row in cur.fetchall()]

                if result:
                    try:
                        hours=12
                        lasttime=result[0]['unixtime']
                        old_gravity = await self.getgravityhoursago(spindle_SQL_CONFIG, spindle[0], Const0, Const1, Const2, Const3, lasttime,hours)
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
                    if result_batch:
                        result[0]['BatchID']=result_batch[0]['batch']
                    else:
                        result[0]['BatchID']='n/a'
                    currentspindle={'label': spindle[0], 'value': spindle_id, 'data': result[0] }
                    spindle_data.append(currentspindle)
                else:
                    currentspindle={'label': spindle[0], 'value': spindle_id, 'data': {} }
                    spindle_data.append(currentspindle)

        return spindle_data

    async def getgravityhoursago(self, spindle_SQL_CONFIG, spindle, Const0, Const1, Const2, Const3, last, hours=12):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
        cur = cnx.cursor()
        
        sql_select=(f"SELECT UNIX_TIMESTAMP(Timestamp) as unixtime, temperature, angle, recipe, battery, '`Interval`', rssi, gravity \
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


    async def reset_spindle_recipe(self, spindle_SQL_CONFIG, id, data):
        cnx = mysql.connector.connect(
            user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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
        await self.delete_mail_sent(spindle_SQL_CONFIG, 'SentAlarmLow', id)
        await self.delete_mail_sent(spindle_SQL_CONFIG, 'SentAlarmSVG', id)
        pass 

    
    async def transfer_calibration(self, spindle_SQL_CONFIG, SpindleID, ArchiveID):
        data=[]
        spindle_calibration = await self.get_calibration(spindle_SQL_CONFIG)
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
                user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
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

    async def test_connection(self, spindle_SQL_CONFIG):
            try:
                cnx = mysql.connector.connect(
                user=spindle_SQL_CONFIG['spindle_SQL_USER'],  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=spindle_SQL_CONFIG['spindle_SQL_PASSWORD'], \
                    host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
                cur = cnx.cursor()
                sqlselect = "SELECT VERSION()"
                cur.execute(sqlselect)
                results = cur.fetchone()
                ver = results[0]
                logging.info("MySQL connection available. MySQL version: %s" % ver)
                sql_connection=True
                database_available=True
                if (ver is None):
                    logging.error("MySQL connection failed")
                    sql_connection=False
            except Exception as e:
                logging.error('Database Error: ' + str(e))
                self.cbpi.notify('Database Connection Error', str(e), NotificationType.ERROR, action=[NotificationAction("OK", self.Confirm)])
                sql_connection=False
            
            spindle_SQL_CONFIG['sql_connection'] = sql_connection
            #spindle_SQL_CONFIG['database_available'] = database_available
            return spindle_SQL_CONFIG

    async def create_database(self, spindle_SQL_CONFIG, admin='pi', admin_password='1tosca42'):
    
        # Create database
        create_db = f"CREATE DATABASE {spindle_SQL_CONFIG['spindle_SQL_DB']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"

        # create user    
        create_user       = f"CREATE USER {spindle_SQL_CONFIG['spindle_SQL_USER']} IDENTIFIED BY '{spindle_SQL_CONFIG['spindle_SQL_PASSWORD']}'"
        grant_user        = f"GRANT ALL PRIVILEGES ON {spindle_SQL_CONFIG['spindle_SQL_DB']} . * TO {spindle_SQL_CONFIG['spindle_SQL_USER']}"
        flush_privileges  = "FLUSH PRIVILEGES"

        try:
            cnx = mysql.connector.connect(
            user=admin,  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=admin_password, \
                host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database='', connection_timeout=1)
            cur = cnx.cursor()
        except Exception as e:
            logging.error('Database Creation Error: ' + str(e))
            self.cbpi.notify('Database Creation Error', str(e), NotificationType.ERROR, action=[NotificationAction("OK", self.Confirm)])
        if cur:
            try:
                cur.execute(create_db)
            except Exception as e:
                logging.error('Database Creation Error: ' + str(e))
                self.cbpi.notify('Database Creation Error', str(e), NotificationType.ERROR, action=[NotificationAction("OK", self.Confirm)])
            try:
                cur.execute(create_user)
                cur.execute(grant_user)
                cur.execute(flush_privileges)
            except Exception as e:
                logging.error('Database Creation Error: ' + str(e))
                self.cbpi.notify('Database Creation Error', str(e), NotificationType.ERROR, action=[NotificationAction("OK", self.Confirm)])
                cur.close()
                cnx.close()

            try:
                cnx = mysql.connector.connect(
                user=admin,  port=spindle_SQL_CONFIG['spindle_SQL_PORT'], password=admin_password, \
                    host=spindle_SQL_CONFIG['spindle_SQL_HOST'], database=spindle_SQL_CONFIG['spindle_SQL_DB'], connection_timeout=1)
                cur = cnx.cursor()

                # Create table
                create_data = "CREATE TABLE `Data` (\
                    `Timestamp` datetime NOT NULL,\
                    `Name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,\
                    `ID` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,\
                    `Angle` double NOT NULL,\
                    `Temperature` double NOT NULL,\
                    `Battery` double NOT NULL,\
                    `ResetFlag` tinyint(1) DEFAULT NULL,\
                    `Gravity` double NOT NULL DEFAULT 0,\
                    `UserToken` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                    `Interval` int(11) DEFAULT NULL,\
                    `RSSI` int(11) DEFAULT NULL,\
                    `Recipe` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                    `Recipe_ID` int(11) NOT NULL,\
                    `Internal` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                    `Comment` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                    `Temperature_Alt` DOUBLE NULL DEFAULT NULL,\
                        PRIMARY KEY (`Timestamp`,`Name`,`ID`)\
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=COMPACT COMMENT='iSpindle Data';"

                # create archive table
                create_archive = "CREATE TABLE `Archive` (\
                        `Recipe_ID` int(11) NOT NULL AUTO_INCREMENT,\
                        `Name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,\
                        `ID` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                        `Recipe` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                        `Batch` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,\
                        `Start_date` datetime NOT NULL,\
                        `End_date` datetime DEFAULT NULL,\
                        `const0` double DEFAULT NULL,\
                        `const1` double DEFAULT NULL,\
                        `const2` double DEFAULT NULL,\
                        `const3` double DEFAULT NULL,\
                        PRIMARY KEY (`Recipe_ID`)\
                        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"

                #create calibration table
                create_calibration = "CREATE TABLE `Calibration` (\
                            `ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,\
                            `const0` double NOT NULL DEFAULT 0,\
                            `const1` double NOT NULL DEFAULT 0,\
                            `const2` double NOT NULL DEFAULT 0,\
                            `const3` double NOT NULL DEFAULT 0,\
                            PRIMARY KEY (`ID`)\
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='iSpindle Calibration Data' ROW_FORMAT=COMPACT;"

                # create config table
                create_config = "CREATE TABLE `Config` (\
                        `ID` int(11) NOT NULL,\
                        `Interval` int(11) NOT NULL,\
                        `Token` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,\
                        `Polynomial` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,\
                        `Sent` tinyint(1) NOT NULL\
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='iSpindle Config Data' ROW_FORMAT=COMPACT;"


                # Create Settings table
                create_settings= "CREATE TABLE `Settings` (\
                                `Section` varchar(64) CHARACTER SET utf8 NOT NULL,\
                                `Parameter` varchar(64) CHARACTER SET utf8 NOT NULL,\
                                `value` varchar(80) CHARACTER SET utf8 NOT NULL,\
                                `DEFAULT_value` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,\
                                `Description_DE` varchar(128) CHARACTER SET utf8 DEFAULT NULL,\
                                `Description_EN` varchar(128) CHARACTER SET utf8 DEFAULT NULL,\
                                `Description_IT` varchar(128) CHARACTER SET utf8 DEFAULT NULL,\
                                `DeviceName` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL\
                                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=COMPACT;"
                alter_settings="ALTER TABLE `Settings`\
                                ADD PRIMARY KEY (`Section`,`Parameter`,`value`,`DeviceName`);"
                cur.execute(create_data)
                cur.execute(create_archive)
                cur.execute(create_calibration)
                cur.execute(create_config)
                cur.execute(create_settings)
                cur.execute(alter_settings)
                cur.close()
                self.cbpi.notify('Database Creation', 'Successfully created Databse', NotificationType.SUCCESS, action=[NotificationAction("OK", self.Confirm)])
                return True
            except Exception as e:
                logging.error('Database Table Creation Error: ' + str(e))
                self.cbpi.notify('Database Creation Error', str(e), NotificationType.ERROR, action=[NotificationAction("OK", self.Confirm)])
                return str(e)
