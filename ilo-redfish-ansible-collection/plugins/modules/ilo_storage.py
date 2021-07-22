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
module: ilo_storage.py
short_description: Create and delete storage
description:
    - Create and delete storage
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
  - name: ilo storage - create 
     ilo_storage:
        ilo_ip            : "{{ilo_ip}}"
        ilo_username      : "{{ username }}"
        ilo_password      : "{{ password }}"

        type              : SmartStorage              # Choices : SmartStorage - LocalStorage
        controller        : SmartArrayController      # Choices : SmartArrayController - HostBusAdapter if SmartStorage
        state             : present
        data:
          raid            : Raid1                     # Choices: Raid0 - Raid1 - Raid10
          physical_drives : ["1I:1:2", "2I:1:6"]
          name            : 'my_logical_drive_name'   # Optional, - if omitted - use system defined name     
     
     register: result

   - debug: var=result['system']

   - name: ilo storage - delete
     ilo_storage:
        ilo_ip            : "{{ilo_ip}}"
        ilo_username      : "{{ username }}"
        ilo_password      : "{{ password }}"

        type              : SmartStorage              # Choices : SmartStorage - LocalStorage
        controller        : SmartArrayController      # Choices : SmartArrayController - HostBusAdapter if SmartStorage
        state             : absent
        data:
          physical_drives : ["1I:1:2", "2I:1:6"]
          name            : 'my_logical_drive_name'   # Optional, - if omitted - use system defined name     
     
     register: result

   - debug: var=result['system'] 





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
                type          =dict(type="str", required=False, choices=['SmartStorage','LocalStorage' ]),
                controller    =dict(type="str", required=False, choices=['SmartArrayController','HostBusAdapter' ]),
                state         =dict(type="str", required=False, choices=['present','absent','erase','init' ]),
                data          =dict(type="dict", required=False, default=None)
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


    _type               = _module.params.get('type')
    _controller         = _module.params.get('controller')
    _state              = _module.params.get('state')
    _data               = _module.params.get('data')

    if _data is not None:
      _raid             = None
      if 'raid' in _data.keys():
        _raid           = _data['raid']
      
      _physical_drives  = None
      if 'physical_drives' in _data.keys():
        _physical_drives  = _data['physical_drives']

      _name             = _data['name']

    
    _sys_result = None
    if _type is not None:
      if _type == 'SmartStorage':
          if _controller == 'SmartArrayController':
            if _data is not None:
              # Create logical drive
              if _state == 'present':
                _sys, _status, _msg   = system.create_logical_drive(raid=_raid,name=_name, drive_list=_physical_drives)
                _sys_result           = dict(storage=_sys)

              # Delete logical drive
              if _state == 'absent':
                _sys, _status, _msg   = system.delete_logical_drive(name=_name, drive_list=_physical_drives)
                _sys_result           = dict(storage=_sys)


          if _controller == 'HostBusAdapter':
            pass

    result = dict(changed= _status, system=json.dumps(_sys_result, indent=4))

    # Logout redfish and exit
    if _status:
      _module.exit_json(**result)
    else:
      _module.fail_json(msg = _msg)

    _connection.logout()




if __name__ == "__main__":
    run_module()
