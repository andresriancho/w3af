#
# w3af.org
# https://github.com/andresriancho/w3af/tree/master/extras
#
FROM ubuntu:16.04

#
# Andres Riancho
#
LABEL maintainer="andres.riancho@gmail.com"

#
# Initial setup
#
WORKDIR /home/w3af
ENV HOME=/home/w3af \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LOGNAME=w3af \
    LC_ALL=C \
    #
    # Squash errors about "Falling back to ..." during package installation
    #
    TERM=linux

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    #
    # Update before installing any package
    #
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    #
    # Install basic and GUI requirements, python-lxml because it doesn't compile correctly from pip
    #
    apt-get install -y python-pip build-essential libxslt1-dev libxml2-dev libsqlite3-dev \
                       libyaml-dev openssh-server python-dev git python-lxml wget libssl-dev \
                       xdot python-gtk2 python-gtksourceview2 ubuntu-artwork dmz-cursor-theme \
                       ca-certificates libffi-dev && \
    #
    # Add the w3af user
    # TODO - actually use the w3af user instead of running everything as root
    #
    useradd w3af && \
    #
    # Get ssh package ready
    #
    mkdir /var/run/sshd && \
    echo 'root:w3af' | chpasswd && \
    mkdir /home/w3af/.ssh/ && \
    echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDjXxcHjyVkwHT+dSYwS3vxhQxZAit6uZAFhuzA/dQ2vFu6jmPk1ewMGIYVO5D7xV3fo7/RXeCARzqHl6drw18gaxDoBG3ERI6LxVspIQYjDt5Vsqd1Lv++Jzyp/wkXDdAdioLTJyOerw7SOmznxqDj1QMPCQni4yhrE+pYH4XKxNx5SwxZTPgQWnQS7dasY23bv55OPgztI6KJzZidMEzzJVKBXHy1Ru/jjhmWBghiXYU5RBDLDYyT8gAoWedYgzVDmMZelLR6Y6ggNLOtMGiGYfPWDUz9Z6iDAUsOQBtCJy8Sj8RwSQNpmOgSzBanqnhed14hLwdYhnKWcPNMry71 w3af@w3af-docker.org' > /home/w3af/.ssh/w3af-docker.pub && \
    mkdir -p /root/.ssh/ && \
    cat /home/w3af/.ssh/w3af-docker.pub >> /root/.ssh/authorized_keys && \
    #
    # Get and install pip
    #
    pip install --upgrade pip && \
    #
    # We install some pip packages before adding the code in order to better leverage
    # the docker cache
    #
    # Leave one library without install, so w3af_dependency_install is actually
    # created and we can run the next commands without if statements
    #
    # tblib==0.2.0
    #
    pip install chardet==3.0.4 cluster==1.1.1b3 \
                darts.util.lru==0.5 \
                esmre==0.3.1 \
                Flask==0.10.1 futures==2.1.5 \
                GitPython==2.1.3 guess-language==0.2 \
                halberd==0.2.4 \
                Jinja2==2.7.3 \
                lxml==3.4.4 \
                markdown==2.6.1 mitmproxy==0.13 msgpack-python==0.4.4 ndg-httpsclient==0.3.3 \
                nltk==3.0.1 \
                PyGithub==1.21.0 PyYAML==3.12 pdfminer==20140328 pebble==4.3.2 phply==0.9.1 psutil==2.2.1 \
                  pyClamd==0.4.0 pyOpenSSL==16.2.0 pyasn1==0.2.3 pybloomfiltermmap==0.3.14 python-ntlm==1.0.1 \
                ruamel.ordereddict==0.4.8 \
                scapy-real==2.2.0-dev \
                termcolor==1.1.0 tldextract==1.7.2 \
                vulndb==0.0.19

#
# Install w3af
#
ADD . /home/w3af/w3af
WORKDIR /home/w3af/w3af
RUN ./w3af_console ; true && \
    #
    # Change the install script to add the -y and not require input
    #
    sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh && \
    #
    # Run the dependency installer
    #
    /tmp/w3af_dependency_install.sh && \
    #
    # Run the dependency installer
    #
    ./w3af_gui ; true && \
    sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh && \
    /tmp/w3af_dependency_install.sh && \
    #
    # Compile the py files into pyc in order to speed-up w3af's start
    #
    python -m compileall -q . && \
    #
    # Cleanup to make the image smaller
    #
    rm /tmp/w3af_dependency_install.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/pip-build-root

EXPOSE 22 44444

CMD ["/usr/sbin/sshd", "-D"]
