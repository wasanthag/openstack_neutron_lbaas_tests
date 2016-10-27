# openstack_neutron_lbaas_tests

This is a crude python test frame work based on openstack python SDK and AVI REST API that tests the following,

1) CRUD operations of neutron lbaas service for provider avi lbaas. This should equally work for HA proxy with minimal changes but this is not tested. Following are tested

    - creating networking, routers and backend servers for load balancers 
    - create lbaas pool, add members , create health monitor, create vip and assign floating IP
    - delete lbaas pool, remove members , delete vip and health monitor and free floating ips
    - modify lbaas algorithms between ROUND_ROBIN, SOURCE_IP and LEAST_CONNS
    - remove and add members to a pool
    - measure the time between creating a VIP and becomes available
    - send traffic to VIP (floating ip)

2) Health of AVI controllers such

    - AVI controller cluster status
    - software versions
    - various config parameters : HA mode, number of SEs, SE redundancy mode

## Install and setup

This repo has a vagrant file which can be used to spin up a ubuntu vm with virtual box , install necessary packages and run the tests.
Required packages can be manually installed,
```
apt-get update
apt-get install -y python-pip git git-review python python-dev python-virtualenv curl
pip install --upgrade pip
pip install python-novaclient==3.2.0
pip install python-neutronclient==4.0.0
pip install python-keystoneclient==2.0.0
pip install pyopenssl ndg-httpsclient pyasn1
pip install PyYAML requests simplejson
```
At the moment the script should be run as a non admin openstack user and all site specific parameters must be added in to config.yml to be read by the script. 


## Script Options

 

This script allows to run individual operations as shown with the help below as well as run all tests in sequence with -r option. If run as individual configurations to setup lbaas services , you will have to run the script with -s option first which setup the network and compute. Once compute and networking is setup, -c option will create the lbaas components. The option -d will just delete your lbaas configuration but leave the base network and compute intact. The -u option will delete all configs including lbaas, compute and networking.

Option -r will first look for any existing instances, network and lbaas configs created and delete them before running all tests.

Option -ls and -fn are calling shell scripts within the python and used to list all configurations for the current tenant and forcefully delete neutron left over configs in the event of the script was unable to delete subnet/network and security groups. This is seen when AVI controllers do not delete SE neutron ports in time after config removal.


```
venv)laptop-linux ~/my_scripts/lbaas-testing/$ ./os-lbaas-test.py -h
INFO:Reading OS Credentials from config.yaml keystone section
usage: os-lbaas-test.py [-h] [-s] [-c] [-d] [-u] [-t] [-r] [-ml] [-ms]
                              [-mr] [-ls] [-fn] [-avi] [-ss] [-rs]
AVI OpenStack LBaaS Test Tool
optional arguments:
  -h, --help            show this help message and exit
  -s, --setup           Setup compute and network for lbaas testing
  -c, --create_lbaas    Start creating lbaas service
  -d, --delete_lbaas    Delete lbaas configs only
  -u, --cleanup         Cleanup compute and network created for lbaas testing
  -t, --send_traffic    Send traffic to the VIP
  -r, --runner          run all tests
  -ml, --modify_lb_method_lc
                        Modify LB method to LEAST_CONNECTIONS
  -ms, --modify_lb_method_si
                        Modify LB method to SOURCE_IP
  -mr, --modify_lb_method_rr
                        Modify LB method to ROUND_ROBIN
  -ls, --list_configs   List All Lbaas and neutron configs
  -fn, --clean_neutron  Clean neutron subnet, network and sec group
  -avi, --check_avi     Check AVI controller health and configs
  -ss, --suspend_vm     Suspend instance 1
  -rs, --resume_vm      Resume instance 1
```
