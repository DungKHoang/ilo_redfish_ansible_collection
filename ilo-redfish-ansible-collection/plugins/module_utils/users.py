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
module: users
short_description: Common routines and class for ilo_user_facts and ilo_users modules
description:
    - get_all           : query iLO to get list of accounts
    _ get_by(type, name): query iLo for users with filter : UserName or RoleId
    - create_user       : create an iLO accoutn with username,password,loginname,roleid, privileges
    - delete_user       : delete iLOm account based on UserName

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


class USERS:

    MSG_ALREADY_PRESENT         = 'Account {0} is already present.'
    MSG_UPDATED                 = 'Resource updated successfully.'
    MSG_DELETED                 = 'Account {0} deleted successfully.'
    MSG_NOT_EXISTED             = 'Account {0} does not exist.'

    def __init__(self, connection):

        self.endpoint               = '/redfish/v1/AccountService/Accounts' 

        self.collection             = None                  # All members of self.endpoint

        self.connection             = connection


 
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

    # ---------------------- Get by name. role,...
    def get_by(self,type = None, name = None ):

        if type == 'name':
            type = 'UserName' 

        __collection, __collection_uris    = self.get_all()
        __acc   = None
        __uri   = None
        if type is not None:
            for i in range(len(__collection)):
                __m     = __collection[i]
                if __m[type] == name:
                    __acc = __m
                    __uri = __collection_uris[i]
                    break
        return __acc, __uri


    # ---------------------- Create account...
    def create_user(self,username, password, roleid, loginname, privileges = [] ):


        _msg                        = ''
        _new                        = None
        _this                       = None
        _status                     = True

        if username is not None:
            _this, _this_uri       = self.get_by(type='UserName', name = username)
            if _this is None:
                # Configure body 
                body                                = dict()

                if loginname is not None or privileges is not None:
                    body.update({'Oem': {'Hpe': dict() }}) 

                body['UserName']                    = username
                body['Password']                    = password
                
                if loginname is not None:
                    body['Oem']['Hpe']['LoginName'] = loginname
                
                if roleid is not None:
                    body['RoleId']                  = roleid
                else:
                    if (privileges is not None) :
                        privs = dict()
                        for _priv in privileges:
                            privs.update({_priv :True})
                        body['Oem']['Hpe']['Privileges']    = privs 
                

                __response          = self.connection.post(self.endpoint, body)
                _resp               = __response.obj
                _status             = True
                if 'error' in _resp.keys():
                    _msg            = _new['error']['@Message.ExtendedInfo'][0]['MessageId']
                    _status         = False

            else :
                _msg                = self.MSG_ALREADY_PRESENT.format(username)
                _status             = False
                _resp               = None


        return   _resp, _status, _msg


    # ---------------------- Delete account...
    def delete_user(self,username):
        _msg                         = ''
        

        if username is not None:
            _this, _this_uri        = self.get_by(type='UserName', name = username)
            if _this is not None:
                __response          = self.connection.delete(_this_uri)
                _resp               = __response.obj               
                _msg                = self.MSG_DELETED.format(username) 
                _status             = True          
            else:
                    _msg            = self.MSG_NOT_EXISTED.format(username)
                    _status         = False
                    _resp           = None


        return _resp, _status, _msg




