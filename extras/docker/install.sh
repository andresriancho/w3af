#!/bin/bash
export LC_ALL=C
install='apt-get install -y --no-install-recommends'

# Remove warnings regarding 'no frontend dialog'
echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Install python
$install python-pip build-essential libxslt1-dev libxml2-dev libsqlite3-dev \
           libyaml-dev openssh-server python-dev git python-lxml wget libssl-dev \
           xdot python-gtk2 python-gtksourceview2 ubuntu-artwork dmz-cursor-theme \
           ca-certificates libffi-dev libjpeg-dev libjpeg8-dev

# Get and install pip
pip install --upgrade pip

cd /home/app/
git clone --depth 1 https://github.com/andresriancho/w3af.git w3af
cd /home/app/w3af

set +e
./w3af_console
set -e

# Change the install script to add the -y and not require input
sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh
sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh

chmod +x /tmp/w3af_dependency_install.sh
/tmp/w3af_dependency_install.sh

# Compile the py files into pyc in order to speed-up w3af's start
python -m compileall .
chown -R app /home/app/w3af

# accept terms [because first run will get stuck otherwise]
if [ -f /home/app/.w3af/startup.conf ]
then
    if ! grep -i "^accepted-disclaimer = true$" /home/app/.w3af/startup.conf
    then
        echo "accepted-disclaimer = true" >> /home/app/.w3af/startup.conf
    fi
else
    if [ ! -d /home/app/.w3af ]
    then
        mkdir /home/app/.w3af
    fi
    echo "[STARTUP_CONFIG]" >> /home/app/.w3af/startup.conf
    echo "auto-update = true" >> /home/app/.w3af/startup.conf
    echo "frequency = D" >> /home/app/.w3af/startup.conf
    echo "accepted-disclaimer = true" >> /home/app/.w3af/startup.conf
    chown -R app.app /home/app/.w3af
fi

# clean
rm -rf /tmp/pip-build-root /tmp/w3af_dependency_install.sh
