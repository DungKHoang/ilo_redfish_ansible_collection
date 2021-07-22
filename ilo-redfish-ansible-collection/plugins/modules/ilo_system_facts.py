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
module: ilo_system_facts
short_description: Retrieve facts about computersystem
description:
    - Retrieve facts about computersystem
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
- name: Gather facts about systems - Summary
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
  register: result
- debug: var=result['system']

- name: Gather facts about CPU
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option: Processors
  register: result
- debug: var=result['system']['Processors']

- name: Gather facts about Memory
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option: Memory
  register: result
- debug: var=result['system']['memory']

- name: Gather facts about storage
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option: Storage
  register: result
- debug: var=result['system']['storage']
- debug: var=result['system']['storage']['local_storage']
- debug: var=result['system']['storage']['smart_array']
- debug: var=result['system']['storage']['host_bus_adapter']

- name: Gather facts about Network
  ilo_system_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    option: Network
  register: result
- debug: var=result['system']['network']

'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iloRedfish import RedFishModule
from ansible.module_utils.systems import SYSTEMS

class SystemFactsModule(object):
    def __init__(self):        
        self.connection       = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        =dict(type="str", required=True),
                ilo_username  =dict(type="str", required=True),
                ilo_password  =dict(type="str", required=True, default=None),
                option        =dict(type="str", required=False, choices=['Processors','Memory','Storage','Network','EthernetInterfaces'])
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
    _sys            = None
    sysFactsModule  = SystemFactsModule()
    _module         = sysFactsModule.module
    _connection     = sysFactsModule.redfish_client

    system          = SYSTEMS(_connection)

    # Get type of output for system: Processor, memory, Storage...
    _option         = _module.params.get('option')
    
    if _option is not None:
      if _option == 'Processors':
          _sys        = system.get_processor_info()
          _sys_result = dict(processors=_sys)

      if _option == 'Memory':
          _sys        = system.get_memory_info()  
          _sys_result = dict(memory=_sys) 
      
      if _option == 'Storage':
          _local,_sma, _hba = system.get_storage_info()
          _sys        = dict (
              local_storage     = _local,
              smart_array       = _sma,
              host_bus_adapter  = _hba 
          )          
          _sys_result = dict(storage=_sys)

      if _option == 'Network':
        _sys        = system.get_network_adapter_info()
        _sys_result = dict(network=_sys)


    else:
       _sys_result  = system.get_system_info()

    result = dict(changed= False, system=json.dumps(_sys_result, indent=4))

    # Logout redfish and exit
    _connection.logout()
    _module.exit_json(**result)



if __name__ == "__main__":
    run_module()
