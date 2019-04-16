FROM ubuntu:bionic

RUN apt-get update && \
    apt-get install -y wget software-properties-common && \
    echo "deb https://deb.nodesource.com/node_10.x bionic main" | tee /etc/apt/sources.list.d/nodesource.list && \
    wget -q -O- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
    apt-get update && \
    apt-get install -y nodejs

ADD . /tmp/code/

RUN cd /tmp/code && \
    npm install && \
    ./node_modules/.bin/grunt

FROM ubuntu:bionic

ADD . /tmp/code/

COPY --from=0 /tmp/code/styles/dist/style.css /tmp/code/styles/dist/style.css

RUN apt-get update && \
    apt-get install -y python3-pip sudo

RUN pip3 install -U pip && \
    cd /tmp/code && \
    pip install -r requirements.txt && \
    python3 setup.py install && \
    useradd --uid 1000 app

ADD start /start

ENTRYPOINT ["/start"]
