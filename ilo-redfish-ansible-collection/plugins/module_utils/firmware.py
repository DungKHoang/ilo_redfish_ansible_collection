 # Copyright 2019 Hewlett Packard Enterprise Development LP
 #
 # Licensed under the Apache License, Version 2.0 (the "License"); you may
 # not use this file except in compliance with the License. You may obtain
 # a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 # WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 # License for the specific language governing permissions and limitations
 # under the License.

# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: firmware
short_description: Common routines and class for ilo_firmware and ilo_firmware_facts
description:
    - get_all                       : query iLO to get collection of system resources
    - get_manager_info              : ilo Information
    - get_firmware_info             : get firmware
 
    - reset_ilo                     : reset ilo



version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''





import collections
import sys
import json
import time
from datetime import datetime as dt

from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

# -------------------------------------------
#   Relate to Ansible
#Instantiating module class        
#from ansible.module_utils.basic import *
#from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.iloRedfish import RedFishModule


#-------------------------------------------------


class FIRMWARE:

    MSG_MAINTENANCE_EXISTED                     = 'iLO - Maintenance Window already exists'
    MSG_MAINTENANCE_ATTRIBUTE_ERROR             = 'iLO - Error in attribute specified for maintenance window. Value is {0}'    

    def __init__(self, connection):

        self.endpoint                                                   = '/redfish/v1/UpdateService' 
        self.maintenance                                                = '/redfish/v1/UpdateService/MaintenanceWindows'
        self.inventory                                                  = '/redfish/v1/UpdateService/FirmwareInventory'
        self.repository                                                 = '/redfish/v1/UpdateService/ComponentRepository/'
        self.installset                                                 = '/redfish/v1/UpdateService/InstallSets/'

        self.connection                                                 = connection
          

        self.maintenance_collection, self.maintenance_collection_uris   = self.get_sub_collection_by(self.maintenance)
        self.inventory_collection, self.inventory_collection_uris       = self.get_sub_collection_by(self.inventory)
        self.repository_collection, self.repository_collection_uris     = self.get_sub_collection_by(self.repository)
        self.install_set_collection, self.install_set_collection_uris   = self.get_sub_collection_by(self.installset)
         


    


    # ----------------- get iLO iformation

    def get_manager_info(self):
        if self.collection is None:
            self.collection,self.collection_uris = self.get_all()
    
        for _m in self.collection:
            _oem                        = _m['Oem']['Hpe']
            _ilo_info                   = dict(
                Firmware                = _m['FirmwareVersion'],
                Model                   = _m['Model'],
                License                 = _oem['License'],
                SelfTestResults         = _oem['iLOSelfTestResults'],
                Links                   = _oem['Links']
            )
        return _ilo_info


    # ----------------- get iLO firmware

    def get_firmware_info(self):
        #for _m in self.collection:
        _m                  = self.collection
        _model              = _m['Model']
        _fw                 = _m['Oem']['Hpe']['Firmware']['Current']
        _fw                 = _fw['VersionString']
        _fw_date            = _fw['Date']

        _fw_info            = dict(
            model           = _model,
            firmware        = _fw,
            date    = _fw_date
        )

        return _fw_info

    # ----------------- get iLO firmware inventory

    def get_firmware_inventory(self):
        if self.inventory_collection is None:
            self.inventory_collection, self.inventory_collection_uris = self.get_sub_collection_by(self.inventory)
        _inventory_list                     = []
        for _m in self.inventory_collection:
            _oem                            = _m['Oem']['Hpe']
            _d                              = dict(
                Location                    = _oem['DeviceContext'],
                FirmwareVersion             = _m['Version'],
                FirmwareName                = _m['Name']
            )
            _inventory_list.append(_d)

        return _inventory_list




    # ----------------- reset ilo
    def reset_ilo(self):
        # Reset ilo
        for _m in self.collection:
            __target        = _m['Actions']['#Manager.Reset']['target']
            _resp           = self.connection.post(__target, {}) 
        
        return _resp.obj

    # ----------------- get sub collection info    
    def get_sub_collection_by(self, uri):
        
        __sub_collection                = []
        __sub_collection_uris           = []

        if uri is not None:
            __resp                      = self.connection.get(uri)
            for __sm in __resp.obj['Members']:
                    __sm_uri            = __sm['@odata.id']
                    __sub_collection_uris.append(__sm_uri)

                    __response          = self.connection.get(__sm_uri)
                    __sub_collection.append(__response.obj)
        
        return __sub_collection, __sub_collection_uris
  
    

    # ----------------- Check maintenance window
    def check_maintenance_window(self, name,  start_time, end_time, id):
        _start_after            = None
        _expire                 = None
        _this                   = None
        if start_time is not None and end_time is not None:
            _start_after        = '{0}Z'.format(self.convert_time_to_iso_format(start_time))   # Add Z at thend for UTC format
            _expire             = '{0}Z'.format(self.convert_time_to_iso_format(end_time))
        
        if self.maintenance_collection is None:
            self.maintenance_collection, self.maintenance_collection_uris = self.get_sub_collection_by(self.maintenance)  
        for _m in self.maintenance_collection:
            if id == _m['Id'] or (name == _m['Name'] and _start_after == _m['StartAfter'] and _expire == _m['Expire']):
                _this        = _m
                break
        return _this
        

    # ----------------- Create maintenance window
    def create_maintenance_window(self, name, description, start_time, end_time):
        if start_time is not None and end_time is not None:
            _this_window        = self.check_maintenance_window(name= name, start_time= start_time , end_time = end_time, id = None) 
            if _this_window is None: # Does not exist
                _start_after        = self.convert_time_to_iso_format(start_time)
                _expire             = self.convert_time_to_iso_format(end_time)

                if name is None:
                    name            = ' Default maintenance window'
                    description     = ' Default maintenance window'

                _body               = dict(
                    Description     = description,
                    Name            = name,
                    StartAfter      = _start_after,
                    Expire          = _expire
                )
                _endpoint           = self.updateservice + '/MaintenanceWindows'
                _resp               = self.connection.post(_endpoint, _body)
                _resp_obj           = _resp.obj
                if 'error' in _resp_obj:
                    _status         = False
                    _info           = _resp_obj['error']['@Message.ExtendedInfo'][0]
                    _msg_id         = _info['MessageId']
                    __msg           = _msg_id.split('.')[-1]
                    _value          = _info['MessageArgs'][0]
                    if 'PropertyValueIncompatible' in __msg:
                        _msg        = self.MSG_MAINTENANCE_ATTRIBUTE_ERROR.format(_value)
                    if 'ResourceAlreadyExists' in __msg:
                        _msg        = self.MSG_MAINTENANCE_EXISTED.format(name)
                else:
                    _msg            = ''
                    _status         = True
            else: # Maintenance window already exists
                _resp_obj           = _this_window
                _msg                = ''
                _status             = True
        
        _maint      = dict(maintenance = _resp_obj)
        return _resp_obj, _msg, _status


    def convert_time_to_iso_format(self, date_time_str):
        if '/' in date_time_str:
            _format             = "%m/%d/%Y %I:%M%p"    # 07/21/2021 5:00pm
        else:
            _format             = "%b %d %Y %I:%M%p"    # July 21 2021 8:00AM

        _time_iso               = dt.strptime(date_time_str, _format ).isoformat()

        return _time_iso

