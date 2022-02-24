FROM continuumio/miniconda3:4.10.3

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN conda create -n cq -c default -c conda-forge -c cadquery python=3.8 cadquery=master && \
    conda clean --all && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

RUN . "/opt/conda/etc/profile.d/conda.sh" && conda activate cq && \
    pip install jupyter-cadquery==3.0.0 cadquery-massembly~=0.9 voila~=0.3 matplotlib==3.3 && \
    find / -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

VOLUME /home/cq/
WORKDIR /home/cq
EXPOSE 8888

USER cq 

ADD --chown=cq:cq examples /home/cq
ADD --chown=cq:cq viewer.ipynb /home/cq
ADD --chown=cq:cq run.sh /tmp
RUN chmod +x /tmp/run.sh

ENTRYPOINT ["/tmp/run.sh"]
