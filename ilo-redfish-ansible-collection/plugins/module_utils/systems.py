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
import time

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

    MSG_PHYSICAL_DRIVE_IN_USE           = 'Physical Drives already in logical drives'
    MSG_PHYSICAL_DRIVE_NOT_EXISTED      = 'Drive in the list {0} does not exist in the controller'    
    MSG_LOGICAL_DISK_NOT_SPECIFIED      = 'Raid not specified or list of drives empty'
    MSG_LOGICAL_DISK_NOT_FOUND          = 'Logical disk not found'

    def __init__(self, connection):

        self.endpoint                   = '/redfish/v1/Systems' 
        self.connection                 = connection

        self.collection,self.collection_uris                                        = self.get_all()                  # All members of self.endpoint
                

        self.processor_collection , self.processor_collection_uris                  = self.get_sub_collection_per(type='Processors')            # All processor collection   
        self.memory_collection , self.memory_collection_uris                        = self.get_sub_collection_per(type='Memory')                 # All memory collection

        # Local Storage
        self.storage_collection , self.storage_collection_uris                      = self.get_sub_collection_per(type='Storage')                  # All storage collection
 
        # Smart Storage
        self.array_controller , self.array_controller_uris                          = self.get_smart_storage_controllers(type='ArrayControllers') 
        self.host_bus_adapter , self.host_bus_adapter_uris                          = self.get_smart_storage_controllers(type='HostBusAdapters')  
        self.smstorage_config_collection , self.smstorage_config_collection_uris    = self.get_smart_storage_config_setting()
        
        # Network Adapters
        self.network_adapter_collection , self.network_adapter_collection_uris      = self.get_sub_collection_per(type='NetworkAdapters')                 # All network Adapters

        self.actions                                                                = [
                "On",
                "ForceOff",
                "GracefulShutdown",
                "ForceRestart",
                "Nmi",
                "PushPowerButton",
                "GracefulRestart"
                                                                                    ]
        # target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset/"


        self.ethernet_collection        = None                  # All ethernet collection
        self.ethernet_collection_uris   = None


    
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
                Model               = _model,
                SerialNumber        = _serialNumber,
                Sku                 = _sku,
                Processor           = _processor,
                ProcessorCount      = _processor_count,
                Cores               = _cores,
                Memory              = _memory,
                BiosVersion         = _biosVersion,
                Mac                 = _macs
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
                Id                  = _id,
                Model               = _model,
                Cores               = _cores,
                Threads             = _threads,
                SpeedMhz            = _speedMhz,
                Cache               = _cache
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
                AmpModeStatus       = _oem['AmpModeStatus'],
                AmpmodeActive       = _oem['AmpModeActive'],
                AmpmodeSupported    = _oem['AmpModeSupported']
            )

            # Memory Summary
            _mem_list               = []
            for _el in _oem['MemoryList']:
                _mem                    = dict(
                    Location            = 'Processor {0}'.format(_el['BoardCpuNumber']),
                    Slots               = _el['BoardNumberOfSockets'],
                    Memory              = str(int(_el['BoardTotalMemorySize'] /1024)) + ' GB',      # in GB
                    Frequency           = _el['BoardOperationalFrequency']
                )
                _mem_list.append(_mem)


        # Get physical memopry
        _physical_memory            = []
        for _ph in self.memory_collection:
            _status              = _ph['Oem']['Hpe']['DIMMStatus'] 
            if _status == 'GoodInUse':      
                _dimm                   = dict(
                    Socket              = _ph['DeviceLocator'],
                    Status              = _status,
                    Size                = str(int(_ph['CapacityMiB']/ 1024)) + ' GB' ,
                    Technology          = _ph['Oem']['Hpe']['BaseModuleType']  
                )
                _physical_memory.append(_dimm)

        _memory                     = dict(
            Amp                     = _amp,
            MemoryList              = _mem_list,
            PhysicalMemory          = _physical_memory 
        )

        return _memory

    # ----------------- get base network_adapters info    
    def get_network_adapter_info(self):
    
        _net_list                       = []
        # Get Base network Summary
        for _m in self.network_adapter_collection:
            _name                       = _m['Name']
            _fw                         = _m['Firmware']['Current']['VersionString']
            _state                      = _m['Status']['State']

            _port_list                  = []
            _i                          = 1
            for _p in _m['PhysicalPorts']:
                _p_dict                 = dict(
                    Id                  = 'Port {0}'.format(_i),
                    Mac                 = _p['MacAddress'],
                    IPv4                = _p['IPv4Addresses'],
                    IPv6                = _p['IPv6Addresses'],
                    LinkStatus          = _p['LinkStatus']
                )
                _port_list.append(_p_dict)
                _i                      = _i + 1

            _net                        = dict(
                Name                    = _name,
                Firmware                = _fw,
                State                   = _state,
                PhysicalPorts           = _port_list
            )

            _net_list.append(_net)


        return _net_list


    # ----------------- get all storage  info    
    def get_storage_info(self):
        _local      = self.get_local_storage()
        _sma, _hba  = self.get_smart_storage()

        return _local, _sma, _hba

    # ----------------- get local storage info    
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
                        Type            = _dr_type,
                        Model           = _dr_model,
                        SerialNumber    = _dr_sn,
                        Location        = _dr_location,
                        Size            = _dr_size,
                        Health          = _dr_health,
                        Temperature     = _dr_temp_health,
                        WearHealth      = _dr_wear_health
                    )
                    _physical_drives.append(_drive)

                _ct                 = dict(
                    Firmware        = _fw,
                    SerialNumber    = _sn,
                    Model           = _model,
                    Location        = _location,
                    PhysicalDrives  = _physical_drives
                )
                _controllers.append(_ct)

        return _controllers

    # ----------------- get controllers info    
    def get_smart_storage(self):

        _smart_array_collection                = self.get_smart_array('ArrayControllers') 
        _hba_collection                        = self.get_smart_array('HostBusAdapters') 

        return _smart_array_collection, _hba_collection

    # ----------------- get Smart Array config
    def get_smart_array(self,type):

        _contr                      = dict()

        if type == 'ArrayControllers':
                _m                      = self.array_controller
                _id                     = _m['Id']
                _model                  = _m['Model']
                _sn                     = _m['SerialNumber'].strip()
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
                    Id                  = _id,
                    Model               = _model,
                    SerialNumber        = _sn,
                    PartNumber          = _pn,
                    Location            = _location,
                    Status              = _health,
                    Firmware            = _fw,
                    LogicalDrives       = _logical_drives,
                    PhysicalDrives      = _physical_drives 
                )



        return _contr


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
                firmware                = __obj['FirmwareVersion']['Current']['VersionString'],
                diskdriveuse            = __obj['DiskDriveUse'],
                encrypteddrive          = __obj['EncryptedDrive']
            )
        return _pd

    # ----------------- get Smart Storage Config and settings info    
    def get_smart_storage_config_setting(self):
        #/redfish/v1/Systems/1/SmartStorageConfig

        __sub_collection                = []
        __sub_collection_uris           = []

        for _endpoint in self.collection_uris:
            _uri                        = _endpoint + '/SmartStorageConfig'
            _resp                       = self.connection.get(_uri)
            __sub_collection.append(_resp.obj)               
            __sub_collection_uris.append(_uri)

        return  __sub_collection, __sub_collection_uris 

    # ----------------- create a logical drive    
    def create_logical_drive(self, raid, name, drive_list=[]):

        _config                         = self.smstorage_config_collection 
        
        if drive_list is not None and raid is not None:
            _smart_array                = self.get_smart_array('ArrayControllers')
            _physical_drives_list       = _smart_array ['PhysicalDrives']
            _pd_list                    = []
            for _pd in _physical_drives_list :
                _pd_list.append(_pd['Location'])

            __existed                   = True
            for _drive in drive_list:
                __existed               = __existed and ( _drive in _pd_list)

            if __existed:
                for _config in self.smstorage_config_collection:
                    _ld_list                        = _config['LogicalDrives']
                    # Check if drive_list already in existing logical drives
                    _unconfigured               = True
                    for _ld in _ld_list:
                        if _ld['DataDrives'] == drive_list:
                            _unconfigured       = False
                            break

                    if _unconfigured:
                        # Build body for create request 
                        _new_ld                     = dict(
                                Raid                    = raid ,
                                DataDrives              = drive_list
                            )
                        if name is not None:
                            _new_ld['LogicalDriveName'] = name

                        _body                       = _config.copy()

                        _body['DataGuard']          = 'Disabled'            # Set to disabled to allow config change
                        _ld_list.append(_new_ld)                            # Add new logical drive to list
                            
                        _resp                       = self.logical_drive_action(_body)
                        _msg                        = ''
                        _status                     = True
                    else:
                        _resp                       = None
                        _msg                        = self.MSG_PHYSICAL_DRIVE_IN_USE
                        _status                     = False
            else:
                _resp                   = None
                _msg                    = self.MSG_PHYSICAL_DRIVE_NOT_EXISTED.format(drive_list) 
                _status                 = False 
        else:
            _resp                       = None
            _msg                        = self.MSG_LOGICAL_DISK_NOT_SPECIFIED
            _status                     = False

        return  _resp,  _status, _msg


    # ----------------- create a logical drive    
    def delete_logical_drive(self, name, drive_list=[]):

        _config                         = self.smstorage_config_collection 
        _found                          = False
        _vol_id                         = None

        if drive_list is not None or name is not None:
            for _config in self.smstorage_config_collection:
                _ld_list                = _config['LogicalDrives']
                for _ld in _ld_list:
                    if _ld['LogicalDriveName'] == name:
                        _found          = True
                        _vol_id         = _ld['VolumeUniqueIdentifier']
                        break
                    else:
                        if _ld['DataDrives'] == drive_list:
                            _found          = True
                            _vol_id         = _ld['VolumeUniqueIdentifier']  
                            break
                if _found:
                    _actions                = dict(
                            Actions         = [ dict(Action = 'LogicalDriveDelete')],
                            VolumeUniqueIdentifier  = _vol_id
                            )                        
                    
                    _body                   = dict( 
                        DataGuard           = 'Permissive',
                        LogicalDrives       =   [
                                                dict(
                                                        Actions                 = [ dict(Action = 'LogicalDriveDelete')],
                                                        VolumeUniqueIdentifier  = _vol_id                            
                                                    )
                                                ]
                        )
                    _resp                   = self.logical_drive_action(_body)
                    _msg                    = ''
                    _status                 = True 


                else:
                    _resp                   = None
                    _msg                    = self.MSG_LOGICAL_DISK_NOT_FOUND
                    _status                 = False
                    

        return  _resp, _status, _msg
        


    # ----------------- define system action   
    def logical_drive_action(self,  body):
        _config                     = self.smstorage_config_collection 
        
        for _config in self.smstorage_config_collection:
            _endpoint                   = _config['@Redfish.Settings']['SettingsObject']['@odata.id']
            _resp                       = self.connection.put(_endpoint, body)
            if 'error' in _resp.obj:
                for _info in _resp.obj['error']['@Message.ExtendedInfo']:
                    _msg                    = _info['MessageId'].split()[-1]
                if  'SystemResetRequired' in _msg:
                    _action             = dict(ResetType = 'ForceRestart')
                    for _m in self.collection_uris:
                        _action_endpoint    = _m + '/Actions/ComputerSystem.Reset/'
                        #_action_endpoint    = '/redfish/v1/Systems/1/Actions/ComputerSystem.Reset/'
                    _resp               = self.connection.post(_action_endpoint, _action)
                    
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
  
    
    # ----------------- get sub collection info    
    def get_sub_collection_per(self, type):
        
        __sub_collection                = []
        __sub_collection_uris           = []

        if self.collection is None:
            self.collection,self.collection_uris = self.get_all()

        if type is not None:
            for _m in self.collection:

                # Power on server if necessary
                _isOff                  = (_m['PowerState'] == 'Off')      
                if (type == 'Storage' or type == 'NetworkAdapters') and _isOff:
                    self.poweron_and_wait_post()            

                # Get collection here
                # Network Adapters use ['Oem']['Hpe']['Links']
                if type == 'NetworkAdapters':
                    __entry_point       = _m['Oem']['Hpe']['Links']['NetworkAdapters']['@odata.id']
                else:
                    __entry_point       = _m[type]['@odata.id']    

                __response              = self.connection.get(__entry_point)

                # Check if __response.obj is ready
                _msg                    = ''
                if 'error' in __response.obj:
                    for _info in __response.obj['error']['@Message.ExtendedInfo']:
                        _msg                    = _info['MessageId'].split()[-1]
                while  'ResourceNotReadyRetry' in _msg:
                    time.sleep(2)
                    # Re-query again
                    __response              = self.connection.get(__entry_point)
                    # Check if __response.obj is ready
                    if 'error' in __response.obj:
                        for _info in __response.obj['error']['@Message.ExtendedInfo']:
                            _msg                    = _info['MessageId'].split()[-1]
                
                for __sm in __response.obj['Members']:
                    __sm_uri            = __sm['@odata.id']
                    __sub_collection_uris.append(__sm_uri)

                    __response          = self.connection.get(__sm_uri)
                    __sub_collection.append(__response.obj)
        
        return __sub_collection, __sub_collection_uris


    # ------------------- Power on server and wait for POSt to complete
    def poweron_and_wait_post(self):
        # Check server power status
        for __uri in self.collection_uris:
            __resp              = self.connection.get(__uri)
            _m                  = __resp.obj
            _power_state        = _m["PowerState"]

            if (_power_state == 'Off'):
                # Power On server 
                _action             = dict(ResetType = 'On')
                _action_endpoint    = __uri + '/Actions/ComputerSystem.Reset/'
                __resp              = self.connection.post(_action_endpoint, _action)

                time.sleep(5)

                ### Query PostState
                __resp              = self.connection.get(__uri)
                _m                  = __resp.obj
                _oem                = _m['Oem']['Hpe']
                _post_state         = _oem['PostState']
                _device_discover    = _oem['DeviceDiscoveryComplete']['DeviceDiscovery']
                
                # Wait for POST to complete
                _iteration          = 0
                _device_discover    = ''

                while  'DeviceDiscoveryComplete' not in _device_discover:
                    time.sleep(1)
                    _iteration  = _iteration + 1 

                    __resp              = self.connection.get(__uri)
                    _m                  = __resp.obj

                    ### PostState
                    _oem                = _m['Oem']['Hpe']
                    _post_state         = _oem['PostState']
                    _device_discover    = _oem['DeviceDiscoveryComplete']['DeviceDiscovery']


    # ----------------- generate error message    
    def generate_error_message(self, msg):
        _error              = dict()
        _error['error']     = dict()
        _error['error']['@Message.ExtendedInfo'] = [dict(MessageId = msg)] 
        return _error


