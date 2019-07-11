FROM continuumio/miniconda3:4.6.14

ARG jl_version

RUN useradd -m cq

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    rm -rf /var/lib/apt/lists/*

USER cq
COPY environment-jl-$jl_version.yml  /tmp
RUN conda env create -f /tmp/environment-jl-$jl_version.yml -n cq && \
    conda run -n cq conda install -y nodejs && \
    conda run -n cq jupyter labextension install @jupyter-widgets/jupyterlab-manager

RUN if [ "$jl_version" = "1.0" ]; then conda run -n cq jupyter-labextension install @jupyter-widgets/jupyterlab-sidecar; fi
 
USER root
RUN mkdir /src /src/js /src/jupyter_cadquery /src/icons
ADD --chown=cq:cq LICENSE setup* jupyter_cadquery.json /src/
ADD --chown=cq:cq jupyter_cadquery  /src/jupyter_cadquery
ADD --chown=cq:cq js /src/js
ADD --chown=cq:cq icons /src/icons
WORKDIR /src

USER cq
RUN conda run -n cq pip install . && \
    conda run -n cq jupyter-labextension install js

USER root
RUN mkdir /data && chown cq:cq /data
ADD --chown=cq:cq examples /data/examples

USER cq
VOLUME /data/workdir

WORKDIR /data

EXPOSE 8888

CMD bash -l -c "source /opt/conda/bin/activate cq && jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'"

