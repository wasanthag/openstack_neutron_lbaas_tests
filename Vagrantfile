# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

service_name = 'avi-lbaas-testing'

$python_os_setup = <<SCRIPT
# Install packages we need
apt-get update
apt-get install -y python-pip git git-review python python-dev python-virtualenv curl
pip install --upgrade pip
pip install python-novaclient==3.2.0
pip install python-neutronclient==4.0.0
pip install python-keystoneclient==2.0.0
pip install pyopenssl ndg-httpsclient pyasn1
pip install PyYAML requests simplejson
sleep 30
# uncomment following lines if you want to run the scripts automatically with vagrant
# make sure the files are in ansible/roles/lbaas-testing/files or similar locally
#cd /vagrant/ansible/roles/lbaas-testing/files/ ; python os-lbaas-test.py -r
#sleep 10
#cd /vagrant/ansible/roles/lbaas-testing/files/ ; python os-lbaas-test.py -avi
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.define "#{service_name}" do |t|
  end
  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "#{service_name}"
  config.vm.provision "shell", inline: $python_os_setup
end
