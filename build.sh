#!/bin/bash

docker build -f base.dockerfile -t robot_base .

docker build -f logic.dockerfile -t logic .
docker build -f monitor.dockerfile -t monitor .
docker build -f control.dockerfile -t control .

docker tag logic localhost:5000/logic
docker tag monitor localhost:5000/monitor
docker tag control localhost:5000/control

docker push localhost:5000/logic
docker push localhost:5000/monitor
docker push localhost:5000/control
