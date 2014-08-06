FROM ubuntu:precise
MAINTAINER Andres Riancho <andres.riancho@gmail.com>

# Initial setup
RUN mkdir /home/w3af
WORKDIR /home/w3af
ENV HOME /home/w3af
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LOGNAME w3af
ENV TERM xterm

# Update before installing any package
RUN apt-get update -y

# Install basic requirements, python-lxml because it doesn't compile correctly from pip
RUN apt-get install -y python-dev git python-lxml wget

# Get and install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# Install w3af
RUN git clone --depth 1 https://github.com/andresriancho/w3af.git
RUN ./w3af_console ; true

WORKDIR /home/w3af/w3af

# Change the install script to add the -y and not require input
RUN sed 's/sudo apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh
RUN sed 's/sudo pip/pip/g' -i /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN cat /tmp/w3af_dependency_install.sh
RUN /tmp/w3af_dependency_install.sh

# Cleanup to make the image smaller
RUN rm /tmp/w3af_dependency_install.sh
RUN rm -rf /tmp/pip-build-root
RUN apt-get clean

ENTRYPOINT ["./w3af_console"]