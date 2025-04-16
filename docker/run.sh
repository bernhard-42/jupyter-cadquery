#!/bin/bash

VIEWER=0
export THEME=light

while getopts "dvgw:h:" o; do
    case "${o}" in
        g)
            export GLASS_MODE=1
            ;;
        w)
            export CAD_WIDTH=${OPTARG}
            ;;
        h)
            export CAD_HEIGHT=${OPTARG}
            ;;
        d)
            export THEME=dark
            ;;
    esac
done

echo "Starting in JupyterLab mode: http://localhost:8888/lab"
. /opt/conda/bin/activate cq && \
jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'
