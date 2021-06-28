FROM continuumio/miniconda3:4.9.2

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN conda create -n cq -c default -c conda-forge -c cadquery python=3.8 cadquery=2.1 && \
    conda clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN . "/opt/conda/etc/profile.d/conda.sh" && conda activate cq && \
    pip install jupyter-cadquery==2.2.0 cadquery-massembly~=0.9 orbitcontrol-patch~=0.1.0 && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

VOLUME /home/cq/
WORKDIR /home/cq
EXPOSE 8888

ADD --chown=cq:cq examples /home/cq

USER cq

CMD bash -l -c ". /opt/conda/bin/activate cq && jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.allow_origin='*'"
