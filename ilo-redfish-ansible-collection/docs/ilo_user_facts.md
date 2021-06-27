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
  type:
    description: filter to select iLO accounts 
    choices: UserName, RoleId
    type: str
    required: false
  name:
    description: filter to select iLO accounts 
    choices: Administrator, Operator, ReadOnly if type == RoleId
    type: str
    required: false    
```

##### EXAMPLES
```YAML
- name: Gather facts about iLO accounts
  ilo_user_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
  no_log: true
  register: result
- debug: var=result['user']


- name: Get account based on filter UserName
  ilo_user_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    type:     'UserName'
    name:     'this_user'
  no_log: true
  register: result
- debug: var=result['user']


- name: Get account based on filter RoleId
  ilo_user_facts:
    ilo_ip:       {{'ilo_ip'}}
    ilo_username: {{'ilo_username'}}
    password:     {{'ilo_password'}}
    type:     'RoleId'
    name:     'Operator'      # Possible values: Administrator, Operator, ReadOnly
  no_log: true
  register: result
- debug: var=result['user']

```