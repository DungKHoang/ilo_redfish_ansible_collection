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
- name: Gather facts about iLO accounts
  ilo_user_facts:
    ilo_ip: 172.16.101.48
    ilo_username: administrator
    password: my_password
  no_log: true
  register: result
- debug: var=result['user']


- name: Get account based on filter ilo_username
  ilo_user_facts:
    ilo_ip:  172.16.101.48
    ilo_username: administrator
    password: my_password
    type:     'ilo_username'
    name:     'this_user'
  no_log: true
  register: result
- debug: var=result['user']


- name: Get account based on filter RoleId
  ilo_user_facts:
    ilo_ip:  172.16.101.48
    ilo_username: administrator
    password: my_password
    type:     'RoleId'
    name:     'Operator'      # Possible values: Administrator, Operator, ReadOnly
  no_log: true
  register: result
- debug: var=result['user']

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

class UserFactsModule(object):
    def __init__(self):        
        self.connection       = None
        REDFISH_COMMON_ARGS   = dict(
                ilo_ip        =dict(type="str", required=True),
                ilo_username  =dict(type="str", required=True),
                ilo_password  =dict(type="str", required=False, default=None),
                type          =dict(type="str", required=False, default='UserName'),
                name          =dict(type="str", required=False, default=None)
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
    userFactsModule = UserFactsModule()
    _module         = userFactsModule.module
    _connection     = userFactsModule.redfish_client

    users           = USERS(_connection)

    # Get filter - RoleId or ilo_username
    _type           = _module.params.get('type')
    _name           = _module.params.get('name')

    if _type is not None and _name is not None:
      _collection, _collection_uris    = users.get_by(_type, _name)
    else:
      _collection, _collection_uris    = users.get_all()

    result = dict(changed= True, user=json.dumps(_collection, indent=4))

    # Logout redfish and exit
    _connection.logout()
    _module.exit_json(**result)



if __name__ == "__main__":
    run_module()
