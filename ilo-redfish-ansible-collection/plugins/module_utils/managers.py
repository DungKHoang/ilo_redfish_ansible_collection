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
module: managers
short_description: Common routines and class for ilo_managers and ilo_manager_facts
description:
    - get_all                       : query iLO to get collection of system resources
    - get_manager_info              : ilo Information
    - get_interface_info            : get IPv4, IPv6, host name
    - get_firmware_info             : get firmware
    - set_ipv4_interface            : set IPv4
    - set_ntp_server                : set ntp 
    - reset_ilo                     : reset ilo



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
from datetime import datetime as dt

from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

# -------------------------------------------
#   Relate to Ansible
#Instantiating module class        
#from ansible.module_utils.basic import *
#from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.iloRedfish import RedFishModule


#-------------------------------------------------


class MANAGERS:

    MSG_MAINTENANCE_EXISTED                     = 'iLO - Maintenance Window already exists'
    MSG_MAINTENANCE_ATTRIBUTE_ERROR             = 'iLO - Error in attribute specified for maintenance window. Value is {0}'    

    def __init__(self, connection):

        self.endpoint                                                   = '/redfish/v1/Managers' 
        self.updateservice                                              = '/redfish/v1/UpdateService'
        self.maintenance                                                = '/redfish/v1/UpdateService/MaintenanceWindows'

        self.connection                                                 = connection
          
        self.main_interface                                             = None                  # Main network interface
        self.collection,self.collection_uris                            = self.get_all()                  # All members of self.endpoint
        self.maintenance_collection, self.maintenance_collection_uris   = self.get_sub_collection_by(self.maintenance)
         


    
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

    # ----------------- get iLO iformation

    def get_manager_info(self):
        if self.collection is None:
            self.collection,self.collection_uris = self.get_all()
    
        for _m in self.collection:
            _oem                        = _m['Oem']['Hpe']
            _ilo_info                   = dict(
                Firmware                = _m['FirmwareVersion'],
                Model                   = _m['Model'],
                License                 = _oem['License'],
                SelfTestResults         = _oem['iLOSelfTestResults'],
                Links                   = _oem['Links']
            )
        return _ilo_info



    # ----------------- get iLO firmware

    def get_firmware_info(self):
        #for _m in self.collection:
        _m                  = self.collection
        _model              = _m['Model']
        _fw                 = _m['Oem']['Hpe']['Firmware']['Current']
        _fw                 = _fw['VersionString']
        _fw_date            = _fw['Date']

        _fw_info            = dict(
            model           = _model,
            firmware        = _fw,
            date    = _fw_date
        )

        return _fw_info



    # ----------------- get IPv4, IPv6, host name
    def get_interface_info(self):
        for _m in self.collection:
            __uri               = _m['EthernetInterfaces']['@odata.id']
            __response          = self.connection.get(__uri)
            #1st element is the main interface
            self.main_interface = __response.obj['Members'][0]['@odata.id']  
            __response          = self.connection.get(self.main_interface)    
            _m                  = __response.obj
            fqdn                = _m['FQDN']
            hostname            = _m['HostName']
            mac                 = _m['MACAddress']
            ipv4                = _m['IPv4Addresses'][0]
            ipv6                = _m['IPv6Addresses'][0]
            dns                 = _m['NameServers']
            dhcpv4              = _m['Oem']['Hpe']['DHCPv4']
            dhcpv6              = _m['Oem']['Hpe']['DHCPv6']

        return hostname,fqdn, mac, ipv4, ipv6, dns, dhcpv4, dhcpv6


    # ----------------- set ipV4 
    def set_ipv4_interface(self, new_hostname, new_domain_name, new_ipv4_dict, new_dns_list ):

        #         new_ipv4_dict            = {
        #    'Address'       : '10.1.1.43',                  # IP address is a required field
        #    'SubnetMask'    : '255.255.0.0',
        #    'Gateway'       : '10.1.1.250' 
        #}



        # Save current information
        hostname,fqdn, mac, ipv4, ipv6, dns, dhcpv4, dhcpv6  = self.get_interface()

        ### Set DHCPv4, DHCP v6
        #DHCPv4 : @{Enabled=False; UseDNSServers=False; UseDomainName=False; UseGateway=False; UseNTPServers=False;UseStaticRoutes=False}
        #DHCPv6 : @{OperatingMode=Stateful; UseDNSServers=False; UseDomainName=False; UseNTPServers=True; UseRapidCommit=False}
        ####

        body        = dict()
        body.update({"Oem": {"Hpe": dict() }})      

        body['Oem']['Hpe']['DHCPv4']                    = dict()

        if dhcpv4['Enabled'] :
            body['Oem']['Hpe']['DHCPv4']['Enabled']     = False

        body['Oem']['Hpe']['DHCPv4']['UseDNSServers']   = False
        body['Oem']['Hpe']['DHCPv4']['UseDomainName']   = False

        body['Oem']['Hpe']['DHCPv6']                    = dict() 
        body['Oem']['Hpe']['DHCPv6'] ['UseDNSServers']  = False     
        body['Oem']['Hpe']['DHCPv6'] ['UseDomainName']  = False


        if new_hostname is not None:
            body.update({'HostName' : new_hostname})
        
        if new_domain_name is not None:
            body['Oem']['Hpe']['DomainName']     = new_domain_name
            if new_hostname is not None:
                fqdn    = new_hostname + '.' + new_domain_name
                body.update({'FQDN' : fqdn})
        
        if new_dns_list is  not None:
            body['Oem']['Hpe']['IPv4']                      =  dict() 
            body['Oem']['Hpe']['IPv4']['DNSServers']        = new_dns_list 
            body['Oem']['Hpe']['IPv4']['DDNSRegistration']  = True 
        
        if new_ipv4_dict is not None:
            body.update({"IPv4Addresses" : [new_ipv4_dict] })              
                
        _resp   = self.connection.patch(self.main_interface, body) 
 
        return _resp.obj


    # ----------------- Set ntp servers
    def set_ntp_server(self, ntp_server_list):

        for __m in self.collection:
            __dt_uri    = __m["Oem"]["Hpe"]["Links"]["DateTimeService"]["@odata.id"]

        body        = dict()
        body.update({"Oem": {"Hpe": dict() }}) 
        body['Oem']['Hpe']['DHCPv6']                    = dict() 
        body['Oem']['Hpe']['DHCPv6'] ['UseNTPServers']  = False       # for manual setting of NTP    
        _resp       = self.connection.patch(self.main_interface, body)   
        
        # - Set NTP servers
        body        = {'StaticNTPServers'   : ntp_server_list}
        _resp       = self.connection.patch(__dt_uri, body)

        return _resp.obj



    # ----------------- reset ilo
    def reset_ilo(self):
        # Reset ilo
        for _m in self.collection:
            __target        = _m['Actions']['#Manager.Reset']['target']
            _resp           = self.connection.post(__target, {}) 
        
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
  
    







