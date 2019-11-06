FROM centos:latest

LABEL maintainer="rmendes@redhat.com"

USER root


RUN yum install git epel-release -y && \
    yum install npm libxml2-devel libxslt-devel openssl-devel python-devel python-pip gcc gcc-c++ expect -y && \
    pip install --upgrade pip setuptools 

RUN mkdir /home/w3af

WORKDIR /home/w3af

RUN git clone https://github.com/andresriancho/w3af.git && \
    chmod +x w3af/w3af_console && \    
    w3af/./w3af_console ; true && \
    sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/yum/yum -y/g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/pip install/pip install --upgrade/g' -i /tmp/w3af_dependency_install.sh && \
    /tmp/w3af_dependency_install.sh 


CMD tail -f /dev/null








