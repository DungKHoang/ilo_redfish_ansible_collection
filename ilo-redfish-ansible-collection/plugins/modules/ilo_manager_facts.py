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
module: ilo_manager_facts
short_description: Retrieve facts about iLO manager 
description:
    - Retrieve facts about iLO manager
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
- name: Gather facts about managers - Summary
  ilo_manager_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
  register: result
- debug: var=result['ilo']

- name: Gather facts about ilo firmware
  ilo_manager_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option:       Firmware
  register: result
- debug: var=result['ilo']['firmware']

- name: Gather facts about ilo networks
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option:       Network
  register: result
- debug: var=result['ilo']['network']



'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iloRedfish import RedFishModule
from ansible.module_utils.managers import MANAGERS

class ManagerFactsModule(object):
    def __init__(self):        
        self.connection       = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        =dict(type="str", required=True),
                ilo_username  =dict(type="str", required=True),
                ilo_password  =dict(type="str", required=True, default=None),
                option        =dict(type="str", required=False, choices=['Firmware','Network'])
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
    _man            = None
    manFactsModule  = ManagerFactsModule()
    _module         = manFactsModule.module
    _connection     = manFactsModule.redfish_client

    manager         = MANAGERS(_connection)

    # Get type of output for manager: Firmware - Network
    _option         = _module.params.get('option')
    
    if _option is not None:
      if _option == 'Firmware':
          _man        = manager.get_manager_info()
          _man_result = dict(firmware=_man['Firmware'])
    

      if _option == 'Network':
          _man        = manager.get_interface_info()  
          _man_result = dict(network=_man) 
      

    else:
       _man_result  = manager.get_manager_info()

    result = dict(changed= False, ilo=json.dumps(_man_result, indent=4))

    # Logout redfish and exit
    _connection.logout()
    _module.exit_json(**result)



if __name__ == "__main__":
    run_module()
