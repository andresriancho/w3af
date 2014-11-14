# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
apt-get update -y
# Install basic requirements, python-lxml because it doesn't compile correctly from pip
apt-get install -y python-dev git python-lxml
# Get and install pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

git clone --depth 1 https://github.com/andresriancho/w3af.git
cd w3af
./w3af_console
# Change the install script to add the -y and not require input
sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
# Run the dependency installer
/tmp/w3af_dependency_install.sh
# Remove the root-owned file
rm /tmp/w3af_dependency_install.sh
echo "Done!"
echo "To use w3af_console type:"
echo "    vagrant ssh"
echo "    ./w3af/w3af_console"
SCRIPT


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "precise64"
  # URL for Ubuntu Server 12.04 LTS (Precise Pangolin) daily
  config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box"
  config.vm.hostname = "w3af"

  # Run the above script
  config.vm.provision "shell", inline: $script

end
