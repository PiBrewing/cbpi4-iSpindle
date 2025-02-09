# -*- coding: utf-8 -*-
import logging

from cbpi.api import *
from cbpi.api.config import ConfigType

logger = logging.getLogger(__name__)


class iSpindleConfigController:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        pass

    async def iSpindle_config(self):

        parametercheck = False
        spindledata = self.cbpi.config.get("spindledata", None)
        plugin = await self.cbpi.plugin.load_plugin_list("cbpi4-iSpindle")
        try:
            self.version = plugin[0].get("Version", "0.0.0")
            self.name = plugin[0].get("Name", "cbpi4-iSPindle")
        except:
            self.version = "0.0.0"
            self.name = "craftbeerpi"

        self.iSpindle_update = self.cbpi.config.get(self.name + "_update", None)

        if spindledata is None:
            logger.warning("INIT Spindledata extra page in UI")
            try:
                await self.cbpi.config.add(
                    "spindledata",
                    "No",
                    type=ConfigType.SELECT,
                    description="Enable extra page for spindledata in ui",
                    source=self.name,
                    options=[
                        {"label": "No", "value": "No"},
                        {"label": "Yes", "value": "Yes"},
                    ],
                )

                spindledata = self.cbpi.config.get("spindledata", "No")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindledata",
                        spindledata,
                        type=ConfigType.SELECT,
                        description="Enable extra page for spindledata in ui",
                        source=self.name,
                        options=[
                            {"label": "No", "value": "No"},
                            {"label": "Yes", "value": "Yes"},
                        ],
                    )

                except:
                    logger.warning("Unable to update database")

        brewfather_enable = self.cbpi.config.get("brewfather_enable", None)
        if brewfather_enable is None:
            logger.warning("INIT Brewfather enable")
            try:
                await self.cbpi.config.add(
                    "brewfather_enable",
                    "No",
                    type=ConfigType.SELECT,
                    description="Enable Brewfather data transfer",
                    source=self.name,
                    options=[
                        {"label": "No", "value": "No"},
                        {"label": "Yes", "value": "Yes"},
                    ],
                )

                brewfather_enable = self.cbpi.config.get("brewfather_enable", "No")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "brewfather_enable",
                        brewfather_enable,
                        type=ConfigType.SELECT,
                        description="Enable Brewfather data transfer",
                        source=self.name,
                        options=[
                            {"label": "No", "value": "No"},
                            {"label": "Yes", "value": "Yes"},
                        ],
                    )

                except:
                    logger.warning("Unable to update database")

        brewfatheraddr = self.cbpi.config.get("brewfatheraddr", None)
        if brewfatheraddr is None:
            logger.warning("INIT Brewfather address")
            try:
                await self.cbpi.config.add(
                    "brewfatheraddr",
                    "",
                    type=ConfigType.STRING,
                    description="Brewfather address",
                    source=self.name,
                )

                brewfatheraddr = self.cbpi.config.get("brewfatheraddr", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "brewfatheraddr",
                        brewfatheraddr,
                        type=ConfigType.STRING,
                        description="Brewfather address",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        brewfatherport = self.cbpi.config.get("brewfatherport", None)
        if brewfatherport is None:
            logger.warning("INIT Brewfather port")
            try:
                await self.cbpi.config.add(
                    "brewfatherport",
                    "",
                    type=ConfigType.NUMBER,
                    description="Brewfather port",
                    source=self.name,
                )

                brewfatherport = self.cbpi.config.get("brewfatherport", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "brewfatherport",
                        brewfatherport,
                        type=ConfigType.NUMBER,
                        description="Brewfather port",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        brewfathersuffix = self.cbpi.config.get("brewfathersuffix", None)
        if brewfathersuffix is None:
            logger.warning("INIT Brewfather suffix")
            try:
                await self.cbpi.config.add(
                    "brewfathersuffix",
                    "",
                    type=ConfigType.STRING,
                    description="Brewfather suffix",
                    source=self.name,
                )

                brewfathersuffix = self.cbpi.config.get("brewfathersuffix", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "brewfathersuffix",
                        brewfathersuffix,
                        type=ConfigType.STRING,
                        description="Brewfather suffix",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        brewfathertoken = self.cbpi.config.get("brewfathertoken", None)
        if brewfathertoken is None:
            logger.warning("INIT Brewfather token")
            try:
                await self.cbpi.config.add(
                    "brewfathertoken",
                    "",
                    type=ConfigType.STRING,
                    description="Brewfather token",
                    source=self.name,
                )

                brewfathertoken = self.cbpi.config.get("brewfathertoken", "")
            except:
                logger.warning("Unable to update database")
            else:
                if self.iSpindle_update == None or self.iSpindle_update != self.version:
                    try:
                        await self.cbpi.config.add(
                            "brewfathertoken",
                            brewfathertoken,
                            type=ConfigType.STRING,
                            description="Brewfather token",
                            source=self.name,
                        )

                    except:
                        logger.warning("Unable to update database")

        spindle_SQL = self.cbpi.config.get(
            "spindle_SQL", None
        )  # 1 to enable output to MySQL database
        if spindle_SQL is None:
            logger.warning("INIT Spindle database select for transfer")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL",
                    "No",
                    type=ConfigType.SELECT,
                    description="Enable transfer of Spindle data to SQL database",
                    source=self.name,
                    options=[
                        {"label": "No", "value": "No"},
                        {"label": "Yes", "value": "Yes"},
                    ],
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL", "No")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL",
                        spindle_SQL,
                        type=ConfigType.SELECT,
                        description="Enable transfer of Spindle data to SQL database",
                        source=self.name,
                        options=[
                            {"label": "No", "value": "No"},
                            {"label": "Yes", "value": "Yes"},
                        ],
                    )

                except:
                    logger.warning("Unable to update database")

        spindle_SQL_HOST = self.cbpi.config.get(
            "spindle_SQL_HOST", None
        )  # Database host name (default: localhost - 127.0.0.1 loopback interface)
        if spindle_SQL_HOST is None:
            logger.warning("INIT Spindle database host name")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL_HOST",
                    "",
                    type=ConfigType.STRING,
                    description="SQL database host. e.g: localhost or IP address",
                    source=self.name,
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL_HOST", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL_HOST",
                        spindle_SQL_HOST,
                        type=ConfigType.STRING,
                        description="SQL database host. e.g: localhost or IP address",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        spindle_SQL_DB = self.cbpi.config.get("spindle_SQL_DB", None)  # Database name
        if spindle_SQL_DB is None:
            logger.warning("INIT Spindle Database Name")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL_DB",
                    "",
                    type=ConfigType.STRING,
                    description="SQL database name",
                    source=self.name,
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL_DB", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL_DB",
                        spindle_SQL_DB,
                        type=ConfigType.STRING,
                        description="SQL database name",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        spindle_SQL_USER = self.cbpi.config.get("spindle_SQL_USER", None)  # DB user
        if spindle_SQL_USER is None:
            logger.warning("INIT Spindle Database user name")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL_USER",
                    "",
                    type=ConfigType.STRING,
                    description="SQL database user name",
                    source=self.name,
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL_USER", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL_USER",
                        spindle_SQL_USER,
                        type=ConfigType.STRING,
                        description="SQL database user name",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        spindle_SQL_PASSWORD = self.cbpi.config.get(
            "spindle_SQL_PASSWORD", None
        )  # DB user's password (change this)
        if spindle_SQL_PASSWORD is None:
            logger.warning("INIT Spindle Database password")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL_PASSWORD",
                    "",
                    type=ConfigType.STRING,
                    description="SQL database password",
                    source=self.name,
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL_PASSWORD", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL_PASSWORD",
                        spindle_SQL_PASSWORD,
                        type=ConfigType.STRING,
                        description="SQL database password",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        spindle_SQL_PORT = self.cbpi.config.get("spindle_SQL_PORT", None)
        if spindle_SQL_PORT is None:
            logger.warning("INIT Spindle Database port number")
            try:
                await self.cbpi.config.add(
                    "spindle_SQL_PORT",
                    "",
                    type=ConfigType.NUMBER,
                    description="SQL database port number",
                    source=self.name,
                )

                spindle_SQL = self.cbpi.config.get("spindle_SQL_PORT", "")
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "spindle_SQL_PORT",
                        spindle_SQL_PORT,
                        type=ConfigType.NUMBER,
                        description="SQL database port number",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        dailyalarm = self.cbpi.config.get("dailyalarm", None)
        if dailyalarm is None:
            logger.warning("INIT Spindle daily alarm")
            try:
                await self.cbpi.config.add(
                    "dailyalarm",
                    "0",
                    type=ConfigType.SELECT,
                    description="Time for daily Spindle alarm",
                    source=self.name,
                    options=[
                        {"label": "0", "value": 0},
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
                        {"label": "23", "value": 23},
                    ],
                )

            except:
                logger.warning("Unable to update config")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "dailyalarm",
                        dailyalarm,
                        type=ConfigType.SELECT,
                        description="Time for daily Spindle alarm",
                        source=self.name,
                        options=[
                            {"label": "0", "value": 0},
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
                            {"label": "23", "value": 23},
                        ],
                    )

                except:
                    logger.warning("Unable to update config")

        statusupdate = self.cbpi.config.get("statusupdate", None)
        if statusupdate is None:
            logger.warning("INIT Spindle status update")
            try:
                await self.cbpi.config.add(
                    "statusupdate",
                    "No",
                    type=ConfigType.SELECT,
                    description="Send daily status update from active iSpindle",
                    source=self.name,
                    options=[
                        {"label": "No", "value": "No"},
                        {"label": "Yes", "value": "Yes"},
                    ],
                )
            except:
                logger.warning("Unable to update config")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "statusupdate",
                        statusupdate,
                        type=ConfigType.SELECT,
                        description="Send daily status update from active iSpindle",
                        source=self.name,
                        options=[
                            {"label": "No", "value": "No"},
                            {"label": "Yes", "value": "Yes"},
                        ],
                    )
                except:
                    logger.warning("Unable to update config")

        alarmlow = self.cbpi.config.get("alarmlow", None)
        if alarmlow is None:
            logger.warning("INIT Spindle low alarm")
            try:
                await self.cbpi.config.add(
                    "alarmlow",
                    0,
                    type=ConfigType.NUMBER,
                    description="Low alarm value for iSpindle",
                    source=self.name,
                )

                alarmlow = self.cbpi.config.get("alarmlow", 0)
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "alarmlow",
                        alarmlow,
                        type=ConfigType.NUMBER,
                        description="Low alarm value for iSpindle",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        alarmsvg = self.cbpi.config.get("alarmsvg", None)
        if alarmsvg is None:
            logger.warning("INIT Spindle attenuation alarm")
            try:
                await self.cbpi.config.add(
                    "alarmsvg",
                    100,
                    type=ConfigType.NUMBER,
                    description="Attenuation alarm value for iSpindle",
                    source=self.name,
                )

                alarmsvg = self.cbpi.config.get("alarmsvg", 100)
            except:
                logger.warning("Unable to update database")
        else:
            if self.iSpindle_update == None or self.iSpindle_update != self.version:
                try:
                    await self.cbpi.config.add(
                        "alarmsvg",
                        alarmsvg,
                        type=ConfigType.NUMBER,
                        description="Attenuation alarm value for iSpindle",
                        source=self.name,
                    )

                except:
                    logger.warning("Unable to update database")

        if self.iSpindle_update == None or self.iSpindle_update != self.version:
            try:
                await self.cbpi.config.add(
                    self.name + "_update",
                    self.version,
                    type=ConfigType.STRING,
                    description="iSpindle Version Update",
                    source="hidden",
                )
            except Exception as e:
                logger.warning("Unable to update database")
                logger.warning(e)

        spindle_SQL_CONFIG = {
            "spindle_SQL": spindle_SQL,
            "spindle_SQL_HOST": spindle_SQL_HOST,
            "spindle_SQL_DB": spindle_SQL_DB,
            "spindle_SQL_USER": spindle_SQL_USER,
            "spindle_SQL_PASSWORD": spindle_SQL_PASSWORD,
            "spindle_SQL_PORT": spindle_SQL_PORT,
        }
        parametercheck = True

        return spindledata, parametercheck, spindle_SQL_CONFIG
