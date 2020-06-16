# w3af.org
# https://github.com/andresriancho/w3af/tree/master/extras

FROM ubuntu:18.04
MAINTAINER Andres Riancho <andres.riancho@gmail.com>

# Initial setup
RUN mkdir /home/w3af
WORKDIR /home/w3af
ENV HOME /home/w3af
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LOGNAME w3af
# Squash errors about "Falling back to ..." during package installation
ENV TERM linux
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Update before installing any package
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

# Install basic and GUI requirements, python-lxml because it doesn't compile correctly from pip
RUN apt-get install -y python-pip build-essential libxslt1-dev libxml2-dev libsqlite3-dev \
                       libyaml-dev openssh-server python-dev git python-lxml wget  \
                       xdot python-gtk2 python-gtksourceview2 ubuntu-artwork dmz-cursor-theme \
                       ca-certificates libffi-dev zlib1g-dev nodejs nodejs-dev libssl1.0-dev \
                       node-gyp npm

# Add the w3af user
# TODO - actually use the w3af user instead of running everything as root
RUN useradd w3af

# Get ssh package ready
RUN mkdir /var/run/sshd
RUN echo 'root:w3af' | chpasswd
RUN mkdir /home/w3af/.ssh/
RUN echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDjXxcHjyVkwHT+dSYwS3vxhQxZAit6uZAFhuzA/dQ2vFu6jmPk1ewMGIYVO5D7xV3fo7/RXeCARzqHl6drw18gaxDoBG3ERI6LxVspIQYjDt5Vsqd1Lv++Jzyp/wkXDdAdioLTJyOerw7SOmznxqDj1QMPCQni4yhrE+pYH4XKxNx5SwxZTPgQWnQS7dasY23bv55OPgztI6KJzZidMEzzJVKBXHy1Ru/jjhmWBghiXYU5RBDLDYyT8gAoWedYgzVDmMZelLR6Y6ggNLOtMGiGYfPWDUz9Z6iDAUsOQBtCJy8Sj8RwSQNpmOgSzBanqnhed14hLwdYhnKWcPNMry71 w3af@w3af-docker.org' > /home/w3af/.ssh/w3af-docker.pub
RUN mkdir -p /root/.ssh/
RUN cat /home/w3af/.ssh/w3af-docker.pub >> /root/.ssh/authorized_keys

# Get and install pip
RUN pip install --index-url=https://pypi.python.org/simple/ --upgrade pip
#
# We install some pip packages before adding the code in order to better leverage
# the docker cache
#
# Leave one library without install, so w3af_dependency_install is actually
# created and we can run the next commands without if statements
#
#tblib==0.2.0
#
RUN pip install setuptools-git>=1.1 pyClamd==0.4.0 PyGithub==1.21.0 GitPython==2.1.15 \
        pybloomfiltermmap==0.3.14 esmre==0.3.1 phply==0.9.1 nltk==3.0.1 chardet==3.0.4 \
        pdfminer==20140328 futures==3.2.0 pyOpenSSL==18.0.0 scapy==2.4.0 guess-language==0.2 \
        cluster==1.1.1b3 msgpack-python==0.5.6 python-ntlm==1.0.1 halberd==0.2.4 \
        darts.util.lru==0.5 ndg-httpsclient==0.4.0 pyasn1==0.4.2 Jinja2==2.7.3 vulndb==0.1.3 \
        markdown==2.6.1 psutil==2.2.1 Tornado==4.5 mitmproxy==0.13 ruamel.ordereddict==0.4.8 \
        Flask==0.10.1 PyYAML==3.12 ds-store==1.1.2 termcolor==1.1.0 tldextract==1.7.2 pebble==4.3.8 \
        acora==2.1 diff-match-patch==20121119 bravado-core==5.0.2 lz4==1.1.0 vulners==1.3.0

# Install w3af
ADD . /home/w3af/w3af
WORKDIR /home/w3af/w3af
RUN ./w3af_console ; true

# Change the install script to add the -y and not require input
RUN sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN ./w3af_gui ; true
RUN sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh
RUN /tmp/w3af_dependency_install.sh

# Compile the py files into pyc in order to speed-up w3af's start
RUN python -m compileall -q .

# Cleanup to make the image smaller
RUN rm /tmp/w3af_dependency_install.sh
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
RUN rm -rf /tmp/pip-build-root

EXPOSE 22 44444

CMD ["/usr/sbin/sshd", "-D"]
