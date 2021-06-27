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
module: systems
short_description: Common routines and class for ilo_systems_facts and ilo_systems
description:
    - get_all                       : query iLO to get collection of system resources
    - get_system_info               : query iLO to get system summary info
    - get_processor_info            : Get details on CPU
    - get_memory_info               : Get details on memory
    - get_storage_info              : Get details on LocalStorage and SmartStorage

version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''





import collections
import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

# -------------------------------------------
#   Relate to Ansible
#Instantiating module class        
#from ansible.module_utils.basic import *
#from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.iloRedfish import RedFishModule


#-------------------------------------------------


class SYSTEMS:


    def __init__(self, connection):

        self.endpoint                   = '/redfish/v1/Systems' 
        self.connection                 = connection

        self.collection,self.collection_uris                            = self.get_all()                  # All members of self.endpoint
                

        self.processor_collection , self.processor_collection_uris      = self.get_sub_collection_per(type='Processors')      # All processor collection   
        self.memory_collection , self.memory_collection_uris            = self.get_sub_collection_per(type='Memory')                 # All memory collection

        self.array_controller , self.array_controller_uris              = self.get_smart_storage_controllers(type='ArrayControllers') 
        self.host_bus_adapter , self.host_bus_adapter_uris              = self.get_smart_storage_controllers(type='HostBusAdapters')  

        self.storage_collection , self.storage_collection_uris          = self.get_sub_collection_per(type='Storage')                  # All storage collection
        
        self.ethernet_collection        = None                  # All ethernet collection
        self.ethernet_collection_uris   = None
        self.network_collection         = None                  # All network interfaces
        self.network_collection_uris    = None

    
    # ----------------- get all members uri    
    def get_all(self):
        __collection                = []
        __collection_uris           = []

        __response                  = self.connection.get(self.endpoint)
        for __uri in __response.obj['Members']:
            __collection_uris.append(__uri['@odata.id'])
            __acc                   = self.connection.get(__uri['@odata.id'])
            __collection.append(__acc.obj) 

        return __collection, __collection_uris


    # ----------------- get system info    
    def get_system_info(self):
        if self.collection is None:
            self.collection,self.collection_uris = self.get_all()
    
        for _m in self.collection:
            _bios                   = _m['Oem']['Hpe']['Bios']['Current']
            _biosVersion            = _bios['VersionString']
            biosDate                = _bios['Date']

            _model                  = _m['Model']
            _serialNumber           = _m['SerialNumber']
            _sku                    = _m['SKU']
            _memory                 = _m['MemorySummary']['TotalSystemMemoryGiB']
            _cpu                    = _m['ProcessorSummary']
            _processor              = _cpu['Model']
            _processor_count        = _cpu['Count']

            # Get CPU core --> ensure that get_subcollection(type='Processors') is called first
            if self.processor_collection is None:
                self.processor_collection,self.processor_collection_uris    = self.get_sub_collection_per(type='Processors')
            _cores                  = self.processor_collection[0]['Oem']['Hpe']['CoresEnabled']


            # Get MACs --> ensure that get_subcollection(type='EthernetInterfaces') is called first
            if self.ethernet_collection is None:
                self.ethernet_collection,self.ethernet_collection_uris    = self.get_sub_collection_per(type='EthernetInterfaces')
            
            _macs                    = []
            for __eth in self.ethernet_collection:
                _macs.append(__eth['MACAddress'])
            
            # Get Network Interfaces
            #if self.network_collection is None:
            #    self.network_collection,self.network_collection_uris    = self.get_sub_collection(type='NetworkInterfaces/')
            #for __net in self.network_collection:


            _sys                    = dict( 
                model               = _model,
                serialNumber        = _serialNumber,
                sku                 = _sku,
                processor           = _processor,
                processor_count     = _processor_count,
                cores               = _cores,
                memory              = _memory,
                biosVersion         = _biosVersion,
                mac                 = _macs
            )
        return _sys                   

    # ----------------- get processor info    
    def get_processor_info(self):
    
        _processors                 = []
        for _m in self.processor_collection:
            _id                     = _m['Id']
            _health                 = _m['Status']['Health']
            _cores                  = _m['TotalCores']
            _threads                = _m['TotalThreads']
            _model                  = _m['Model']

            _oem                    = _m['Oem']['Hpe']
            _speedMhz               = _oem['RatedSpeedMHz']
            _cache                  = []
            for _c in _oem['Cache']:
                _cache.append(dict(name=_c['Name'],size=str(_c['MaximumSizeKB']) + ' KB'))

            _cpu                    = dict(
                id                  = _id,
                model               = _model,
                cores               = _cores,
                threads             = _threads,
                speedMhz            = _speedMhz,
                cache               = _cache
            )
            _processors.append(_cpu)

        return _processors

    # ----------------- get memory info    
    def get_memory_info(self):
    
        # Get Memory Summary
        for _m in self.collection:
            _mem_uri                = _m['Memory']['@odata.id']
            _mem                    = self.connection.get(_mem_uri)
            _oem                    = _mem.obj['Oem']['Hpe']

            # AMP info
            _amp                    = dict(
                ampmodestatus       = _oem['AmpModeStatus'],
                ampmodeactive       = _oem['AmpModeActive'],
                ampmodesupported    = _oem['AmpModeSupported']
            )

            # Memory Summary
            _mem_list               = []
            for _el in _oem['MemoryList']:
                _mem                    = dict(
                    location            = 'Processor {0}'.format(_el['BoardCpuNumber']),
                    slots               = _el['BoardNumberOfSockets'],
                    memory              = str(int(_el['BoardTotalMemorySize'] /1024)) + ' GB',      # in GB
                    frequency           = _el['BoardOperationalFrequency']
                )
                _mem_list.append(_mem)


        # Get physical memopry
        _physical_memory            = []
        for _ph in self.memory_collection:
            _status              = _ph['Oem']['Hpe']['DIMMStatus'] 
            if _status == 'GoodInUse':      
                _dimm                   = dict(
                    socket              = _ph['DeviceLocator'],
                    status              = _status,
                    size                = str(int(_ph['CapacityMiB']/ 1024)) + ' GB' ,
                    technology          = _ph['Oem']['Hpe']['BaseModuleType']  
                )
                _physical_memory.append(_dimm)

        _memory                     = dict(
            amp                     = _amp,
            memorylist              = _mem_list,
            phsyicalmemory          = _physical_memory 
        )

        return _memory

    # ----------------- get memory info    
    def get_storage_info(self):
        _local      = self.get_local_storage()
        _sma, _hba  = self.get_smart_storage()

        return _local, _sma, _hba

    # ----------------- get storage info    
    def get_local_storage(self):

        _controllers                = []
        for _m in self.storage_collection:
            _ss_name                = _m['Name']
            _health                 = _m['Status']['Health']
            _ct_list               = _m['StorageControllers']
            for _sc in _ct_list:
                _fw                 = _sc['FirmwareVersion']
                _sn                 = _sc['SerialNumber']
                _model              = _sc['Model']
                _location           = _sc['Location']['PartLocation']['ServiceLabel']

                # get physical drives
                _physical_drives    = []
                for _dr_list in _m['Drives']:
                    _uri            = _dr_list['@odata.id']                    
                    _resp           = self.connection.get(_uri)                   
                    _dr             = _resp.obj

                    _dr_type        = _dr['MediaType']
                    _dr_model       = _dr['Model']
                    _dr_sn          = _dr['SerialNumber']
                    
                    _lc_list         = _dr['Location']
                    for _lc in _lc_list:
                        _lc         = _lc['Info'].split(':')    # format:Box:Bay
                        _dr_location= 'Box {0}:Bay {1}'.format(_lc[0],_lc[1])

                    _dr_health      = _dr['Oem']['Hpe']['DriveStatus']['Health']
                    _dr_temp_health = _dr['Oem']['Hpe']['TemperatureStatus']['Health']
                    _dr_wear_health = _dr['Oem']['Hpe']['WearStatus']

                    if 'CapacityBytes' in _dr :
                        _dr_size    = str(round(_dr['CapacityBytes'] / pow(1000,4) , 1)) + ' GB'
                    else:
                        _dr_size    = 'Unknown'

                    _drive      = dict(
                        type            = _dr_type,
                        model           = _dr_model,
                        serialnumber    = _dr_sn,
                        location        = _dr_location,
                        size            = _dr_size,
                        health          = _dr_health,
                        temperature     = _dr_temp_health,
                        wear            = _dr_wear_health
                    )
                    _physical_drives.append(_drive)

                _ct                 = dict(
                    firmware        = _fw,
                    serialnumber    = _sn,
                    model           = _model,
                    location        = _location,
                    physicaldrives  = _physical_drives
                )
                _controllers.append(_ct)

        return _controllers

# ----------------- get controllers info    
    def get_smart_storage(self):

        _smart_array_collection,_smart_array_collection_uris    =  self.get_smart_storage_controllers('ArrayControllers') 
        _hba_collection,_hba_collection_uris                    = self.get_smart_storage_controllers('HostBusAdapters') 

        return _smart_array_collection, _hba_collection


    # ----------------- get controllers info    
    def get_smart_storage_controllers(self, type):
        # type = HostBusAdapters or ArrayControllers
        _sub_collection                 = []
        _sub_collection_uri             = []
        

        for _m in self.collection:
            _sst_uri                = _m['Oem']['Hpe']['Links']['SmartStorage']['@odata.id']
            _resp                   = self.connection.get(_sst_uri)
            _controller_uri         = _resp.obj['Links'][type]['@odata.id']

            _resp                   = self.connection.get(_controller_uri)
            _count                  = _resp.obj['Members@odata.count']
            if _count >= 1:
                _members            = _resp.obj['Members']
                for _s in _members:
                    _sub_collection_uri = _s['@odata.id']
                    _resp               = self.connection.get(_sub_collection_uri)
                    _sub_collection     = _resp.obj

        return _sub_collection, _sub_collection_uri


    # ----------------- get Smart Array config
    def get_smart_array(self):

        _m                      = self.array_controller
        _id                     = _m['Id']
        _model                  = _m['Model']
        _sn                     = _m['SerialNumber']
        _health                 = _m['Status']['Health']
        _location               = _m['Location']
        _pn                     = _m['ControllerPartNumber']
        _fw                     = _m['FirmwareVersion']['Current']['VersionString']
        _ld_uri                 = _m['Links']['LogicalDrives']['@odata.id']
        _pd_uri                 = _m['Links']['PhysicalDrives']['@odata.id']

        # get Physical drives
        _physical_drives        = []
        _pd_collection, _pd_collection_uris = self.get_sub_collection_by(_pd_uri)
        for _uri in _pd_collection_uris:
            _pd                 = self.get_physical_drive_by(_uri)
            _physical_drives.append(_pd)

        # get Logical drives
        _logical_drives        = []
        _ld_collection, _ld_collection_uris = self.get_sub_collection_by(_ld_uri)
        for _uri in _ld_collection_uris:
            _ld                 = self.get_logical_drive_by(_uri)
            _logical_drives.append(_ld)

        _contr                  = dict(
            id                  = _id,
            model               = _model,
            serialnumber        = _sn,
            partnumber          = _pn,
            location            = _location,
            status              = _health,
            firmware            = _fw,
            logicaldrives       = _logical_drives,
            physicaldrives      = _physical_drives 
        )



        return _contr

    # ----------------- get logical drive info    
    def get_logical_drive_by(self, uri):
        _ld                            = None
        if uri is not None:
            __resp                      = self.connection.get(uri)
            __obj                       = __resp.obj


            _physical_drives        = []
            _pd_collection, _pd_collection_uris = self.get_sub_collection_by(__obj['Links']['DataDrives']['@odata.id'])
            for _uri in _pd_collection_uris :
                _pd                     = self.get_physical_drive_by(_uri)
                _physical_drives.append(_pd)

            _ld                         = dict(
                id                      = __obj['LogicalDriveNumber'],
                raid                    = __obj['Raid'],
                health                  = __obj['Status']['Health'],
                size                    = str(int(__obj['CapacityMiB'] / 1024)) + ' GB',
                physicaldrives          = _physical_drives
            )         
        return _ld
    
    # ----------------- get physical drive info    
    def get_physical_drive_by(self, uri):
        _pd                             = None
        if uri is not None:
            __resp                      = self.connection.get(uri)
            __obj                       = __resp.obj
            _pd                         = dict(
                location                = __obj['Location'],
                health                  = __obj['Status']['Health'],
                serialnumber            = __obj['SerialNumber'],
                size                    = str(int(__obj['CapacityMiB'] / 1024)) + ' GB',
                firmware                = __obj['FirmwareVersion']['Current']['VersionString']
            )
        return _pd

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


    # ----------------- get sub collection info    
    def get_sub_collection_per(self, type):
        
        __sub_collection                = []
        __sub_collection_uris           = []

        if self.collection is None:
            self.collection,self.collection_uris = self.get_all()

        if type is not None:
            for _m in self.collection:
                __entry_point           = _m[type]['@odata.id']
                __response              = self.connection.get(__entry_point)
                for __sm in __response.obj['Members']:
                    __sm_uri            = __sm['@odata.id']
                    __sub_collection_uris.append(__sm_uri)

                    __response          = self.connection.get(__sm_uri)
                    __sub_collection.append(__response.obj)
        
        return __sub_collection, __sub_collection_uris


