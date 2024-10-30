#!/bin/sh 
docker run --rm -p 8080:8080 --env WHY3IDE=web --volume $PWD:/data --workdir /data why3 "$@"