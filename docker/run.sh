#!/bin/bash

VIEWER=0
export THEME=light

while getopts "dvgw:h:" o; do
    case "${o}" in
        v)
            VIEWER=1
            ;;
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

if [[ "VIEWER" -eq "1" ]]; then
    echo "Starting in viewer mode: http://localhost:8888/"
    . /opt/conda/bin/activate cq &&  \
    voila --theme $THEME \
    --Voila.ip=0.0.0.0 \
    --Voila.port=8888 \
    --show_tracebacks=True \
    --enable_nbextensions=True \
    --VoilaExecutor.kernel_name=jcv \
    --VoilaConfiguration.file_whitelist="favicon.ico" \
    --VoilaConfiguration.file_whitelist=".*\.js" \
    /home/cq/viewer.ipynb
else
    echo "Starting in JupyterLab mode: http://localhost:8888/lab"
    . /opt/conda/bin/activate cq && \
    jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'
fi