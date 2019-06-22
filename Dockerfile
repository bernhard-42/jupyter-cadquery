FROM continuumio/miniconda3:4.6.14

RUN useradd -m cq
USER cq

RUN conda init bash
RUN conda create -n pycq python=3.6 numpy jupyterlab
RUN conda install -n pycq -c conda-forge -c cadquery pythonocc-core=0.18.2 pyparsing python=3.6 nodejs

RUN conda run -n pycq pip install ipywidgets pythreejs sidecar dataclasses
RUN conda run -n pycq jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-threejs @jupyter-widgets/jupyterlab-sidecar
RUN conda run -n pycq pip install --upgrade git+https://github.com/CadQuery/cadquery.git

ADD . /src
USER root
RUN chown -R cq /src
USER cq
WORKDIR /src

RUN conda run -n pycq jupyter-labextension install js
RUN conda run -n pycq pip install .

USER root
RUN apt-get update -y \
 && apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir /data
RUN chown cq:cq /data
USER cq

VOLUME /data
WORKDIR /data

EXPOSE 8888

CMD bash -l -c "conda activate pycq && jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token=''"

