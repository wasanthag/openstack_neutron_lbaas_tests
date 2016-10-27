#! /bin/sh
BASE_NAME=Multiple-
printf "++++++++ Deleting VIPS and Pools created for multi vip test +++++++\n"
for i in $(neutron lb-vip-list | grep Multiple-VIP | awk '{print $2}') ; do neutron lb-vip-delete $i ; done
for i in $(neutron lb-pool-list | grep Multiple | awk '{print $2}') ; do neutron lb-pool-delete $i ; done

