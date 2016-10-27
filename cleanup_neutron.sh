#! /bin/sh
BASE_NAME=lbaas-vm
printf "++++++++ Deleting routers +++++++\n"
for i in $(neutron router-list | grep ${BASE_NAME}-router1 | awk '{print $2}') ; do neutron router-gateway-clear $i ; done
x=`neutron router-list | grep ${BASE_NAME}-router1 | awk '{print $2}'`
y=`neutron router-port-list ${BASE_NAME}-router1 | grep 192.168.69 |awk '{print $2}'`
z=`neutron subnet-list | grep ${BASE_NAME}-snet1 |awk '{print $2}'`
neutron router-interface-delete $x $z
for i in $(neutron router-list | grep ${BASE_NAME}-router1 | awk '{print $2}') ; do neutron router-delete $i ; done
printf "++++++++ Deleting subnet +++++++\n"
#neutron subnet-delete ${BASE_NAME}-snet1
for i in $(neutron subnet-list | grep ${BASE_NAME}-snet1 | awk '{print $2}') ; do neutron subnet-delete $i ; done
printf "++++++++ Deleting network +++++++\n"
#neutron net-delete ${BASE_NAME}-net1
for i in $(neutron net-list | grep ${BASE_NAME}-net1 | awk '{print $2}') ; do neutron net-delete $i ; done
printf "++++++++ Deleting security group +++++++\n"
neutron security-group-delete ${BASE_NAME}-sg
