# Ansible Modules for iLO Redfish

Modules to manage iLO using Ansible playbooks.

## Requirements

 - Ansible >= 2.1
 - Python >= 2.7.9
 -  Python ilo Rest  ([Install python ilorest](https://github.com/HewlettPackard/python-ilorest-library))
 

### 1. Download the ZIP file from github
### 2. Unzip to a local folder


### 2. Configure the ANSIBLE_LIBRARY environmental variable

Set the environment variables `ANSIBLE_LIBRARY` and `ANSIBLE_MODULE_UTILS`, specifying the `library` full path from the cloned project:

```bash
$ export ANSIBLE_LIBRARY=/path/to/ilo_redfish_collection/plugins/modules
$ export ANSIBLE_MODULE_UTILS=/path/to/ilo_redfish_collection/plugins/module_utils