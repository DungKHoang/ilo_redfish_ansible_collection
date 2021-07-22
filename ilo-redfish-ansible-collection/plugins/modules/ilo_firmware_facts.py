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
module: ilo_firmware_facts
short_description: Retrieve facts about iLO firmware 
description:
    - Retrieve facts about iLO firmware
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
    - name: Gather facts about firmware inventory 
      ilo_firmware_facts:
        ilo_ip          : "{{ ip }}"
        ilo_username    : "{{ username }}"
        ilo_password    : "{{ password }}"
        option          : firmware_inventory
      register: result
    - debug: var=result['ilo']

    - name: Gather facts about software install set
      ilo_firmware_facts:
        ilo_ip          : "{{ ip }}"
        ilo_username    : "{{ username }}"
        ilo_password    : "{{ password }}"
        option          : install_set
      register: result
    - debug: var=result['ilo']

    - name: Gather facts about maintenance_window
      ilo_firmware_facts:
        ilo_ip          : "{{ ip }}"
        ilo_username    : "{{ username }}"
        ilo_password    : "{{ password }}"
        option          : maintenance_window
      register: result
    - debug: var=result['ilo']

    - name: Gather facts about component respository
      ilo_firmware_facts:
        ilo_ip          : "{{ ip }}"
        ilo_username    : "{{ username }}"
        ilo_password    : "{{ password }}"
        option          : component_respository
      register: result
    - debug: var=result['ilo']



'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iloRedfish import RedFishModule
from ansible.module_utils.firmware import FIRMWARE

class FirmwareFactsModule(object):
    def __init__(self):        
        self.connection       = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        =dict(type="str", required=True),
                ilo_username  =dict(type="str", required=True),
                ilo_password  =dict(type="str", required=True, default=None),
                option        =dict(type="str", required=True, choices=['firmware_inventory','component_repository', 'maintenance_window', 'install_set']),
        )
        _module                 = AnsibleModule(argument_spec=REDFISH_COMMON_ARGS, supports_check_mode=True)
        REDFISH_COMMON_ARGS     = dict(
            ilo_ip              = _module.params['ilo_ip'],
            ilo_username        = _module.params['ilo_username'],
            ilo_password        = _module.params['ilo_password']
        )

        _redfish                = RedFishModule(module_args=REDFISH_COMMON_ARGS) 

        self.redfish_client     = _redfish.redfish_client
        self.module             = _module

def run_module():
    _fw             = None
    firmwareModule  = FirmwareFactsModule()
    _module         = firmwareModule.module
    _connection     = firmwareModule.redfish_client

    firmware         = FIRMWARE(_connection)

    # Get data
    _option         = _module.params.get('option')

    
    if _option == 'firmware_inventory':
          _fw         = firmware.get_firmware_inventory()
          _fw_result = dict(firmware_inventory=_fw)

    if _option == 'component_repository':
          _fw        = firmware.repository_collection  
          _fw_result = dict(component_repository=_fw) 

    if _option == 'maintenance_window':
           _fw        = firmware.maintenance_collection  
           _fw_result = dict(maintenance_window=_fw)  

    if _option == 'install_set':
           _fw        = firmware.install_set_collection  
           _fw_result = dict(install_set=_fw) 

    result = dict(changed= False, ilo=json.dumps(_fw_result, indent=4))

    # Logout redfish and exit
    _connection.logout()
    _module.exit_json(**result)



if __name__ == "__main__":
    run_module()
