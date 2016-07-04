# w3af.org
# https://github.com/andresriancho/w3af/tree/master/extras

FROM ubuntu:14.04
MAINTAINER Andres Riancho <andres.riancho@gmail.com>

ADD . /w3af
RUN apt-get update && apt-get upgrade -y && \
    /bin/bash /w3af/add_user.sh && \
    /bin/bash /w3af/install.sh && \
    /bin/bash /w3af/cleanup.sh

USER app
ENV PATH /home/app/w3af:$PATH 
WORKDIR /home/app

CMD["w3af_api","w3af_console","w3af_gui"]

EXPOSE 5000,44449,44444

# Ports
#
# 5000  => API
# 44449 => RFI Plugin
# 44444 => ?
