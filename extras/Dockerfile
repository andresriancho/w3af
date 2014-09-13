FROM ubuntu:12.04
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

# Get ssh package ready
RUN apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo 'root:w3af' | chpasswd

# Add the w3af user
# TODO - actually use the w3af user instead of running everything as root
RUN useradd w3af

# Install basic requirements, python-lxml because it doesn't compile correctly from pip
RUN apt-get install -y python-dev git python-lxml wget libssl-dev

# GUI deps
RUN apt-get install xdot python-gtk2 python-gtksourceview2 ubuntu-artwork dmz-cursor-theme ca-certificates -y

# Get and install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# Install w3af
RUN git clone --depth 1 https://github.com/andresriancho/w3af.git
WORKDIR /home/w3af/w3af
RUN ./w3af_console ; true

# Change the install script to add the -y and not require input
RUN sed 's/sudo apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/sudo pip/pip/g' -i /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN cat /tmp/w3af_dependency_install.sh
RUN /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN ./w3af_gui ; true
RUN sed 's/sudo apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/sudo pip/pip/g' -i /tmp/w3af_dependency_install.sh
RUN /tmp/w3af_dependency_install.sh

# Compile the py files into pyc in order to speed-up w3af's start
RUN python -m compileall .

# Cleanup to make the image smaller
RUN rm /tmp/w3af_dependency_install.sh
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
RUN rm -rf /tmp/pip-build-root

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
