# module: ilo_user

description: This modules enables configuration of iLO accounts  

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
  state:
    description: Create or remove iLO account
    Choices:     present ---> Account will be created
                 absent ---> account will be deleted
  username:
    description: name of user to be configured 
    type: str
    required: true
  loginame:
    description: login name of user to be configured  
    choices: Administrator, Operator, ReadOnly if type == RoleId
    type: str
    required: false 
  password:
    description: password for new user
    type: str
    required: false
  roleid:
    description: RoleId for new user
    choices:     Administrator, Operator, ReadOnly
  privileges:
    description: if RoleId is not specified, define custom privileges 
    choices:
      - LoginPriv                                                    
      - HostBIOSConfigPriv 
      - HostNICConfigPriv                                             
      - HostStorageConfigPriv   
      - RemoteConsolePriv       
      - UserConfigPriv          
      - VirtualMediaPriv        
      - VirtualPowerAndResetPriv
      - iLOConfigPriv  

```

##### EXAMPLES
```YAML
   - name: create user with privs
     ilo_user:
        ilo_ip:       {{'ilo_ip'}}
        ilo_username: {{'ilo_username'}}
        password:     {{'ilo_password'}}

        state                       : present       
        data:
          username                  : new_user
          loginname                 : new_loginname
          password                  : new_password
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
     no_log: true
     register: result
   - debug: var=result['user'] 

   - name: create user with roleid
     ilo_user:
        ilo_ip:       {{'ilo_ip'}}
        ilo_username: {{'ilo_username'}}
        password:     {{'ilo_password'}}

        state                       : present       
        data:
          username                  : new_user
          loginname                 : new_loginname
          password                  : new_password
          roleid                    : Operator  # Possible values: Administrator,Operator,ReadOnly                                             
     no_log: true
     register: result
   - debug: var=result['user'] 

   - name: delete user
     ilo_user:
        ilo_ip        : "{{ ip }}"
        ilo_username  : "{{ username }}"
        ilo_password  : "{{ password }}"

        state                       : absent       
        data:
          username                  : user_to_be_deleted

```