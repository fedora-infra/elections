# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/23/Cloud/x86_64/Images/Fedora-Cloud-Base-Vagrant-23-20151030.x86_64.vagrant-libvirt.box"
  config.vm.box = "f23-cloud-libvirt"
  config.vm.network "forwarded_port", guest: 5000, host: 5002
  config.vm.synced_folder ".", "/vagrant", type: "sshfs"
  config.vm.provision "shell", inline: "dnf -y install python redhat-rpm-config python-devel python-pip rpl"
  config.vm.provision "shell", inline: "pushd /vagrant/; pip install -r requirements.txt"
  config.vm.provision "shell", inline: "pushd /vagrant/; python createdb.py", privileged: false
end
