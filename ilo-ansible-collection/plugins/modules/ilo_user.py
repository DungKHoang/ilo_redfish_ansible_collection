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
module: ilo_user_facts
short_description: Retrieve facts about iLO accounts
description:
    - Retrieve facts about iLO accounts
version_added: "1.0"
requirements:
    - iLO 5
author:
    - Dung K Hoang
'''

EXAMPLES = '''
   - name: create user with privs
     ilo_users:
        ilo_ip        : "10.1.1.7"
        ilo_username  : "{{ username }}"
        ilo_password  : "{{ password }}"

        state                       : present       
        data:
          username                  : user_custom_privs
          loginname                 : user_custom_privs
          password                  : some_password
          #roleid                   :  Possible values: Administrator , Operator, ReadOnly. If RoleId is not defined, use custom privileges below
          privileges:
            - LoginPriv                                                    
            - HostBIOSConfigPriv 
            - HostNICConfigPriv                                             
            - HostStorageConfigPriv   
            - RemoteConsolePriv       
            - UserConfigPriv          
            - VirtualMediaPriv        
            - VirtualPowerAndResetPriv
            - iLOConfigPriv
  register: result
- debug: var=result['ansible_facts']['accounts']

- name: create user with privs
     ilo_user:
        ilo_ip        : "10.1.1.7"
        ilo_username  : "{{ username }}"
        ilo_password  : "{{ password }}"

        state                       : present       
        data:
          username                  : user_with_operator_role
          loginname                 : user_with_operator_role
          password                  : some_password
          roleid                   :  Operator

  register: result
- debug: var=result['ansible_facts']['accounts']

   - name: delete user with state = absent
     ilo_user:
        ilo_ip        : "10.1.1.7"
        ilo_username  : "{{ username }}"
        ilo_password  : "{{ password }}"

        state                       : absent       
        data:
          username                  : user_to_delete

'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iloRedfish import RedFishModule
from ansible.module_utils.users import USERS

class UsersModule(object):
    def __init__(self):        
        self.connection        = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        = dict(type="str", required=True),
                ilo_username  = dict(type="str", required=True),
                ilo_password  = dict(type="str", required=True, default=None),
                state         = dict(type="str", required=True, choices=['present', 'absent']),
                data          = dict(type="dict", required=False, default=None)
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

    usersModule     = UsersModule()
    _module         = usersModule.module
    _connection     = usersModule.redfish_client

    users           = USERS(_connection)

    _state          = _module.params.get('state')
    _data           = _module.params.get('data')

    _msg            = ''
    _value          = None
    _status         = False

    if _state == 'present': 
        _roleid       = None
        _privileges   = []

        _username     = _data['username']
        _password     = _data['password']
        _loginname    = _data['loginname']
        if 'roleid' in _data.keys():
          _roleid     = _data['roleid']
        else:
          _privileges = _data['privileges']

        # Create user   username, password, roleid, loginname, privileges
        _msg, _value, _status = users.create_user(username=_username, password=_password, roleid=_roleid, loginname=_loginname,privileges= _privileges )    
        result = dict(changed= True, user=json.dumps(_value, indent=4))


    if _state == 'absent': 
        _username     = _data['username']
        _msg, _status = users.delete_user(_username)
        result        = dict(changed=_status, user=_msg)
        
      
    # Logout redfish and exit
    _connection.logout()
    if _status:
      _module.exit_json(**result)
    else:
      _module.fail_json(msg = _msg)
    




if __name__ == "__main__":
    run_module()
