FROM centos:7

LABEL maintainer="rmendes@redhat.com"

RUN yum install git epel-release -y && \
    yum install npm libxml2-devel libxslt-devel openssl-devel python-devel python-pip gcc gcc-c++ expect -y && \  
    pip install --upgrade pip setuptools==44.0 && \
    pip install gitpython && \
    mkdir /home/w3af

WORKDIR /home/w3af

RUN git clone https://github.com/andresriancho/w3af.git && \
    chmod +x w3af/w3af_console && \    
    w3af/./w3af_console ; true && \
    sed 's/sudo //g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/yum/yum -y/g' -i /tmp/w3af_dependency_install.sh && \
    sed 's/pip install/pip install /g' -i /tmp/w3af_dependency_install.sh && \
    umask 022 && \
    /tmp/w3af_dependency_install.sh && \
    echo "#/bin/bash /n npm install -g retire@2.0.3 /n npm update -g retire" >> /tmp/node-normalization.sh && \
    chmod +x /tmp/node-normalization.sh && \
    /tmp/node-normalization.sh

RUN chmod 775 /home/w3af && \ 
    chown -R 1001 /home/w3af && \
    chmod -R "g+rwX" /home/w3af && \
    chown -R 1001:root /home/w3af 

USER 1001

CMD tail -f /dev/null
