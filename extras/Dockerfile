FROM ubuntu:precise
MAINTAINER Andres Riancho <andres.riancho@gmail.com>

RUN apt-get update -y

# Install basic requirements, python-lxml because it doesn't compile correctly from pip
RUN apt-get install -y python-dev git python-lxml wget

# Get and install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# Install w3af
RUN git clone --depth 1 https://github.com/andresriancho/w3af.git
RUN cd w3af && ./w3af_console

# Change the install script to add the -y and not require input
RUN sed 's/apt-get/apt-get -y/g' -i /tmp/w3af_dependency_install.sh

# Run the dependency installer
RUN /tmp/w3af_dependency_install.sh
RUN rm /tmp/w3af_dependency_install.sh

CMD ["w3af/w3af_console"]