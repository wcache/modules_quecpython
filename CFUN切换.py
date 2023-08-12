import _thread
from queue import Queue

import osTimer
import sys_bus
import ujson
import uos
import utime

import checkNet
import modem
import net
import sim

import request
from aLiYun import aLiYun

from machine import ExtInt
from machine import Pin
from machine import UART
from machine import I2C
from misc import Power
from misc import PowerKey
from misc import ADC
from misc import USB

import pm

from usr.guard import NetService 

from usr.sensor import Sensor
from usr.merge_audio import MergeAudioPaly
from usr.battery import Battery
from usr.history import History
from usr.logging import getLogger
from usr.remote import RemotePublish, RemoteSubscribe
from usr.aliyunIot import AliYunIot
from usr.location import Location, GPSMatch, GPSParse
import ql_fs as dataStorage
from usr.QuecCloudOTA import QuecCloudOTA

log = getLogger(__name__)

sys_log =getLogger("sys_log")

DEVICE_FIRMWARE_NAME = uos.uname()[0].split("=")[1]
DEVICE_FIRMWARE_VERSION = modem.getDevFwVersion()

PROJECT_NAME = "StudentCard" 
PROJECT_VERSION  = "2.1"
UPDATA_DATE  = "2023-0311-13:00"

TEMP_DATA = "0505"

class NetStatus(object):
    CONNECT = 1     
    DISCONNECT = 0  

class ErrCode(object):
    OK = 0
    ECONF = -1000                        
    ENOSIM = -1001                      
    EAIR = -1002                        
    ESYSTEM = -1006                     
    EEND = -2000                        

EXCEPTION_TOPIC = "exception_topic"
class ExceptionServices(Exception):
    SYSTEM_RESET_DELAY_TIME = 10 * 60 * 1000
    CFUN_SWITCH_TIME = 2 * 60 * 1000 
    error_map = {     
        ErrCode.OK: 'No ERROR',
        ErrCode.ECONF: 'read system config ERROR',
        ErrCode.ENOSIM: 'sim card is not find',
        ErrCode.EAIR: 'air error',
        ErrCode.ESYSTEM : 'device queue process error',
        ErrCode.EEND: 'publish msg to aliyun failed',
    }

    def __init__(self):
        self.__system_error_count = 0   

        self.error_state = ErrCode.OK  
        self.__cfun_switch_timer = osTimer()

        sys_bus.subscribe("cfun_switch_timer", self.__cfun_switch_timer_process)
        sys_bus.subscribe(EXCEPTION_TOPIC, self.__exception_handler)
    
    def __cfun_switch_timer_cb(self, *argv):
        sys_log.error("cfun_switch_timer,argv:{}".format(*argv))
        sys_bus.publish("cfun_switch_timer", TEMP_DATA)

    def __cfun_switch_timer_process(self, topic, message):
        sys_log.error("__cfun_switch_timer_process,message:{}".format(message))
        net.setModemFun(0, 0)
        utime.sleep(5)
        net.setModemFun(1, 0)

    def __exception_handler(self, topic, msg):
        error_code = msg.get("error_code")
        msg = msg.get("msg")

        self.error_state = error_code   
        if ErrCode.OK == error_code :
            sys_log.error("{}".format(self.error_map[ErrCode.OK]))  
            net_state = net.getState()
            if net_state != -1:
                if net_state[1][0] == 1 or net_state[1][0] == 5: 
                    self.__cfun_switch_timer.stop() 
                    sys_log.error("netwerk recovery sucess")

        elif ErrCode.ECONF == error_code :
            sys_log.error("{}".format(self.error_map[ErrCode.ECONF]))
        elif ErrCode.ENOSIM == error_code :           
            sys_log.error("{}".format(self.error_map[ErrCode.ENOSIM]))
            self.__cfun_switch_timer.start(self.CFUN_SWITCH_TIME, 1, self.__cfun_switch_timer_cb)
        elif ErrCode.EAIR == error_code:
            sys_log.error("{}, try switch cfun to recover".format(self.error_map[ErrCode.EAIR]))
            self.__cfun_switch_timer.start(self.CFUN_SWITCH_TIME, 1, self.__cfun_switch_timer_cb)
        elif ErrCode.ESYSTEM == error_code:
            self.__system_error_count += 1 
            if self.__system_error_count > 10 :
                Power.powerRestart()
            sys_log.error("{}".format(self.error_map[ErrCode.ESYSTEM]))
        else:
            sys_log.error("unkonow error, error code:{}".format(error_code))

    def get_sevice_error_state(self):
        return self.error_state


def net_state_check(self):
    checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)
    stagecode, subcode = checknet.wait_network_connected(30)
    if stagecode == 1:
        message = dict(error_code=ErrCode.ENOSIM , msg=None)
        sys_bus.publish(EXCEPTION_TOPIC , message)
        return False
    elif stagecode == 2:
        message = dict(error_code=ErrCode.EAIR , msg=None)
        sys_bus.publish(EXCEPTION_TOPIC , message)
        return False
    elif stagecode == 3:
        if subcode == 1:
            return True 
        else:
            message = dict(error_code=ErrCode.EAIR , msg=None)
            sys_bus.publish(EXCEPTION_TOPIC , message)
            return False
