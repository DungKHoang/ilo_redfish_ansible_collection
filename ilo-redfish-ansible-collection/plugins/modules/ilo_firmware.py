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
module: ilo_firmware
short_description: management of firmware update 
description:
    - Manage maintenance window
    - Update iLO firmware
    - Update System BIOS
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
- name: Create maintenance window
  ilo_firmware:
    ilo_ip          : "{{ ip }}"
    ilo_username    : "{{ username }}"
    ilo_password    : "{{ password }}"
    
    state:              present
    option:             Maintenance Window
    data:
        name:           '1st Maintenance window'
        description:    '1st window for maintenance'
        start_time:     'Jul 21 2021 5:00PM'        # Either use long date
        end_time:       '07/22/2021 8:00AM'         # Or use short date

  register: result
- debug: var=result['ilo']['maintenance']

- name: Delete maintenance window
  ilo_firmware:
    ilo_ip          : "{{ ip }}"
    ilo_username    : "{{ username }}"
    ilo_password    : "{{ password }}"}

    state:              absent
    option:             Maintenance Window
    data:
        name:           '1st Maintenance window'
        id:             '23675'                  # Optional - Maintenance window ID

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
from ansible.module_utils.managers import MANAGERS

class FirmwareModule(object):
    def __init__(self):        
        self.connection       = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        =dict(type="str", required=True),
                ilo_username  =dict(type="str", required=True),
                ilo_password  =dict(type="str", required=True, default=None),
                state         =dict(type="str", required=True, choices=['present','absent', 'update']),
                option        =dict(type="str", required=True, choices=['Maintenance Window','Firmware']),
                data          =dict(type="dict", required=True, default=None)
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
    firmwareModule  = FirmwareModule()
    _module         = firmwareModule.module
    _connection     = firmwareModule.redfish_client

    manager         = MANAGERS(_connection)

    # Get data
    _option         = _module.params.get('option')
    _state          = _module.params.get('state')
    _data           = _module.params.get('data')


    if _option == 'Firmware':
        pass
        #_man        = manager.get_manager_info()
        #_man_result = dict(firmware=_man['Firmware'])


    if 'Maintenance' in _option:
        _fw_result      = None
        _msg            = None
        _status         = False

        _name           = _data['name']
        _description    = _data['description']
  
        if _state == 'present':
            _start_time                 = _data['start_time']
            _end_time                   = _data['end_time']
            _fw_result, _msg, _status   = manager.create_maintenance_window( name= _name, description=_description, 
                                            start_time=_start_time, end_time=_end_time)
        if _state == 'absent':
            _id         = _data['id']
            pass

        
    result = dict(changed= _status, ilo=json.dumps(_fw_result, indent=4))

    if _status:
      _module.exit_json(**result)
    else:
      _module.fail_json(msg = _msg)

    _connection.logout()


if __name__ == "__main__":
    run_module()
