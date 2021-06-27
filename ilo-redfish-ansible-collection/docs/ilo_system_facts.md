# module: ilo_user_facts

description: This modules provides facts of ilo users/accounts  

##### ARGUMENTS
```YAML
  ilo_ip:
    description: IP address of iLO 
    type: str
    required: true
  ilo_username:
    description: Admin account to access iLO
    type: str
    required: true
  ilo_password:
    description: Admin account password to access iLO
    type: str
    required: true
  options:
    description: type of system inof
    choices: Processors, Memory, Storage
    type: str
    required: false
   
```

##### EXAMPLES
```YAML
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
- debug: var=result['system']['processors']

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



```