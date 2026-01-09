#!/bin/bash
app="texasholdem"
docker stop ${app}
docker rm ${app}
docker rmi ${app}
docker build -t ${app} .
docker run -d -p 5003:5003 \
  --name=${app} \
  -v $PWD:/app ${app}
read -n1 -s