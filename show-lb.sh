#! /bin/sh
printf "++++++++ Networks +++++++\n"
neutron net-list
printf "+++++++++subnets+++++++++\n"
neutron subnet-list
printf "+++++++routers+++++++++++\n"
neutron router-list
printf "++++++++Lbaas HM+++++++++\n"
neutron lb-healthmonitor-list 
printf "+++++++Lb memebers+++++++\n"
neutron lb-member-list
printf "+++++++++++ LB vips++++++\n" 
neutron lb-vip-list
printf "+++++++++LB Pools++++++++\n"
neutron lb-pool-list
printf "++++++floating ips+++++++\n"
neutron floatingip-list
printf "+++++++instances+++++++++\n"
nova list
printf "+++++security-groups++++\n"
neutron security-group-list
printf "+++++Keypairs++++\n"
nova keypair-list
