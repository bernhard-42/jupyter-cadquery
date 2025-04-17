FROM condaforge/mambaforge:24.9.2-0

RUN adduser --disabled-password --gecos "Default user" --uid 1000 cq && \
    apt-get update -y && \
    apt-get install --no-install-recommends -y libgl1-mesa-glx libglu1-mesa && \
    apt-get clean

RUN mamba env create -n cq -y -f /tmp/environment.yml && \
    mamba clean --all && \
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
