#!/usr/bin/env python
__author__ = 'wasanthag'
from os import environ as env
import keystoneclient.v2_0.client as ksclient
from neutronclient.v2_0 import client as neutronclient
from neutronclient.neutron import v2_0 as neutronV20
from novaclient.client import Client as nvclientv20
#from novaclient.v2.client import Client as nvclientv20
from novaclient.v2.servers import Server as svrs
from subprocess import call

import time
import yaml
import argparse
import struct
import socket
import os
import re
import sys

import avicontrollercheck

class Create_Networking(object):
    network_name = ""
    subnet_name = ""
    router_name = ""
    router_port_name = ""
    float_net_name = ''
    lbaas_provider = ''
    lb_pool_name = ""
    lb_vip_name = ""
    lb_monitor_name = ""
    lb_vip_port = ''
    lb_vip_ssl_port = ''
    resource_id = ''
    os_tenant_id =''
    number_of_vms = ''
    base_ip_address = ""

    created_pool = dict()
    created_member = dict()
    created_vip = dict()
    created_fip = dict()
    created_monitor = dict()


    def __init__(self):
        self.keystone = ksclient.Client(auth_url=env['OS_AUTH_URL'],
                                        username=env['OS_USERNAME'],
                                        password=env['OS_PASSWORD'],
                                        tenant_name=env['OS_TENANT_NAME'],
                                        region_name=env['OS_REGION'])

        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'network':
                    print "INFO:Reading configs from config.yaml %s section" % section
                    #self.txt = cfg[section]['net_name']
                    self.network_name = cfg[section]['net_name']
                    self.subnet_name = cfg[section]['subnet_name']
                    self.router_name = cfg[section]['router_name']
                    self.router_port_name = cfg[section]['router_port_name']
                    self.float_net_name = cfg[section]['float_net']
                    self.lbaas_provider = cfg[section]['lbaas_provider']
                    self.lb_pool_name = cfg[section]['lbaas_pool']
                    self.lb_vip_name = cfg[section]['lbaas_vip']
                    self.lb_monitor_name = cfg[section]['lbaas_monitor']
                    self.lb_vip_port = cfg[section]['lbaas_vip_port']
                    self.lb_vip_ssl_port = cfg[section]['lbaas_vip_ssl_port']


                elif section == 'keystone':
                    self.os_tenant_id = cfg[section]['os_tenant_id']

                elif section == 'compute':
                    self.number_of_vms = cfg[section]['number_of_vms']
                    self.base_ip_address = cfg[section]['vm_base_ip']


    def neutron_authenticate(self):
        try:

            self.endpoint_url = self.keystone.service_catalog.url_for(service_type='network')
            self.token = self.keystone.auth_token
            self.neutron = neutronclient.Client(endpoint_url=self.endpoint_url, token=self.token)
            return self.neutron

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred during authentication"
            print lbaas_excep
            sys.exit(1)


    def find_anything(self, resource_type, resource_name):
        self.resource_type = resource_type
        self.resource_name = resource_name


        try:
            self.resource_id = neutronV20.find_resourceid_by_name_or_id(self.neutron_authenticate(), self.resource_type, self.resource_name)
            print "INFO:Found Resource %s : %s" % (self.resource_type, self.resource_id)

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred during searching for resource"
            print lbaas_excep
            sys.exit(1)


        return self.resource_id


    def increment_ip(self, ip):
        ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
        x = ip2int(ip)
        x = x + 1
        int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
        return int2ip(x)


    def print_values(self, val, type):
        if type == 'ports':
            val_list = val['ports']
        if type == 'networks':
            val_list = val['networks']
        if type == 'routers':
            val_list = val['routers']
        if type == 'pools':
            val_list = val['pools']
        for p in val_list:
               print "++++++++++++++++++++++++++++++++++++++"
               for k, v in p.items():
                    print("%s : %s" % (k, v))

        return


    def display_networks(self):
        #import pdb
        #pdb.set_trace()
        try:
            n1 = self.neutron_authenticate()
            netw = n1.list_networks()
            print "+++++ Printing list of networks+++++"
            self.print_values(netw, 'networks')
            print "INFO:Successfully Displayed Networks \n"
        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred during display networks"
            print lbaas_excep
            sys.exit(1)


    def create_network(self):


         try:
            print('TASK:Creating Network %s .......' % self.network_name)
            n1 = self.neutron_authenticate()
            #Create network
            body_create_network = {'network': {'name': self.network_name,'admin_state_up': True}}
            netw = n1.create_network(body=body_create_network)
            net_dict = netw['network']
            self.network_id = net_dict['id']
            #Create subnet and associate
            print "TASK:Creating and adding subnet ........"
            self.name_servers = ['8.8.8.4.4','8.8.8.8']
            body_create_subnet = {'subnets': [{'cidr': '192.168.69.0/24','ip_version': 4, 'network_id': self.network_id, 'name': self.subnet_name, 'dns_nameservers': self.name_servers}]}
            self.subnet = n1.create_subnet(body=body_create_subnet)
           # print('Created subnet %s' % self.subnet['cider'])

            print('INFO:Network %s created' % self.network_name)

         except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred during creating network"
            print lbaas_excep
            sys.exit(1)


    def delete_network(self):
        try:
            n1 = self.neutron_authenticate()
            print "TASK:Deleting Network : %s ........" % self.network_name
            n1.delete_network(self.find_anything('network', self.network_name))
            print "INFO:Successfully Deleted network %s \n" % self.network_name

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting network"
            print lbaas_excep
            sys.exit(1)


    def create_router(self):
        n1 = self.neutron_authenticate()

        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'network':
                    float_network = tenant_id = cfg[section]['float_net']

        #neutron.format = json
        try:

            routers_list = n1.list_routers(retrieve_all=True)
            print "TASK:Creating router %s ........." % self.router_name

            request = {'router': {'name': self.router_name,'admin_state_up': True}}

            #create router
            router = n1.create_router(request)
            self.router_id = router['router']['id']
            body_value = {'port': {
            'admin_state_up': True,
            'device_id': self.router_id,
            'name': self.router_port_name,
            'network_id': self.find_anything('network', self.network_name),
            }}
            #Adding previuosly created subnet to the router
            subnet_body = {}
            subnet_body['subnet_id'] = self.find_anything('subnet', self.subnet_name)
            n1.add_interface_router(self.router_id, subnet_body)

            #Setting external gateway for the router
            self.body_value_egw = {'network_id': self.find_anything('network', float_network)}
            response_set_egw = n1.add_gateway_router(self.router_id,self.body_value_egw)
            #print (response_set_egw)

            print "INFO:Router %s Created successfully \n" %self.router_id

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating router"
            print lbaas_excep
            sys.exit(1)


    def delete_router(self):

        try:
            print "TASK:Deleting router %s ......" %self.router_name
            n1 = self.neutron_authenticate()
            r = n1.remove_gateway_router(self.find_anything('router', self.router_name))
            subnet_body = {}
            subnet_body['subnet_id'] = self.find_anything('subnet', self.subnet_name)
            r2 = n1.remove_interface_router(self.find_anything('router', self.router_name), subnet_body)

            response = n1.delete_router(self.find_anything('router', self.router_name))
            #response2 = n1.delete_port(self.find_anything('port', self.router_port_name))

            print "INFO:Router %s Deleted Successfully" % self.router_name
            print "INFO:Router port %s Deleted Successfully \n" % self.router_port_name

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting router"
            print lbaas_excep
            sys.exit(1)


    def create_health_monitor(self):

         print "TASK:Creating Lbaas Health Monitor ......"

         try:
            nnc = self.neutron_authenticate()

            self.monitor_dic  = {'admin_state_up': True, 'delay': 3, 'max_retries': 3, 'timeout': 3, 'type': 'PING', 'pools': [self.lb_pool_name]}
            m_body = {'health_monitor': {'admin_state_up': True, 'delay': 3, 'max_retries': 3, 'timeout': 5, 'type': 'PING'}}
            h = nnc.create_health_monitor(m_body)
            h = h['health_monitor']

            print "INFO:Successfully created health monitor %s" %h['id']
         except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating health monitor"
            print lbaas_excep
            sys.exit(1)

         return h['id']


    def create_lb_pool(self):

        print "TASK:Creating Lbaas pool %s and assign health monitor........." %self.lb_pool_name
        nnc = self.neutron_authenticate()
        self.snet_id = self.find_anything('subnet', self.subnet_name)
        self.hm_id = self.create_health_monitor()
        pool = {'lb_method': 'ROUND_ROBIN', 'name': self.lb_pool_name,
                        'protocol': 'HTTPS', 'description': "wgamage lbaas pool",
                        'subnet_id': self.snet_id, 'provider': self.lbaas_provider,
                        'admin_state_up': True}
        body = {'pool': pool}
        try:
            p = nnc.create_pool(body)['pool']
            self.created_pool[p['id']] = p
        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating lb pool"
            print lbaas_excep
            sys.exit(1)
        try:
            body = {'health_monitor': {'id': self.hm_id}}
            pool_id = self.find_anything('pool', self.lb_pool_name)
            nnc.associate_health_monitor(pool_id, body)
            print "INFO:Lb pool %s associated with health moniotr %s" % (pool_id, self.hm_id)
            print "INFO:Lbaas pool successfully created \n"
        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred associating lb pool to health monitor"
            print lbaas_excep
            sys.exit(1)


        return p


    def create_lb_members(self, pid):
        self.mport = self.lb_vip_ssl_port
        self.mip = ''
        self.mpid = pid
        try:
            print "TASK:Adding memebers to Lbaas pool......."
            nnc = self.neutron_authenticate()
            self.mip = self.base_ip_address
            for i in range (0, self.number_of_vms):
                mem = {'pool_id': self.mpid, 'protocol_port': self.mport, 'address': self.mip, 'weight': 1, 'admin_state_up': True}
                body = {'member': mem}
                m = nnc.create_member(body)['member']
                print "INFO:Added memeber %s to pool %s" %(self.mip ,self.mpid)
                self.mip = self.increment_ip(self.mip)
                self.created_member[m['id']] = m

            print "INFO:Successfully Added Members to pool"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating lb pool members"
            print lbaas_excep
            sys.exit(1)


    def create_lb_vip(self, pid):
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'network':
                    float_network = tenant_id = cfg[section]['float_net']

        #self.vip_port = self.lb_vip_ssl_port
        self.snet_id = self.find_anything('subnet', self.subnet_name)
        print "TASK:Creating Lbaas vip %s ......." %self.lb_vip_name

        try:
            nnc = self.neutron_authenticate()
            vip = {'protocol': 'HTTPS', 'name': self.lb_vip_name, 'protocol_port': self.lb_vip_ssl_port,
                       'subnet_id': self.snet_id, 'pool_id': pid, 'admin_state_up': True, \
                       'description': "Wgamage vip"}
            body = {'vip': vip}
            v = nnc.create_vip(body)['vip']
            self.created_vip[v['id']] = v
            print "INFO:Successfully created vip"
        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating lb vip"
            print lbaas_excep
            sys.exit(1)
        try:
            #assigning a floating ip to the vip
            fbody = {'floatingip': {'floating_network_id': self.find_anything('network', float_network)}}
            fip = nnc.create_floatingip(fbody)['floatingip']
            if fip['port_id'] != v['port_id']:
                body = {'floatingip': {'port_id': v['port_id']}}
                nnc.update_floatingip(fip['id'], body)
            self.created_fip[fip['id']] = fip

            print "INFO:Successfully assigned floating ip to vip"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred assigning floating ip to lb vip"
            print lbaas_excep
            sys.exit(1)


    def setup_networking(self):
        print "TASK:Setting up basic networking for Lbaas testing ........"
        self.create_network()
        self.create_router()


    def teardown_network(self):
        print "TASK::Tearing down basic networking setup for Lbaas testing ........"
        self.delete_router()
        print "INFO:Waiting 30 Seconds for AVi SE neutron ports to be cleared ......"
        time.sleep(30)
        self.delete_network()


    def setup_lbaas(self):

        print "TASK:Setting up Lbaas service ........"
        #logger.debug('TASK:Setting up Lbaas service .........')
        try:
            p = self.create_lb_pool()
            self.create_lb_members(p['id'])
            self.create_lb_vip(p['id'])

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred setting up lbaas"
            print lbaas_excep
            sys.exit(1)


    def setup_multiple_lbaas(self):

        print "TASK:Setting up multiple Lbaas VIPS and pools ........"
        logging.debug('TASK:Setting up multiple Lbaas VIPS and pools ........')
        scale = 7
        p_name = "Multiple-Pool"
        desc = "lbpool"
        v_name = "Multiple-VIP"
        vip_port = 8080

        nnc = self.neutron_authenticate()
        self.snet_id = self.find_anything('subnet', self.subnet_name)
        self.hm_id = self.create_health_monitor()


        for i in range(1,8):

            pool_name = p_name + i.__str__()
            desc1 = desc + i.__str__()
            vip_name = v_name + i.__str__()


            print "TASK:Creating Lbaas pool %s and assign health monitor........." %pool_name

            pool = {'lb_method': 'ROUND_ROBIN', 'name': pool_name,
                            'protocol': 'HTTPS', 'description': desc1,
                            'subnet_id': self.snet_id, 'provider': self.lbaas_provider,
                            'admin_state_up': True}
            body = {'pool': pool}


            try:
                p = nnc.create_pool(body)['pool']

            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred creating lb pool"
                print lbaas_excep
                sys.exit(1)
            try:
                body = {'health_monitor': {'id': self.hm_id}}
                pool_id = self.find_anything('pool', pool_name)
                nnc.associate_health_monitor(pool_id, body)

                print "INFO:Lb pool %s associated with health moniotr %s" % (p, self.hm_id)
                print "INFO:Lbaas pool successfully created \n"
            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred associating lb pool to health monitor"
                print lbaas_excep
                sys.exit(1)

            time.sleep(5)


            try:
                print "TASK:Adding memebers to Lbaas pool......."

                self.mip = self.base_ip_address
                for i in range (0, self.number_of_vms):
                    mem = {'pool_id': pool_id, 'protocol_port': vip_port, 'address': self.mip, 'weight': 1, 'admin_state_up': True}
                    body = {'member': mem}
                    m = nnc.create_member(body)['member']
                    print "INFO:Added memeber %s to pool %s" %(self.mip ,pool_id)
                    self.mip = self.increment_ip(self.mip)
                    self.created_member[m['id']] = m

                print "INFO:Successfully Added Members to pool"

            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred creating lb pool members"
                print lbaas_excep
                sys.exit(1)

            print "TASK:Creating Lbaas vip %s ......." %vip_name
            try:

                vip = {'protocol': 'HTTPS', 'name': vip_name, 'protocol_port': vip_port,
                           'subnet_id': self.snet_id, 'pool_id': pool_id, 'admin_state_up': True, \
                           'description': "Multiple VIP Test"}
                body = {'vip': vip}
                v = nnc.create_vip(body)['vip']
                self.created_vip[v['id']] = v
                print "INFO:Successfully created vip"
            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred creating lb vip"
                print lbaas_excep
                sys.exit(1)

            time.sleep(10)
            vip_port = vip_port + 1


    def delete_lbaas(self):
    #pools are a list of dictionaries
    # API V2.0 is not supported by lbaas here
    #so methods such with lbaas in it cannot be used

        print "TASK:Deleting existing Lbaas configs ......."
        try:
            nnc = self.neutron_authenticate()
            lb_list = nnc.list_pools()
            lb_vip_list = nnc.list_vips()
            lb_hm = []
            lb_members_list = nnc.list_members()
            #pools are a list of dictionaries


            try:
                for k in lb_vip_list:
                    for l in lb_vip_list[k]:
                            for m,n in l.iteritems():
                                if m == 'name' and l[m] == self.lb_vip_name:
                                    print "INFO:Deleting LB VIP  %s " % l['id']
                                    nnc.delete_vip(l['id'])

            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred deleting lbaas VIP"
                print lbaas_excep
                sys.exit(1)
            try:
                for k in lb_list:
                    for l in lb_list[k]:
                            for m,n in l.iteritems():
                                if m == 'name' and l[m] == self.lb_pool_name:
                                    lb_hm = l['health_monitors']
                                    print "INFO:Deleting LB Pool  %s " % l['id']
                                    nnc.delete_pool(l['id'])
            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred deleting lbaas Pool"
                print lbaas_excep
                sys.exit(1)

            try:
                if lb_hm != []:
                    print "INFO:Deleting Health Monitor %s" %lb_hm[0]
                    nnc.delete_health_monitor(lb_hm[0])
            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred deleting lbaas Health Monitor"
                print lbaas_excep
                sys.exit(1)
            try:
                self.float_delete()
            except Exception as lbaas_excep:
                print "EXCEPTION:Exception Occurred deleting floating IP assigned to VIP"
                print lbaas_excep
                sys.exit(1)

            print "INFO:Successfully Deleted Lbaas pool, memebers, health monitors, vip and assigned floating ip"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting lbaas configs"
            print lbaas_excep
            sys.exit(1)


    def float_delete(self):
        print "TASK:Deleting All unassigned floating Ips ........."
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'keystone':
                    print "INFO:Reading Tenant id from config.yaml %s section" % section
                    tenant_id = cfg[section]['os_tenant_id']

                if section == 'network':
                    float_network = tenant_id = cfg[section]['float_net']

        try:
            nnc = self.neutron_authenticate()

            self.fnet_id =  self.find_anything('network', float_network)
            fips = nnc.list_floatingips(floating_network_id=self.fnet_id, tenant_id= tenant_id)['floatingips']
            for i in fips:
               if i['fixed_ip_address'] is None:
                   nnc.delete_floatingip(i['id'])

            print "INFO:Successfully Deleted unassigned floating ip addresses"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting floating ips"
            print lbaas_excep
            sys.exit(1)


    def send_traffic(self):
        vip_port = ""
        fid = ''
        cmd = ''
        WGET_CMD1 = "wget --server-response --no-check-certificate "
        WGET_CMD2 =  " 2>&1 | awk '/^  HTTP/{print $2}'"
        resp = ""
        int_address = ''
        found = False
        pings = 0
        wait_time = 0


        try:

            nnc = self.neutron_authenticate()
            vips = nnc.list_vips()

            for i in vips['vips']:
                 if i["name"] == self.lb_vip_name:
                    int_address = i["address"]
                    vip_pid = i["port_id"]
                    vip_port = i["protocol_port"]


            fips = nnc.list_floatingips()
            for j in fips['floatingips']:
                if j["fixed_ip_address"] == int_address:
                    fid = j["floating_ip_address"]

            if vip_port == 80:
                cmd = "curl --connect-timeout 5 http://" + fid
                cmd2 = WGET_CMD1 + "http://" + fid + WGET_CMD2
            elif vip_port == 443:
                cmd = "curl -k --connect-timeout 5 https://" + fid
                cmd2 = WGET_CMD1 + "https://" + fid + WGET_CMD2


            while found == False:
                response = os.system("ping -c 1 -w 2 " + fid + "> /dev/null 2>&1")
                if response == 0:
                    print "INFO:VIP %s is up!" %fid
                    found = True
                else:
                     pings +=1
                     time.sleep(30)
                     if pings == 10:
                         print "WARNING:VIP is not up for 5 Min"

            wait_time = pings * 30 / 60
            wait_time = wait_time + 300

            print "INFO:VIP online in %i minutes" %wait_time


            print "TASK:sending traffic with %s ......." % cmd
            for i in range (0, 20):
                os.system(cmd)
                print "\n"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred while sending traffic to vip"
            print lbaas_excep
            sys.exit(1)

    def send_traffic_redirect(self):
        vip_port = ""
        fid = ''
        cmd = ''
        WGET_CMD1 = "wget --server-response --no-check-certificate "
        WGET_CMD2 = " 2>&1 | awk '/^  HTTP/{print $2}'"
        resp = ""
        int_address = ''
        found = False
        pings = 0
        wait_time = 0

        try:

            nnc = self.neutron_authenticate()
            vips = nnc.list_vips()

            for i in vips['vips']:
                if i["name"] == self.lb_vip_name:
                    int_address = i["address"]
                    vip_pid = i["port_id"]
                    vip_port = i["protocol_port"]

            fips = nnc.list_floatingips()
            for j in fips['floatingips']:
                if j["fixed_ip_address"] == int_address:
                    fid = j["floating_ip_address"]

            cmd = "curl -k -L --connect-timeout 5 https://" + fid
            cmd2 = WGET_CMD1 + "http://" + fid + WGET_CMD2


            while found == False:
                response = os.system("ping -c 1 -w 2 " + fid + "> /dev/null 2>&1")
                if response == 0:
                    print "INFO:VIP %s is up!" % fid
                    found = True
                else:
                    pings += 1
                    time.sleep(30)
                    if pings == 10:
                        print "WARNING:VIP is not up for 5 Min"

            wait_time = pings * 30 / 60
            wait_time = wait_time + 300

            print "INFO:VIP online in %i minutes" % wait_time

            print "TASK:sending traffic with -L option to follow redirect %s ......." % cmd
            for i in range(0, 20):
                os.system(cmd)
                print "\n"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred while sending traffic to vip"
            print lbaas_excep
            sys.exit(1)

    def modify_lb_method(self, new_lb_method):
        print "TASK:Changing LB method to %s ......." % new_lb_method
        try:
            nnc = self.neutron_authenticate()
            snet_id = self.find_anything('subnet', self.subnet_name)
            lb_list = nnc.list_pools(tenant_id=self.os_tenant_id, name=self.lb_pool_name,
                        subnet_id=snet_id)['pools']

            for k in lb_list:
               if k['name'] == self.lb_pool_name:
                        print "INFO:Updating LB method of %s to %s" % (self.lb_pool_name, new_lb_method)
                        pool = {'lb_method': new_lb_method}
                        #body = {'pool': pool}
                        body = {'pool': {'lb_method': new_lb_method}}
                        nnc.update_pool(k['id'], body)
            print "INFO:LB Method successfully updated"

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred updating lb method"
            print lbaas_excep
            sys.exit(1)


class Create_Instances(object):
    neutron_network_name = ""
    instance_name = ""
    image_name = ""
    flavor_name = ""
    key_name = ""
    float_net_name = ''
    base_ip_address = ""
    net_id = ''
    number_of_vms = ''

    def __init__(self):
        self.keystone = ksclient.Client(auth_url=env['OS_AUTH_URL'],
                                        username=env['OS_USERNAME'],
                                        password=env['OS_PASSWORD'],
                                        tenant_name=env['OS_TENANT_NAME'],
                                        region_name=env['OS_REGION'])


        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'compute':
                    print "INFO:Reading configs from config.yaml %s section" % section
                    #self.txt = cfg[section]['net_name']
                    self.network_name = cfg[section]['net_name']
                    self.instance_name = cfg[section]['vm_base_name']
                    self.base_ip_address = cfg[section]['vm_base_ip']
                    self.image_name = cfg[section]['image_name']
                    self.flavor_name = cfg[section]['flavor_name']
                    self.key_name = cfg[section]['key_name']
                    self.sec_group_name = cfg[section]['sec_group_name']
                    self.number_of_vms = cfg[section]['number_of_vms']


    def get_nova_credentials_v2(self):
        d = {}
        d['version'] = '2'
        d['username'] = env['OS_USERNAME']
        d['api_key'] = env['OS_PASSWORD']
        d['auth_url'] = env['OS_AUTH_URL']
        d['project_id'] = env['OS_TENANT_NAME']
        return d


    def increment_ip(self, ip):
        ip2int = lambda ipstr: struct.unpack('!I', socket.inet_aton(ipstr))[0]
        x = ip2int(ip)
        x = x + 1
        int2ip = lambda n: socket.inet_ntoa(struct.pack('!I', n))
        return int2ip(x)


    def create_keypair(self):
        credentials = self.get_nova_credentials_v2()
        nova_client = nvclientv20(**credentials)

        print "TASK:Creating Keypair %s ........" % self.key_name
        try:
            keypair = nova_client.keypairs.create(self.key_name)
            print "INFO:Key pair %s created successfully" %self.key_name

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating key pair"
            print lbaas_excep
            sys.exit(1)


    def delete_keypair(self):
        credentials = self.get_nova_credentials_v2()
        nova_client = nvclientv20(**credentials)

        print "TASK:Deleting Keypair %s ......" % self.key_name
        try:
            keypair = nova_client.keypairs.delete(self.key_name)
            print "INFO:Key pair %s deleted successfully" %self.key_name

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting key pair"
            print lbaas_excep
            sys.exit(1)


    def create_sec_group(self):
        self.sec_group_id = ""
        print "TASK:Creating Security Group %s .......\n" % self.sec_group_name
        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)
            sg = nova_client.security_groups.create(name=self.sec_group_name, description="wgamage lbaas testing")


            self.sec_group_id = nova_client.security_groups.find(name=self.sec_group_name)
            # Add rules for ICMP, tcp/80 and tcp/443
            old_sid = str(self.sec_group_id)
            new_sid = old_sid.replace(":", "")

            nova_client.security_group_rules.create(new_sid, ip_protocol="icmp",from_port=-1, to_port=-1)
            nova_client.security_group_rules.create(new_sid, ip_protocol="tcp",from_port=80, to_port=80)
            nova_client.security_group_rules.create(new_sid, ip_protocol="tcp",from_port=443, to_port=443)
            print "INFO:Security Group %s created successfuilly" %self.sec_group_name
        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating security group"
            print lbaas_excep
            sys.exit(1)


    def delete_sec_group(self):
        self.sec_group_id = ""
        print "TASK:Deleting Security Group %s .........\n" % self.sec_group_name
        print "INFO: Sleeping for 30 seconds to let neutron sync with nova"
        try:
            time.sleep(30)
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)
            sgl = nova_client.security_groups.list()
            #this function returns a list of classes
            for i in sgl:
                if i.__getattr__('name') == self.sec_group_name:
                   sgd = nova_client.security_groups.delete(i.__getattr__('id'))
                   print "INFO:Sucessfully deleted security group %s" % i.__getattr__('name')
                   break


        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting security group"
            print lbaas_excep
            sys.exit(1)


    def create_instances(self, net_id):
        self.net_id = net_id
        print "TASK:Creating Instance with network id %s ........." % self.net_id

        self.user_data = """#cloud-config
            password: XYZ
            chpasswd: { expire: False }
            ssh_pwauth: True
            manage-resolv-conf: true
            resolv_conf:
                nameservers:
                    - '8.8.8.8'
                    - '8.8.8.4'
            #package_upgrade: true
            packages:
                - httpd
                - mod_ssl
                - curl
            runcmd:
                - mkdir /etc/httpd/ssl
                - openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/httpd/ssl/apache.key -out /etc/httpd/ssl/apache.crt -subj "/C=US/ST=North Carolina/L=RTP/O=Test-ORG/OU=DEVOPS/CN=openstack.cloud.com"
                - curl -s -o /var/www/html/index.html http://169.254.169.254/latest/meta-data/hostname
                - systemctl enable httpd
                - systemctl start httpd
                #- sync
                #- sync
                #- reboot
            """
        #import pdb
        #pdb.set_trace()

        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)

            self.image = nova_client.images.find(name=self.image_name)
            self.flavor = nova_client.flavors.find(name=self.flavor_name)
            base_name = self.instance_name
            ipa = self.base_ip_address
            sec_grp_name = [self.sec_group_name]
            for i in range (0, self.number_of_vms):
                vm_name = base_name + str(i)
                print "INFO:Creating vm %s" % vm_name
                self.nics = [{'net-id': self.net_id, 'v4-fixed-ip': ipa}]
                instance = nova_client.servers.create(name=vm_name, image=self.image,flavor=self.flavor, key_name=self.key_name, nics=self.nics, security_groups=sec_grp_name, userdata=self.user_data)
                print("INFO:Sleeping for 5s after create command")
                time.sleep(5)
                ipa = self.increment_ip(ipa)
            #print("INFO:List of VMs\n")
            #print(nova_client.servers.list())
            print("INFO:Instance Created successfully \n")

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred creating instances"
            print lbaas_excep
            sys.exit(1)


    def delete_instances(self, vm_name):
        self.server_del = vm_name
        print "TASK:Deleting Instance %s ........" % self.server_del

        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)

            servers_list = nova_client.servers.list()

            server_exists = False

            for s in servers_list:
                if s.name == self.server_del:
                    print("INFO:This server %s exists" % self.server_del)
                    server_exists = True
                    break
            if not server_exists:
                print("INFO:server %s does not exist" % self.server_del)
            else:
                print("TASK:Deleting server..........")
                nova_client.servers.delete(s)
                print("INFO:server %s deleted" % self.server_del)
                print("INFO:Sleeping for 5s after delete command")
                time.sleep(5)

            print("INFO:Instance Deleted successfully \n")

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred deleting instances"
            print lbaas_excep
            sys.exit(1)


    def setup_compute(self, net_id):
        self.net_id = net_id
        print "TASK:Setting up Compute for Lbaas Testing........"
        self.create_keypair()
        self.create_sec_group()
        self.create_instances(self.net_id)


    def teardown_compute(self):
        print "TASK:Tearing down compute setup for Lbaas Testing........"
        try:
            base_name = self.instance_name
            for i in range(0, self.number_of_vms):
                vm_name = base_name + str(i)
                print "TASK:Deleting vm %s ........" % vm_name
                self.delete_instances(vm_name)

            self.delete_keypair()
            self.delete_sec_group()

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred tearing down compute"
            print lbaas_excep
            sys.exit(1)


    def suspend_instances(self):

        print "TASK:Suspend Instance 1...."


        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)

            base_name = self.instance_name
            ipa = self.base_ip_address

            i = 0
            vm_name = base_name + str(i)

            instance = nova_client.servers.find(name=vm_name)
            instance.suspend()

            print("INFO:Instance Suspended successfully \n")

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred suspending instance"
            print lbaas_excep
            sys.exit(1)

    def resume_instances(self):

        print "TASK:Resume Instance 1...."



        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)

            base_name = self.instance_name
            ipa = self.base_ip_address

            i = 0
            vm_name = base_name + str(i)

            instance = nova_client.servers.find(name=vm_name)
            instance.resume()

            print("INFO:Instance Resumed successfully \n")

        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred resuming instance"
            print lbaas_excep
            sys.exit(1)

    def find_existing_compute(self):
        try:
            credentials = self.get_nova_credentials_v2()
            nova_client = nvclientv20(**credentials)

            servers_list = nova_client.servers.list()

            for s in servers_list:
                x = re.search(self.instance_name, s.name)
                #y = x.group(0)

                if x is not None:
                    print("INFO:Found existing servers")
                    return True
                else:
                    return False
                


        except Exception as lbaas_excep:
            print "EXCEPTION:Exception Occurred finding existing compute"
            print str(lbaas_excep)
            sys.exit(1)


    def create_tenant_users(self):
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'keystone+admin':
                    print "INFO:Reading OS Credentials from config.yaml %s section" % section
                    env['OS_TENANT_ID'] = cfg[section]['os_tenant_id']
                    env['OS_TENANT_NAME'] = cfg[section]['os_tenant_name']
                    env['OS_PASSWORD'] = cfg[section]['os_password']
                    env['OS_USERNAME'] = cfg[section]['os_username']
                    env['OS_AUTH_URL'] = cfg[section]['os_auth_url']
                    env['OS_REGION'] = cfg[section]['os_region']

        self.keystone_admin = ksclient.Client(auth_url=env['OS_AUTH_URL'],
                                        username=env['OS_USERNAME'],
                                        password=env['OS_PASSWORD'],
                                        tenant_name=env['OS_TENANT_NAME'],
                                        region_name=env['OS_REGION'])


        self.keystone_admin.tenants.create(tenant_name="openstackDemo",description="Default Tenant", enabled=True)
        tenants = self.keystone_admin.tenants.list()
        my_tenant = [x for x in tenants if x.name=='openstackDemo'][0]
        my_user = self.keystone_admin.users.create(name="adminUser", password="secretword",tenant_id=my_tenant.id)

        role = self.keystone_admin.roles.create('admin')

        self.keystone_admin.roles.add_user_role(my_user, role, my_tenant)




if __name__=='__main__':

    import logging

    new_lb_method = ''
    avi_vip = ''
    avi_user = ''
    avi_passwd = ''
    avi_vip_timeout = 0
    log_level ="logging.DEBUG"
    log_file_name = "os-lbaas-test-log.txt"



    with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            for section in cfg:
                if section == 'keystone':
                    print "INFO:Reading OS Credentials from config.yaml %s section" % section
                    env['OS_TENANT_ID'] = cfg[section]['os_tenant_id']
                    env['OS_TENANT_NAME'] = cfg[section]['os_tenant_name']
                    env['OS_PASSWORD'] = cfg[section]['os_password']
                    env['OS_USERNAME'] = cfg[section]['os_username']
                    env['OS_AUTH_URL'] = cfg[section]['os_auth_url']
                    env['OS_REGION'] = cfg[section]['os_region']
                if section == 'avi':
                    avi_vip = cfg[section]['avi_controller_vip']
                    avi_user = cfg[section]['avi_controller_user']
                    avi_passwd = cfg[section]['avi_controller_passwd']
                    avi_vip_timeout = cfg[section]['vip_timeout']
                if section == 'general':
                    log_level = cfg[section]['log_level']
                    log_file_name = cfg[section]['log_file_name']


    logging.basicConfig(filename=log_file_name, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info('+++++Staring running os-lbaas-test.py+++++')



    parser = argparse.ArgumentParser(
    	description='AVI OpenStack LBaaS Test Tool')
    parser.add_argument('-s', '--setup', action="store_true", help="Setup compute and network for lbaas testing")
    parser.add_argument('-c', '--create_lbaas', action="store_true", help="Start creating lbaas service")
    parser.add_argument('-cm', '--create_multiple_lbaas', action="store_true", help="Start creating multiple lbaas service")
    parser.add_argument('-d', '--delete_lbaas', action="store_true", help="Delete lbaas configs only")
    parser.add_argument('-dm', '--delete_multiple_lbaas', action="store_true", help="Delete multiple lbaas configs")
    parser.add_argument('-u', '--cleanup', action="store_true", help="Cleanup compute and network created for lbaas testing")
    parser.add_argument('-t', '--send_traffic', action="store_true", help="Send traffic to the VIP")
    parser.add_argument('-tr', '--send_traffic_redirect', action="store_true", help="Send traffic to the VIP to test HTTP redirect")
    parser.add_argument('-r', '--runner', action="store_true", help="run all tests")
    parser.add_argument('-synth', '--synth', action="store_true", help="run synthetic tests")
    parser.add_argument('-ml', '--modify_lb_method_lc', action="store_true", help="Modify LB method to LEAST_CONNECTIONS ")
    parser.add_argument('-ms', '--modify_lb_method_si', action="store_true", help="Modify LB method to SOURCE_IP ")
    parser.add_argument('-mr', '--modify_lb_method_rr', action="store_true", help="Modify LB method to ROUND_ROBIN ")
    parser.add_argument('-ls', '--list_configs', action="store_true", help="List All Lbaas and neutron configs ")
    parser.add_argument('-fn', '--clean_neutron', action="store_true", help="Clean neutron subnet, network and sec group ")
    parser.add_argument('-avi', '--check_avi', action="store_true", help="Check AVI controller health and configs ")
    parser.add_argument('-ss', '--suspend_vm', action="store_true", help="Suspend instance 1 ")
    parser.add_argument('-rs', '--resume_vm', action="store_true", help="Resume instance 1 ")
    #parser.add_argument("new_lb_method", help="New LB method: ROUND_ROBIN,LEAST_CONNECTIONS,SOURCE_IP")
    #parser.add_argument("--create_lbaas")
    args = parser.parse_args()
    if args.setup:
             print "You entered : setup"
             print "++++++ Creating Network +++++++\n"
             cn = Create_Networking()
             cn.setup_networking()
             nid = cn.find_anything('network', cn.network_name)
             print "++++++ Creating Compute +++++++\n"
             ni = Create_Instances()
             ni.setup_compute(nid)
             print "++++++ Completed creating Network and compute +++++++\n"

    elif args.create_lbaas:
            print "You entered : Create_lbaas"
            print "++++++ Creating Lbaas pool, members and vip ++++++\n"
            cn = Create_Networking()
            cn.setup_lbaas()
            print "++++++ Completed creating Lbaas services ++++++\n"

    elif args.create_multiple_lbaas:
            print "You entered : Create_multiple_lbaas"
            print "++++++ Creating multiple Lbaas pools, members and vips ++++++\n"
            cn = Create_Networking()
            cn.setup_multiple_lbaas()
            print "++++++ Completed creating multiple Lbaas services ++++++\n"

    elif args.delete_lbaas:
            print "you have entered: delete lbaas"
            print "++++++ Deleting Lbaas pool, members and vip ++++++\n"
            cn = Create_Networking()
            cn.delete_lbaas()
            print "++++++ Completely deleted Lbaas services ++++++\n"

    elif args.cleanup:
            print "you have entered: cleanup"
            print "++++++ Deleting Lbaas configs, instances and networks ++++++\n"
            cn = Create_Networking()
            ni = Create_Instances()
            cn.delete_lbaas()
            ni.teardown_compute()
            cn.teardown_network()
            print "++++++ Completely deleted All configurations ++++++\n"

    elif args.send_traffic:
            print "you have entered: send traffic to vip"
            print "INFO:Waiting for servers to install httpd and vip to come up ....."
            print "++++++ Sending traffic to VIP ++++++\n"
            cn = Create_Networking()
            cn.send_traffic()
            print "++++++ Sending traffic to VIP completed ++++++\n"

    elif args.send_traffic_redirect:
        print "you have entered: send traffic to vip to test HTTP redirect"
        print "INFO:Waiting for servers to install httpd and vip to come up ....."
        print "++++++ Sending traffic to VIP with -L option ++++++\n"
        cn = Create_Networking()
        cn.send_traffic_redirect()
        print "++++++ Sending traffic to VIP completed ++++++\n"


    elif args.modify_lb_method_lc:
            print "you have entered: Modify LB Method to LEAST CONNECTIONS"
            print "++++++ Modifying LB method ++++++\n"
            cn = Create_Networking()
            cn.modify_lb_method("LEAST_CONNECTIONS")
            print "++++++ Modifying LB method completed ++++++\n"

    elif args.modify_lb_method_si:
            print "you have entered: Modify LB Method to SOURCE_IP"
            print "++++++ Modifying LB method ++++++\n"
            cn = Create_Networking()
            cn.modify_lb_method("SOURCE_IP")
            print "++++++ Modifying LB method completed ++++++\n"

    elif args.modify_lb_method_rr:
            print "you have entered: Modify LB Method to ROUND_ROBIN"
            print "++++++ Modifying LB method ++++++\n"
            cn = Create_Networking()
            cn.modify_lb_method("ROUND_ROBIN")
            print "++++++ Modifying LB method completed ++++++\n"

    elif args.suspend_vm:
            print "you have entered: Suspend VM"
            print "++++++ Suspend VM 1++++++\n"
            ni = Create_Instances()
            ni.suspend_instances()

    elif args.resume_vm:
            print "you have entered: Resume VM 1"
            print "++++++ Resume VM 1++++++\n"
            ni = Create_Instances()
            ni.resume_instances()


    elif args.list_configs:
            print "you have entered: List all configs"
            print "++++++ Listing network, instance and lbaas configurations ++++++\n"
            call(['bash', 'show-lb.sh'])

    elif args.clean_neutron:
            print "you have entered: Clean neutron configs"
            print "++++++ Force delete neutrom secgroup, subnet and network configurations ++++++\n"
            call(['bash', 'cleanup_neutron.sh'])

    elif args.delete_multiple_lbaas:
            print "you have entered: Clean multiple vips"
            print "++++++ Delete multiple vips, pools created with -cm option ++++++\n"
            call(['bash', 'cleanup_multi.sh'])

    elif args.check_avi:
            print "you have entered: Check AVI Health and configs"
            print "+++++++ Checking AVI controller cluster status and configuration +++++++\n"
            avi_session = avicontrollercheck._create_session(avi_vip, avi_user, avi_passwd)
            avicontrollercheck._check_cluster_health(avi_session, avi_vip)
            avicontrollercheck._check_configs(avi_session, avi_vip)
            avicontrollercheck._check_tenant_configs(avi_session, avi_vip)


    elif args.runner:
            print "you have entered: Run all tests"
            print "++++++ Checking for Any Existing Lbaas configs, instances and networks ++++++\n"
            cn = Create_Networking()
            ni = Create_Instances()
            if ni.find_existing_compute() == True:
                print "++++++ Deleting Any Existing Lbaas configs, instances and networks ++++++\n"
                cn.delete_lbaas()
                ni.teardown_compute()
                cn.teardown_network()

            print "++++++ Running all tests ++++++\n"
            print "++++++ Creating Network +++++++\n"
            #cn = Create_Networking()
            cn.setup_networking()
            nid = cn.find_anything('network', cn.network_name)
            time.sleep(5)
            print "++++++ Creating Compute +++++++\n"
            #ni = Create_Instances()
            ni.setup_compute(nid)
            print "++++++ Completed creating Network and compute +++++++\n"
            time.sleep(5)

            print "++++++ Creating Lbaas pool, members and vip ++++++\n"
            cn.setup_lbaas()
            print "++++++ Completed creating Lbaas services ++++++\n"
            print "++++++ Listing network, instance and lbaas configurations ++++++\n"
            call(['bash', 'show-lb.sh'])

            print "INFO:Waiting %i minutes for servers to be up and install httpd" %avi_vip_timeout
            time.sleep(avi_vip_timeout)

            print "++++++ Sending traffic to VIP ++++++\n"
            cn.send_traffic()

            print "++++++ Taking instance 1 out of pool ++++++\n"
            ni.suspend_instances()
            print "INFO:Waiting 30 seconds for servers to be suspended"
            time.sleep(30)


            print "++++++ Sending traffic to VIP ++++++\n"
            cn.send_traffic()

            print "++++++ Adding insatnce 1 back in to the pool ++++++\n"
            ni.resume_instances()
            print "INFO:Waiting 30 seconds for servers to be up"
            time.sleep(30)


            print "++++++ Sending traffic to VIP ++++++\n"
            cn.send_traffic()

            print "++++++ Modifying LB method to LEAST CONNS++++++\n"
            cn.modify_lb_method("LEAST_CONNECTIONS")

            print "++++++ Sending traffic to VIP ++++++\n"
            cn.send_traffic()
            time.sleep(10)

            print "++++++ Modifying LB method ++++++\n"
            cn.modify_lb_method("SOURCE_IP")
            print "++++++ Sending traffic to VIP ++++++\n"
            cn.send_traffic()
            time.sleep(10)

            print "++++++ Deleting Lbaas configs, instances and networks ++++++\n"
            cn = Create_Networking()
            ni = Create_Instances()
            cn.delete_lbaas()
            ni.teardown_compute()
            cn.teardown_network()

            print "++++++ Listing network, instance and lbaas configurations ++++++\n"
            call(['bash', 'show-lb.sh'])

            print "++++++ Test run completed ++++++\n"


    elif args.synth:
            print "you have entered: Run synthatic tests"
            cn = Create_Networking()
            ni = Create_Instances()
            while True:

                print "++++++ Creating Lbaas pool, members and vip ++++++\n"
                cn.setup_lbaas()
                print "++++++ Completed creating Lbaas services ++++++\n"
                print "++++++ Listing network, instance and lbaas configurations ++++++\n"
                call(['bash', 'show-lb.sh'])

                print "INFO:Waiting %i minutes for servers to be up and install httpd" %avi_vip_timeout
                time.sleep(avi_vip_timeout)

                print "++++++ Sending traffic to VIP ++++++\n"
                cn.send_traffic()

                print "++++++ Deleting Lbaas configs ++++++\n"
                cn.delete_lbaas()

                print "++++++ Listing network, instance and lbaas configurations ++++++\n"
                call(['bash', 'show-lb.sh'])
                print "INFO:Waiting 10 minutes between runs\n"
                time.sleep(600)

    logging.info('+++++Running os-lbaas-test.py Completed+++++')









