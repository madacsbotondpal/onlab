#!/bin/bash

docker stack rm robot-stack
docker stack deploy --compose-file swarm.yaml robot-stack