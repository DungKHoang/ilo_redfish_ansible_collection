#!/usr/bin/python
# -*- coding: utf-8 -*-
###
# Copyright (2016-2019) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from __future__ import (absolute_import, division, print_function, unicode_literals)

import abc
import collections
import json
import logging
import os
import traceback
import sys

try:
    from ansible.module_utils import six
    from ansible.module_utils._text import to_native
except ImportError:
    import six
    to_native = str



from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

#Instantiating module class        
from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule




ACCOUNTSERVICE            = '/redfish/v1/AccountService' 
CHASSIS                   ='/redfish/v1/Chassis'  
EVENTSERVICE              ='/redfish/v1/EventService'  
JSONSCHEMAS               ='/redfish/v1/JsonSchemas'  
MANAGERS                  ='/redfish/v1/Managers'  
REGISTRIES                ='/redfish/v1/Registries'  
SESSIONSERVICE            ='/redfish/v1/SessionService'  
SYSTEMS                   ='/redfish/v1/Systems'  
TASKS                     ='/redfish/v1/TaskService'  
TELEMETRYSERVICE          ='/redfish/v1/TelemetryService'  
UPDATESERVICE             ='/redfish/v1/UpdateService'  

def transform_list_to_dict(list_):
    """
    Transforms a list into a dictionary, putting values as keys.

    :arg list list_: List of values
    :return: dict: dictionary built
    """

    ret = {}

    if not list_:
        return ret

    for value in list_:
        if isinstance(value, collections.Mapping):
            ret.update(value)
        else:
            ret[to_native(value)] = True

    return ret

def merge_list_by_key(original_list, updated_list, key, ignore_when_null=None):
    """
    Merge two lists by the key. It basically:

    1. Adds the items that are present on updated_list and are absent on original_list.

    2. Removes items that are absent on updated_list and are present on original_list.

    3. For all items that are in both lists, overwrites the values from the original item by the updated item.

    :arg list original_list: original list.
    :arg list updated_list: list with changes.
    :arg str key: unique identifier.
    :arg list ignore_when_null: list with the keys from the updated items that should be ignored in the merge,
        if its values are null.
    :return: list: Lists merged.
    """
    ignore_when_null = [] if ignore_when_null is None else ignore_when_null

    if not original_list:
        return updated_list

    items_map = collections.OrderedDict([(i[key], i.copy()) for i in original_list])

    merged_items = collections.OrderedDict()

    for item in updated_list:
        item_key = item[key]
        if item_key in items_map:
            for ignored_key in ignore_when_null:
                if ignored_key in item and item[ignored_key] is None:
                    item.pop(ignored_key)
            merged_items[item_key] = items_map[item_key]
            merged_items[item_key].update(item)
        else:
            merged_items[item_key] = item

    return list(merged_items.values())

def _str_sorted(obj):
    if isinstance(obj, collections.Mapping):
        return json.dumps(obj, sort_keys=True)
    else:
        return str(obj)

def _standardize_value(value):
    """
    Convert value to string to enhance the comparison.

    :arg value: Any object type.

    :return: str: Converted value.
    """
    if isinstance(value, float) and value.is_integer():
        # Workaround to avoid erroneous comparison between int and float
        # Removes zero from integer floats
        value = int(value)

    return str(value)


class RedFishModuleException(Exception):
    """
    RedFish base Exception.

    Attributes:
       msg (str): Exception message.
       redfish_response (dict): redfish rest response.
   """

    def __init__(self, data):
        self.msg = None
        self.redfish_response = None

        if isinstance(data, six.string_types):
            self.msg = data
        else:
            self.redfish_response = data

            if data and isinstance(data, dict):
                self.msg = data.get('message')

        if self.redfish_response:
            Exception.__init__(self, self.msg, self.redfish_response)
        else:
            Exception.__init__(self, self.msg)

            

# @six.add_metaclass(abc.ABCMeta)



class RedFishModule:
    '''
    iloRedFish ansible module wrapper class
    '''
    MSG_CREATED                 = 'Resource created successfully.'
    MSG_UPDATED                 = 'Resource updated successfully.'
    MSG_DELETED                 = 'Resource deleted successfully.'
    MSG_ALREADY_PRESENT         = 'Resource is already present.'
    MSG_ALREADY_ABSENT          = 'Resource is already absent.'
    MSG_DIFF_AT_KEY             = 'Difference found at key \'{0}\'. '
    MSG_MANDATORY_FIELD_MISSING = 'Missing mandatory field: name'

        

    def __init__(self, module_args):
        """
       module init function

        """
        self.redfish_client         = self.create_redfish_client(module_args)


    def create_redfish_client(self, module_args):


        SYSTEM_URL          = "https://" + module_args['ilo_ip']
        LOGIN_ACCOUNT       = module_args['ilo_username']  
        LOGIN_PASSWORD      = module_args['ilo_password'] 

        try:
            # Create a Redfish client object
            redfish_client = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, password=LOGIN_PASSWORD)
            redfish_client.login()


        except ServerDownOrUnreachableError as exception:
            error_msg       = '; '.join(to_native(e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

        return redfish_client

    def get(self, endpoint):
        '''
            return object 
        '''            
        response            = self.redfish_client(endpoint)
        return response.obj