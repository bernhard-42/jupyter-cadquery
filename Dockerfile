FROM continuumio/miniconda3:4.7.10

RUN useradd -m cq

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    rm -rf /var/lib/apt/lists/*

COPY environment.yml  /tmp
RUN mkdir /src /src/js /src/jupyter_cadquery /src/icons
ADD --chown=cq:cq LICENSE setup* jupyter_cadquery.json /src/
ADD --chown=cq:cq jupyter_cadquery  /src/jupyter_cadquery
ADD --chown=cq:cq js /src/js
ADD --chown=cq:cq icons /src/icons
RUN mkdir /data && chown cq:cq /data
ADD --chown=cq:cq examples /data/examples

WORKDIR /src
RUN conda env create -f /tmp/environment.yml -n cq && \
    conda run -n cq conda install -y nodejs && \
    conda run -n cq jupyter labextension install @jupyter-widgets/jupyterlab-manager @jupyter-widgets/jupyterlab-sidecar && \
    conda run -n cq pip install . && \
    conda run -n cq jupyter-labextension install js && \
    conda run -n cq jupyter lab build

VOLUME /data/workdir

WORKDIR /data

EXPOSE 8888

USER cq
CMD bash -l -c "source /opt/conda/bin/activate cq && jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'"
